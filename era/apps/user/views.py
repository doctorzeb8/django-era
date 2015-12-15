import string

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import get_hasher, make_password

from era import _, random_str
from era.views import RedirectView, FormView, CollectionView, ObjectView
from era.utils.functools import factual, pick

from .components import JoinNotification, ResetNotification, InviteNotification
from .decorators import role_required
from .forms import LoginForm, ProfileForm, JoinForm, ResetForm, ConfirmForm, UserForm
from .models import Confirm


class PasswordMixin:
    def gen_password(self, **kw):
        return random_str(5, ''.join([
            string.ascii_uppercase,
            string.digits]), **kw)

    def set_password(self, form):
        if form.cleaned_data['password']:
            form.instance.set_password(form.cleaned_data['password'])


class UserMixin(PasswordMixin):
    def get_user(self, form):
        model = get_user_model()
        return model.objects.filter(**pick(form.cleaned_data, model.USERNAME_FIELD)).first()


class ConfirmationMixin:
    def gen_code(self, salt=None):
        hasher = get_hasher()
        generate = True
        while generate:
            code = random_str()
            encoded = hasher.encode(code, salt or hasher.salt())
            generate = bool(Confirm.objects.filter(code=encoded).count())
        return code, encoded

    def create_confirmation(self, user, key, password):
        code, encoded = self.gen_code(password)
        Confirm.objects.create(
            user=user,
            key=key,
            code=encoded,
            sign=make_password(password))
        return code


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

    def get_success_message(self, **kw):
        return _('welcome {username}').format(username=str(self.request.user))


class HistoryNavigationMixin:
    back_button_url = 'index'

    def get_back_action(self):
        return {
            'icon': 'chevron-left',
            'title': _('back'),
            'level': 'warning',
            'link': self.back_button_url}


class AuthFormMixin:
    keywords = ['auth']
    form_props = {'class': 'condensed'}


class AuthRequestView(
    UserMixin, ConfirmationMixin, HistoryNavigationMixin, AuthFormMixin, FormView):
    long_term = True
    back_button_url = 'login'


class LoginView(LoginMixin, AuthFormMixin, FormView):
    form_class = LoginForm

    @property
    def has_comm(self):
        return get_user_model().get_communicator(user=None) is not None

    def get_actions(self):
        result = [{
                'icon': 'sign-in',
                'title': _('login'),
                'level': 'success'}]
        if self.has_comm:
            result.extend([{
                'icon': 'user-plus',
                'title': _('join'),
                'level': 'default',
                'link': 'join'
            }, {
                'icon': 'unlock',
                'title': _('unlock'),
                'level': 'danger',
                'link': 'reset'
            }])
        return result

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


class LogoutView(RedirectView):
    decorators = [login_required]
    permanent = True

    def get_redirect_url(self):
        auth.logout(self.request)
        self.pattern_name = 'index'
        return super().get_redirect_url()


class ProfileView(UserMixin, LoginMixin, FormView):
    decorators = [login_required]
    form_class = ProfileForm
    form_props = {'class': 'condensed'}

    def get_instance(self):
        return self.request.user

    def prepare_form(self, form):
        form.fields['password'].required = False
        return form

    def process_valid(self, form, **kw):
        if form.cleaned_data['password']:
            self.set_password(form)
            return self.process_login(auth.authenticate(**dict(
                self.request.user.username_dict,
                password=form.cleaned_data['password'])))
        return super().process_valid(**dict(kw, form=form))

    def get_success_message(self, **kw):
        return _('your profile was updated successfully')


class JoinView(AuthRequestView):
    form_class = JoinForm
    success_redirect = 'confirm'
    success_message = _('confirmation code has been sent')

    def get_actions(self):
        return [{
            'icon': 'check',
            'title': _('submit'),
            'level': 'success'
        }, self.get_back_action()]

    def process_valid(self, form, **kw):
        user = self.get_user(form)
        if user:
            confirm = Confirm.objects.filter(user=user, key='registration').first()
            if confirm:
                user.delete()
                confirm.delete()
            else:
                self.send_message('error', _('sorry, user with such data exists'))
                return self.reload()
        return super().process_valid(form=form, **kw)

    def save_form(self, form):
        form.instance.role = settings.USER_ROLES[-1].string
        self.set_password(form)
        super().save_form(form)
        form.instance.comm.send(
            self.request,
            _('registration'),
            JoinNotification,
            code=self.create_confirmation(
                form.instance,
                'registration',
                form.cleaned_data['password']))


class ResetView(AuthRequestView):
    form_class = ResetForm
    success_redirect = 'unlock'
    success_message = _('confirmation code has been sent')
    actions = [{'icon': 'send', 'title': _('request'), 'level': 'success'}]

    def process_valid(self, form, **kw):
        user = self.get_user(form)
        if user:
            Confirm.objects.filter(user=user, key='password').delete()
            user.comm.send(
                self.request,
                _('access restoration'),
                ResetNotification,
                code=self.create_confirmation(
                    user,
                    'password',
                    form.cleaned_data['password']))
            return self.success_finish()
        else:
            self.send_message('error', _('sorry, invalid credentials'))
            return self.reload()


class ConfirmView(LoginMixin, AuthFormMixin, FormView):
    form_class = ConfirmForm
    repeat_url = 'join'
    update_password = False

    def get_initial(self):
        return pick(self.request.GET, 'code')

    def get_actions(self):
        return [
            {'icon': 'check', 'title': _('submit'), 'level': 'success'},
            {'icon': 'refresh', 'title': _('repeat'), 'level': 'default', 'link': self.repeat_url}]

    def process_valid(self, form, **kw):
        confirm = Confirm.objects \
            .filter(code=get_hasher().encode(
                form.cleaned_data['code'],
                form.cleaned_data['sign'])) \
            .first()
        if confirm:
            if self.update_password:
                confirm.user.password = confirm.sign
                confirm.user.save()
            user = confirm.user
            confirm.delete()
            return self.process_login(auth.authenticate(**dict(
                user.username_dict,
                password=form.cleaned_data['sign'])))
        else:
            self.send_message('error', _('sorry, invalid credentials'))
        return self.reload()


class UnlockView(ConfirmView):
    repeat_url = 'reset'
    update_password = True


class UserManagerMixin:
    decorators = [login_required, role_required(allow=['developer'])]
    model = get_user_model()


class BaseUsersView(UserManagerMixin, CollectionView):
    list_display = (get_user_model().USERNAME_FIELD, 'role', 'name', 'access')
    list_filter = ('role', 'access')
    list_counters = ('role', )
    list_search = ('name', )
    default_state = {'filters': {'access': True}}


class BaseUserView(PasswordMixin, UserManagerMixin, ObjectView):
    form_class = UserForm
    form_props = {'class': 'condensed'}

    def send_invite(self, form, password):
        return form.instance.comm.send(
            self.request,
            _('invitation'),
            InviteNotification,
            password=password)

    def save_form(self, form):
        if not form.instance.pk:
            password = form.cleaned_data['password'] or self.gen_password()
            form.instance.set_password(password)
            form.instance.comm and self.send_invite(form, password)
        else:
            self.set_password(form)
        super().save_form(form)


class UsersView(BaseUsersView): pass
class UserView(BaseUserView): pass
