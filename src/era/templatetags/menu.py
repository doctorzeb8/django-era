from django.core.urlresolvers import reverse, resolve
from ..utils.functools import pick, omit
from .library import register, Component, ComplexComponent, Tag
from .markup import Link, Caption


class MenuItem(Tag):
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
        if self.props.divider:
            return {}
        result = {'caption': self.inject(Caption, self.props.caption)}
        if not 'active' in self.props:
            if self.props.url and self.props.reverse:
                result['active'] = resolve(self.request.path).url_name == self.props.url
            else:
                result['active'] = False
        if self.props.include is None:
            result['include'] = result.get('active', self.props.active)
        if self.props.disabled:
            result.update({'url': '#', 'reverse': False})
        return result

    def tweak(self):
        if not self.props.include:
            self.dom.empty()
        elif self.props.divider:
            self.dom.add_class('nav-divider')
        else:
            self.dom.add_class(self.get_class_set('disabled', 'active'))
        super().tweak()


class Menu(Component):
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


class DropdownMenu(Component):
    def DOM(self):
        return self.inject(
            Tag, {'el': 'li', 'class': 'dropdown'}, ''.join([
                self.inject(
                    Link,
                    {
                        'url': '#',
                        'reverse': False,
                        'attrs': {
                            'class': 'dropdown-toggle',
                            'data-toggle': 'dropdown'}},
                    ''.join([
                        self.props.toggle,
                        self.inject(
                            Tag, {'el': 'span', 'class': 'caret'})])),
                self.inject(
                    Tag,
                    {'el': 'ul', 'class': 'dropdown-menu'},
                    ''.join(map(
                        lambda i: self.inject(MenuItem, i),
                        self.props.menu)))]))
