import string

from django import forms
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import get_hasher
from django.utils.text import capfirst

from era import _
from era.views import BaseView, FormView, CollectionView, ObjectView
from era.utils.functools import pick

from .components import ResetNotification
from .decorators import login_required, role_required
from .mixins import AnonymousMixin, UserMixin, PasswordMixin, LoginMixin, WelcomeMixin, \
    InvitationMixin, SignMixin
from .models import Confirm


class LoginView(AnonymousMixin, UserMixin, LoginMixin, WelcomeMixin, FormView):
    validate_unique = False

    def get_actions(self):
        return [{
            'icon': 'sign-in',
            'title': _('login'),
            'level': 'success'
            }, {
            'icon': 'user-plus',
            'title': _('join'),
            'level': 'link',
            'link': 'registration'
            }, {
            'icon': 'unlock',
            'title': _('unlock'),
            'level': 'link',
            'link': 'reset'}]

    def prepare_form(self, form):
        form = super().prepare_form(form)
        form.fields['password'].widget = forms.PasswordInput()
        return form

    def process_valid(self, form, **kw):
        user = auth.authenticate(**form.cleaned_data)
        if user:
            if Confirm.objects.filter(user=user, key='registration').count():
                self.send_message('error', _('sorry, unconfirmed data'))
            else:
                return self.process_login(user)
        else:
            self.send_message('error', _('sorry, invalid credentials'))
        return self.reload()

    def get_success_redirect(self, **kw):
        return self.request.GET.get('next', super().get_success_redirect(**kw))


class RegistrationView(AnonymousMixin, SignMixin, FormView):
    extra_fields = ['name', 'password']
    validate_unique = False
    confirm = 'registration'
    success_redirect = 'confirm'
    success_message = _('confirmation data has been sent')

    def process_valid(self, form, **kw):
        user = self.get_user(form)
        if user:
            confirm = self.get_confirmation(user).first()
            if confirm:
                user.delete()
                confirm.delete()
            else:
                self.send_message('error', _('sorry, user with such data exists'))
                return self.reload()
        return super().process_valid(form=form, **kw)

    def save_form(self, form):
        form.instance.role = settings.USER_ROLES[-1].string
        super().save_form(form)


class ResetView(AnonymousMixin, SignMixin, FormView):
    validate_unique = False
    notification = ResetNotification
    notification_message = _('access restoration')
    success_redirect = 'unlock'

    def get(self, *args, **kw):
        self.send_message('info', _('please set new password and confirm it by code'))
        return super().get(*args, **kw)

    def prepare_form(self, form):
        form = super().prepare_form(form)
        form.fields['password'].label = capfirst(self.password_messages['new'])
        return form

    def process_valid(self, form, **kw):
        user = self.get_user(form)
        if user:
            self.get_confirmation(user).delete()
            return super().process_valid(form=form, **kw)
        else:
            self.send_message('error', _('sorry, invalid credentials'))
            return self.reload()

    def save_form(self, form):
        self.send_notification(form)


class ConfirmView(AnonymousMixin, LoginMixin, WelcomeMixin, FormView):
    model = Confirm
    fields = ('code', 'sign')
    repeat_url = 'registration'

    def check(self, code, sign):
        confirm = Confirm.objects.filter(code=get_hasher().encode(code, sign)).first()
        if confirm:
            confirm.user.password = confirm.sign
            confirm.user.save()
            user = confirm.user
            confirm.delete()
            return self.process_login(auth.authenticate(**dict(
                user.username_dict,
                password=sign)))
        else:
            self.send_message('error', _('sorry, invalid credentials'))
        return False

    def get(self, *args, **kw):
        data = pick(self.request.GET, 'code', 'sign')
        if 'code' in data and 'sign' in data:
            return self.check(**data) or self.navigate('confirm')
        return super().get(*args, **kw)

    def get_actions(self):
        result = [{'icon': 'check', 'title': _('submit'), 'level': 'success'}]
        if not 'code' in self.request.GET:
            result.append({
                'icon': 'refresh',
                'title': _('repeat'),
                'level': 'link',
                'link': self.repeat_url})
        return result

    def prepare_form(self, form):
        form = super().prepare_form(form)
        if 'code' in self.request.GET:
            form.fields['code'].widget = forms.HiddenInput(
                attrs={'value': self.request.GET['code']})
        else:
            form.fields['code'].label = capfirst(_('enter received code'))

        if 'sign' in self.request.GET:
            form.fields['sign'].label = capfirst(_('enter received password'))
        else:
            form.fields['sign'].label = capfirst(_('enter your password again'))
        form.fields['sign'].widget = forms.PasswordInput()
        return form

    def process_valid(self, form, **kw):
        return self.check(**pick(form.cleaned_data, 'code', 'sign')) or self.reload()


class UnlockView(ConfirmView):
    repeat_url = 'reset'


class UserView(InvitationMixin, ObjectView):
    decorators = [login_required, role_required(allow=['developer'])]
    extra_fields = ['role', 'name', 'password', 'access']
    form_props = {'class': 'condensed'}


class UsersView(CollectionView):
    decorators = [login_required, role_required(allow=['developer'])]
    model = get_user_model()
    list_display = (model.USERNAME_FIELD, 'role', 'name', 'access')
    list_filter = ('role', 'access')
    list_counters = ('role', )
    list_search = ('name', )
    default_state = {'filters': {'access': True}}


class ProfileView(UserMixin, PasswordMixin, LoginMixin, FormView):
    validate_unique = False
    decorators = [login_required]
    extra_fields = ['name', 'password']
    form_props = {'class': 'condensed'}

    def get_instance(self):
        return self.request.user

    def prepare_form(self, form):
        form = super().prepare_form(form)
        form.fields[self.model.USERNAME_FIELD].widget = forms.TextInput(
            attrs={'readonly': 'readonly'})
        return form

    def process_valid(self, form, **kw):
        if form.cleaned_data['password']:
            self.save_form(form)
            return self.process_login(auth.authenticate(**dict(
                self.request.user.username_dict,
                password=form.cleaned_data['password'])))
        return super().process_valid(**dict(kw, form=form))

    def get_success_message(self, **kw):
        return _('your profile was updated successfully')


class LogoutView(BaseView):
    decorators = [login_required]

    def get(self, *args, **kw):
        auth.logout(self.request)
        response = self.navigate('login')
        response.status_code = 307
        return response
