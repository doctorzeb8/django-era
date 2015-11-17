from django.conf import settings
from django.utils.text import capfirst
from era import _
from era.components import register, TemplateComponent, Tag, Component, Break, Link, Image, Menu
from era.utils.functools import factual
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
                'active': self.check_active('login', 'recovery', 'confirm')}]
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
    parts = ['logo', 'empty', 'value', 'link']

    def get_parts(self):
        return self.parts

    def render_empty(self):
        return ' '

    def render_value(self, label=None, value=None):
        label = label or self.value
        return ': '.join([
            capfirst(str(label)),
            value or self.props.get(label.string)])

    def render_logo(self):
        if self.props.user.comm.display_html:
            return self.inject(Logo)

    def render_link(self, **kw):
        if self.props.user.comm.display_html:
            return self.inject(Link, dict({'host': True, 'newtab': True}, **kw))

    def DOM(self):
        delimiter = Break().as_string() if self.props.user.comm.display_html else '\n'
        return delimiter.join(factual(map(
            lambda attr: getattr(self, '_'.join(['render', attr]))(),
            self.get_parts())))


class ConfirmationMixin:
    value = _('code')

    def render_link(self):
        return super().render_link(
            url=self.url_name,
            qs={'code': self.props.code},
            nodelist=_('confirm'))


class JoinNotification(ConfirmationMixin, Notification):
    url_name = 'confirm'


class ResetNotification(ConfirmationMixin, Notification):
    url_name = 'unlock'


class InviteNotification(Notification):
    value = _('password')

    def render_link(self):
        return super().render_link(
            url='login',
            nodelist=_('login'))
