from itertools import chain
from django.core.urlresolvers import reverse
from django.utils.text import capfirst
from urllib.parse import urlencode

from ..utils.functools import just, call, factual, reduce_dict, omit, pick, truthful
from .library import register, Import, Component, ComplexComponent, Tag


@register.era
class Icon(Component):
    def DOM(self):
        return self.inject(
            Tag,
            {'el': 'i', 'class': ' '.join(chain(
                ['fa', 'fa-' + self.props.name],
                map(
                    lambda z: 'fa-' + z[0].format(self.props.pop(z[1])),
                    filter(
                        lambda z: z[1] in self.props,
                        zip(
                            ('{0}x', 'li', 'lg', 'fw', 'spin', 'rotate-{0}'),
                            ('size', 'list', 'large', 'fixed', 'spin', 'rotate'))))))})


class MarkedList(Tag):
    el = 'ul'

    def get_items(self):
        return self.props.items

    def get_nodelist(self):
        return ''.join(map(
            lambda item: '<li>{0}</li>'.format(item),
            self.get_items()))


class IconicList(Component):
    def get_defaults(self):
        return {'icon': 'asterisk', 'heading': 'h4'}

    def DOM(self):
        return ''.join([
            '' if not self.props.get('title') else self.inject(
                Tag,
                {'el': self.props.heading},
                capfirst(self.props.title)),
            self.inject(
                Tag,
                {'el': 'ul', 'class': 'fa-ul'},
                ''.join(map(
                    lambda content: self.inject(
                        Tag,
                        {'el': 'li'},
                        ''.join([content, self.inject(
                            Icon, {'name': self.props.icon, 'list': True})])),
                    map(str, self.get_items()))))])


@register.era
class Break(Component):
    def get_defaults(self):
        return {'x': 1, 'ruler': False}

    def resolve_props(self):
        return {
            'x': int(self.props.x),
            'tag': '<{0}r />'.format(self.props.ruler and 'h' or 'b')}

    def DOM(self):
        if 'join' in self.props:
            return self.props.tag.join(self.props.join)
        return self.props.x * self.props.tag


@register.era
class ProgressBar(Component):
    def get_defaults(self):
        return {'level': 'success'}

    def resolve_props(self):
        return {'value': str(int(self.props.value))}

    def DOM(self):
        return self.inject(
            Tag, {'class': 'progress'}, self.inject(
                Tag,
                {'attrs': {
                    'class': 'progress-bar progress-bar-' + self.props.level,
                    'style': 'width: {0}%;'.format(self.props.value)}},
                self.props.value + '%'))


@register.era
class Row(Tag):
    def resolve_attrs(self):
        return {'class': 'row'}


@register.era
class Container(Tag):
    def get_defaults(self):
        return {'fluid': False}

    def resolve_attrs(self):
        return {'class': 'container' + (self.props.fluid and '-fluid' or '')}


@register.era
class Column(Tag):
    def get_defaults(self):
        return {'constrict': False}

    def resolve_attrs(self):
        return {'class': ' '.join(reduce_dict(
            lambda k, v: 'col-{0}-{1}'.format(k, v),
            dict({'md': 12} if not self.props.constrict else {
                'md': 12 - self.props.constrict * 2,
                'md-offset': self.props.constrict
            }, **omit(self.props, 'nodelist', 'class', 'constrict'))))}


@register.era
class Link(Tag):
    el = 'a'

    def get_defaults(self):
        return {
            'nodelist': '',
            'newtab': False,
            'reverse': True,
            'host': False,
            'url': 'index',
            'args': [],
            'kwargs': {},
            'rel': None,
            'qs': None}

    def resolve_props(self):
        if self.props.rel:
            return {
                'reverse': False,
                'url': '/'.join([
                    self.request.path.rstrip('/'),
                    self.props.rel])}
        return {}

    def get_url(self):
        return ''.join(factual([
            self.props.host and self.get_host(),
            (self.props.reverse and reverse or just)(
                self.props.url,
                **pick(self.props, 'args', 'kwargs')),
            self.props.qs and '?' + urlencode(self.props.qs)]))

    def get_nodelist(self):
        return self.props['nodelist'] or self.get_url()

    def resolve_attrs(self):
        return {
            'target': self.props.newtab and '_blank' or '_self',
            'href': self.get_url()}


@register.era
class Button(Tag):
    el = 'button'

    def get_defaults(self):
        return {'level': 'primary', 'type': 'button', 'name': 'button'}

    def resolve_attrs(self):
        return dict(
            {'class': 'btn btn-' + self.props.level},
            **pick(self.props, 'type', 'onclick'))


