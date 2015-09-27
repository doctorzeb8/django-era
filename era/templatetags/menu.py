from itertools import chain
from django.conf import settings
from django.apps import apps
from django.core.urlresolvers import resolve
from django.utils.text import capfirst

from ..utils.functools import factual, pick, omit
from ..utils.translation import get_string, get_model_names
from ..utils.urls import exists_import
from .library import register, Component, ComplexComponent, Tag
from .markup import Link, Caption


class NavigationMixin:
    def check_active(self, *args):
        return resolve(self.request.path).url_name in args


class MenuItem(NavigationMixin, Tag):
    el = 'li'

    def get_defaults(self):
        return {
            'divider': False,
            'include': True,
            'disabled': False,
            'url': None,
            'reverse': True}

    def get_nodelist(self):
        if self.props.divider or not self.props.include:
            return ''
        return self.inject(
            Link, pick(self.props, 'url', 'reverse'), self.props.caption)

    def resolve_props(self):
        result = {}
        if self.props.divider:
            return {}
        elif 'model' in self.props:
            model = apps.get_model(*self.props.model.split('.'))
            self.props.caption['title'] = get_model_names(model)[-1]
            (prefix, url) = map(get_string, get_model_names(model))

            result['url'] = url
            result['active'] = self.check_active(
                url, *map(
                    lambda suffix: '-'.join([prefix, suffix]),
                    ['add', 'edit']))
        elif not 'active' in self.props:
            if self.props.url and self.props.reverse:
                result['active'] = self.check_active(self.props.url)
            else:
                result['active'] = False
        if self.props.include is None:
            result['include'] = result.get('active', self.props.active)
        if self.props.disabled:
            result.update({'url': '#', 'reverse': False})
        result['caption'] = self.inject(Caption, self.props.caption)
        return result

    def tweak(self):
        if not self.props.include:
            self.dom.empty()
        elif self.props.divider:
            self.dom.add_class('nav-divider')
        else:
            self.dom.add_class(self.get_class_set('disabled', 'active'))
        super().tweak()


class Menu(NavigationMixin, Component):
    def get_items(self):
        return self.props.items

    def get_defaults(self):
        return {'pills': False, 'tabs': False, 'stacked': False}

    def render_item(self, item):
        if isinstance(item, list):
            return self.inject(
                DropdownMenu, {'toggle': item[0], 'menu': item[1:]})
        return self.inject(MenuItem, item)

    def DOM(self):
        return self.inject(
            Tag,
            {'el': 'ul', 'class': self.get_class_set(
                'pills', 'tabs', 'stacked', prefix='nav', include='nav')},
            ''.join(map(self.render_item, self.get_items())))


class DropdownMenu(NavigationMixin, Tag):
    el = 'li'

    def resolve_attrs(self):
        return {'class': 'dropdown'}

    def get_nodelist(self):
        return ''.join([
            self.inject(
                Link, {
                    'url': self.props.toggle.get('url', '#'),
                    'reverse': False,
                    'attrs': {
                        'class': 'dropdown-toggle',
                        'data-toggle': 'dropdown'}},
                ''.join([
                    self.inject(Caption, self.props.toggle['caption']),
                    '' if not self.props.menu else self.inject(
                        Tag, {'el': 'span', 'class': 'caret'})])),
            '' if not self.props.menu else self.inject(
                Tag,
                {'el': 'ul', 'class': 'dropdown-menu'},
                ''.join(map(
                    lambda i: self.inject(MenuItem, i),
                    self.props.menu)))])


@register.era
class MainMenu(Menu):
    def get_app_menu_items(self, cls):
        result = cls()
        result.request = self.request
        result.context = self.context
        return result.get_items()

    def get_items(self):
        return list(chain(*map(
            self.get_app_menu_items,
            factual(map(
                lambda module: getattr(
                    module,
                    ''.join([capfirst(module.__package__), 'Menu']),
                    None),
                factual(map(
                    lambda app: exists_import('.'.join([app, 'components'])),
                    settings.MODULES)))))))
