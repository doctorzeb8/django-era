from functools import reduce
from itertools import chain
from django.conf import settings
from django.apps import apps
from django.utils.text import capfirst

from ..utils.functools import factual, first, pick, omit
from ..utils.translation import get_string, get_model_names
from ..utils.urls import exists_import
from .library import register, Component, ComplexComponent, Tag
from .markup import Link, Caption


class MenuItem(Tag):
    el = 'li'

    def get_defaults(self):
        return {
            'divider': False,
            'include': True,
            'disabled': False,
            'link': {'url': None}}

    def get_nodelist(self):
        if self.props.divider or not self.props.include:
            return ''
        return self.inject(Link, self.props.link, self.props.caption)

    def resolve_props(self):
        return {'caption': self.inject(Caption, self.props.caption)}

    def tweak(self):
        if not self.props.include:
            self.dom.empty()
        elif self.props.divider:
            self.dom.add_class('nav-divider')
        else:
            self.dom.add_class(self.get_class_set('disabled', 'active'))
        super().tweak()


class Dropdown(Tag):
    el = 'li'

    def get_defaults(self):
        return {'active': False}

    def resolve_props(self):
        result = {}
        if self.props.active:
            result['class'] = 'active'
        if self.props.nodelist:
            if not 'caret' in self.props:
                result['caret'] = self.inject(
                    Tag, {'el': 'span', 'class': 'caret'})
        else:
            result['caret'] = ''
        return result

    def get_nodelist(self):
        return ''.join([
            self.inject(
                Link,
                self.props.link,
                ''.join([
                    self.inject(Caption, self.props.caption),
                    self.props.caret]),
                attrs={
                    'class': 'dropdown-toggle',
                    'data-toggle': 'dropdown'}),
            '' if not self.props.nodelist else self.inject(
                Tag,
                {'el': 'ul', 'class': 'dropdown-menu'},
                self.props.nodelist)])


class Menu(Tag):
    el = 'ul'
    inline = True

    def get_items(self):
        return self.props.get('items', [])

    def resolve_item(self, item):
        link = item.get('link', {})
        if 'divider' in item:
            return {}
        elif 'model' in item:
            model = apps.get_model(*item['model'].split('.'))
            if not 'title' in item['caption']:
                item['caption']['title'] = get_model_names(model)[-1]
            (prefix, url) = map(get_string, get_model_names(model))
            if not 'url' in link:
                link['url'] = url
            item['active'] = self.check_active(
                url, *map(
                    lambda suffix: '-'.join([prefix, suffix]),
                    ['add', 'edit']))
        elif not 'active' in item:
            if link.get('url') and link.get('reverse', True):
                item['active'] = self.check_active(link.get('url'))
            else:
                item['active'] = False
        if 'include' in item and item['include'] is None:
            item['include'] = item.get('active')
        if item.get('disabled'):
            link.update({'url': '#', 'reverse': False})
        return dict(item, link=link)

    def resolve_items(self):
        return map(self.resolve_item, self.get_items())

    def filter_items(self, fn=lambda i: True, items=None):
        if items is None:
            items = self.resolve_items()
        return list(filter(lambda i: i.get('include', True) and fn(i), items))

    def render_item(self, item):
        if 'dropdown' in item:
            return self.render_dropdown(item) or ''
        return self.inject(MenuItem, item)

    def render_items(self, items=None):
        if items is None:
            items = self.resolve_items()
        return ''.join(map(self.render_item, items))

    def render_dropdown(self, item):
        items = list(item['dropdown'].resolve_items())
        include_items = self.filter_items(items=items)
        active_items = self.filter_items(lambda i: i.get('active'), items)

        if len(include_items):
            toggle = item['caption'].get('toggle', True)
            props = dict({
                'link': {},
                'nodelist': '',
                'active': item.get('active') or bool(active_items)},
                **pick(item, 'caption', 'attrs', 'link', 'caret'))

            display = first(props['active'] and active_items or include_items)
            if item['caption'].get('collapse', True) and len(include_items) == 1:
                if not props['active']:
                    props['link'].update(pick(display, 'url'))
                if toggle:
                    props.update(pick(display, 'caption'))
                return self.inject(MenuItem, props)
            if toggle and props['active']:
                props.update(pick(display, 'caption'))
                props['nodelist'] = self.render_items(self.filter_items(
                    lambda i: not i.get('active'),
                    items))
            else:
                props['nodelist'] = self.render_items(items)
            return self.inject(Dropdown, props)

    def get_defaults(self):
        return {'pills': False, 'tabs': False, 'stacked': False}

    def resolve_attrs(self):
        return {'class': self.get_class_set(
            'pills', 'tabs', 'stacked', prefix='nav', include='nav')}

    def get_nodelist(self):
        return self.render_items()


@register.era
class MainMenu(Menu):
    def get_items(self):
        return list(chain(*map(
            lambda cls: self.insert(cls).get_items(),
            factual(map(
                lambda module: getattr(
                    module,
                    ''.join([capfirst(module.__name__.split('.')[0]), 'Menu']),
                    None),
                factual(map(
                    lambda app: exists_import('.'.join([app, 'components'])),
                    getattr(settings, 'MAIN_MENU', []))))))))
