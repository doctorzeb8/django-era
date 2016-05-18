from django.conf import settings
from django.utils.text import capfirst
from era import _
from era.components import register, TemplateComponent, Tag, Component, Break, Link, Image, Menu
from era.utils.functools import factual, pick
from era.utils.translation.verbose import verbose_attr


class UserModelMixin:
    @property
    def is_superuser(self):
        return self.request.user.is_authenticated() \
            and self.request.user.role == settings.USER_ROLES[0].string

    def get_user_menu_item(self):
        return {
            'model': 'users.User',
            'caption': {'icon': 'users'},
            'include': self.is_superuser}


class AuthMenu(Menu):
    def get_items(self):
        if self.request.user.is_anonymous():
            return [{
                'caption': {'icon': 'sign-in', 'title': _('login')},
                'link': {'url': 'login'},
                'active': self.check_active('login', 'join', 'reset', 'unlock', 'confirm')}]
        return [{
            'caption': {'icon': 'user', 'title': _('profile')},
            'link': {'url': 'profile'}
            }, {
            'caption': {'icon': 'sign-out', 'title': _('logout')},
            'link': {'url': 'logout'}}]


class BaseUsersMenu(UserModelMixin, AuthMenu):
    def get_items(self):
        return [self.get_user_menu_item()] + super().get_items()


@register.era
class Logo(Link):
    inline = True

    def resolve_props(self):
        return {
            'host': True,
            'url': 'index',
            'newtab': True}

    def get_nodelist(self):
        return self.inject(Image, {
            'host': True,
            'url': 'images/logo.png'})


class Notification(Component):
    parts = []

    def get_parts(self):
        return self.parts

    def render_empty(self):
        return ' '

    def render_value(self, label, value=None):
        return ': '.join([capfirst(str(label)), value or self.props.get(label.string)])

    def render_logo(self):
        return self.inject(Logo)

    def render_link(self, **kw):
        if self.props.user.comm.display_html:
            return self.inject(Link, dict({'host': True, 'newtab': True}, **kw))

    def DOM(self):
        delimiter = Break().as_string() if self.props.user.comm.display_html else '\n'
        return delimiter.join(factual(map(
            lambda attr: getattr(self, '_'.join(['render', attr]))(),
            self.get_parts())))


class AuthNotification(Notification):
    def get_parts(self):
        result = []
        if self.props.user.comm.display_html:
            result = ['logo', 'empty']
        if 'code' in self.props:
            result.append('code')
        if 'password' in self.props:
            result.append('password')
        return result + ['link']

    def render_code(self):
        return self.render_value(_('code'))

    def render_password(self):
        return self.render_value(_('password'))

    def render_link(self, **kw):
        qs = pick(self.props, 'code')
        if 'password' in self.props and 'code' in qs:
            qs['sign'] = self.props.password
        if not 'nodelist' in kw:
            kw['nodelist'] = _('confirm')
        return super().render_link(url=self.url_name, qs=qs, **kw)


class InviteNotification(AuthNotification):
    url_name = 'login'

    def render_link(self, **kw):
        return super().render_link(nodelist=_('login'), **kw)


class RegistrationNotification(AuthNotification):
    url_name = 'confirm'


class ResetNotification(AuthNotification):
    url_name = 'unlock'