@register.era
class Label(Tag):
    el = 'span'

    def get_defaults(self):
        return {'level': 'default'}

    def resolve_attrs(self):
        return {'class': 'label label-' + self.props.level}


@register.era
class Alert(Tag):
    def get_defaults(self):
        return {'level': 'primary', 'dismiss': True}

    def resolve_attrs(self):
        return {'class': 'alert alert-' + self.props.level}

    def tweak(self):
        super().tweak()
        if self.props.dismiss:
            self.dom.prepend(
                self.inject(
                    Tag,
                    {'el': 'button', 'class': 'close', 'attrs': 
                        {'type': 'button', 'data-dismiss': 'alert'}},
                    self.inject(Icon, {'name': 'remove'})))


@register.era
class Well(Tag):
    def resolve_attrs(self):
        return {
            'class': ' '.join(factual([
                'well', 
                '' if not 'size' in self.props else 'well-' + self.props.size]))}


@register.era
class Caption(Component):
    def DOM(self):
        return self.inject(
            Tag, {'el': 'span', 'class': 'caption'},
                self.props.title if not 'icon' in self.props else ''.join([
                    self.inject(Icon, {'name': self.props.icon}),
                    self.inject(Tag, {'el': 'span'}, self.props.title)]))


@register.era
class Panel(ComplexComponent):
    parts = ['title', 'body']

    def get_defaults(self):
        return {'level': 'default', 'title': False}

    def DOM(self):
        return self.inject(
            Tag,
            {'class': 'panel panel-' + self.props.level},
            ''.join([
                '' if not self.props.title else self.inject(
                    Tag, {'class': 'panel-heading'}, self.inject(
                        Tag, {'name': 'h3'}, self.props.title)),
                self.inject(
                    Tag, {'class': 'panel-body'}, self.props.body)]))


@register.era
class Navbar(ComplexComponent):
    parts = ['head', 'brand', 'collapse']

    def get_defaults(self):
        return {'id': 'default', 'container': False}

    def DOM(self):
        nodelist = ''.join([
            self.inject(
                Tag,
                {'class': 'navbar-header'},
                ''.join([
                    self.inject(
                        Tag,
                        {'el': 'button', 'attrs': {
                            'class': 'navbar-toggle collapsed',
                            'data-toggle': 'collapse',
                            'data-target': '#' + self.props.id}},
                        self.inject(Icon, {'name': 'align-justify'})),
                    self.props.head,
                    '' if not self.props.brand else self.inject(
                        Link,
                        {'url': '/', 'reverse': False, 'class': 'navbar-brand'},
                        self.props.brand)])),
            self.inject(
                Tag,
                {'attrs': {'id': self.props.id, 'class': 'navbar-collapse collapse'}},
                self.props.collapse)])

        return self.inject(
            Tag,
            {'el': 'nav', 'class': 'navbar navbar-default'},
            nodelist if not self.props.container else self.inject(
                Container, {'fluid': self.props.container == 'fluid'}, nodelist))


class Table(Component):
    def slice(self, seq):
        return list(seq)[slice(*call(
            getattr(self, 'get_slice', lambda: (None, None))))]

    def get_thead_items(self):
        return self.props.get('thead', [])

    def get_tbody_items(self):
        return self.props.get('tbody', [])

    def get_defaults(self):
        return {
            'striped': False,
            'bordered': False,
            'hover': True,
            'condensed': True,
            'responsive': True}

    def render_content(self, content, cell):
        if isinstance(content, bool):
            return self.inject(
                Icon,
                {'name': (content and 'check' or 'minus') + '-circle'})
        return content

    def render_items(self, items, cell='td'):
        return ''.join(map(
            lambda row: self.inject(
                Tag,
                truthful({'el': 'tr', 'class': row.get('level')}),
                ''.join(map(
                    lambda c: self.inject(
                        Tag,
                        {'el': cell},
                        self.render_content(c, cell)),
                    self.slice(row['items'])))),
            items))

    def DOM(self):
        return self.inject(
            Tag,
            {'el': 'table', 'class': self.get_class_set(
                'striped',
                'bordered',
                'hover',
                'condensed',
                'responsive',
                prefix='table',
                include='table')},
            ''.join([
                    self.inject(
                        Tag,
                        {'el': 'thead'},
                        self.render_items(
                            [{'items': self.get_thead_items()}],
                            cell='th')),
                    self.inject(
                        Tag,
                        {'el': 'tbody'},
                        self.render_items(self.get_tbody_items()))]))
