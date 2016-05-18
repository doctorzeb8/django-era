import string
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.forms import PasswordInput
from django.utils.text import capfirst
from era import _, random_str
from era.utils.functools import pick

from .components import InviteNotification, RegistrationNotification
from .decorators import anonymous_required
from .models import Confirm


class AnonymousMixin:
    decorators = [anonymous_required]
    keywords = ['auth']
    form_props = {'class': 'condensed'}


class UserMixin:
    model = get_user_model()
    extra_fields = ['password']
    validate_unique = True

    def get_fields(self):
        return [self.model.USERNAME_FIELD] + self.extra_fields

    def prepare_form(self, form):
        form = super().prepare_form(form)
        if not self.validate_unique:
            form.validate_unique = lambda: None
        return form


class PasswordMixin:
    long_term = True
    password_messages = {
        'new': _('enter new password'),
        'blank': _('leave blank for random')}

    def gen_password(self, **kw):
        return random_str(5, ''.join([
            string.ascii_uppercase,
            string.digits]), **kw)

    def prepare_form(self, form):
        form = super().prepare_form(form)
        if self.instance:
            form.fields['password'].required = False
            form.fields['password'].widget = PasswordInput({
                'placeholder': self.password_messages['new']})
        else:
            form.fields['password'].required = False
            form.fields['password'].widget = PasswordInput({
                'placeholder': self.password_messages['blank']})
        return form

    def process_valid(self, form, **kw):
        if not self.instance and not 'password' in form.changed_data:
            form.cleaned_data['password'] = self.gen_password()
        return super().process_valid(form=form, **kw)

    def save_form(self, form):
        if not self.instance or form.cleaned_data['password']:
            form.instance.set_password(form.cleaned_data['password'])
        super().save_form(form)


class LoginMixin:
    def get_access(self, user):
        return user.access

    def process_login(self, user):
        if self.get_access(user):
            auth.login(self.request, user)
            return self.success_finish()
        else:
            self.send_message('error', _('sorry, access denied'))
            return self.navigate('login')


class WelcomeMixin:
    def get_success_message(self, **kw):
        return _('welcome {username}').format(username=self.request.user.get_short_name())


class InvitationMixin(UserMixin, PasswordMixin):
    notification = InviteNotification
    notification_message = _('invitation')

    def get_user(self, form):
        return form.instance.pk and form.instance or self.model.objects \
            .filter(**pick(form.cleaned_data, self.model.USERNAME_FIELD)) \
            .first()

    def send_notification(self, form, **kw):
        if not 'password' in form.changed_data:
            kw['password'] = form.cleaned_data['password']
        if kw:
            self.get_user(form).comm.send(
                self.request, self.notification_message, self.notification, **kw)

    def save_form(self, form):
        new_user = not bool(form.instance.pk)
        super().save_form(form)
        if new_user:
            self.send_notification(form)


class ConfirmationMixin(InvitationMixin):
    confirm = 'password'
    back_url = 'login'
    notification = RegistrationNotification
    notification_message = _('registration')
    success_message = _('confirmation data has been sent')

    def get_actions(self):
        return super().get_actions() if not self.back_url else [
            {'icon': 'send', 'title': _('request'), 'level': 'success'},
            {'icon': 'chevron-left', 'title': _('back'), 'level': 'link', 'link': self.back_url}]

    def create_confirmation(self, user, key, password):
        code, encoded = Confirm.gen_code(password)
        Confirm.objects.create(
            user=user,
            key=key,
            code=encoded,
            sign=make_password(password))
        return code

    def get_confirmation(self, user):
        return Confirm.objects.filter(user=user, key=self.confirm)

    def send_notification(self, form, **kw):
        kw['code'] = self.create_confirmation(
            self.get_user(form), self.confirm, form.cleaned_data['password'])
        super().send_notification(form, **kw)


class SignMixin(ConfirmationMixin):
    def get_success_redirect(self, **kw):
        result = super().get_success_redirect(**kw)
        if not self.instance and not 'password' in kw['form'].changed_data:
            return result + '?sign=blank'
        return result
