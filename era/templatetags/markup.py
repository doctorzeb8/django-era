from itertools import chain
from django.core.urlresolvers import reverse
from django.utils.text import capfirst
from urllib.parse import urlencode

from ..utils.functools import just, call, factual, reduce_dict, omit, pick, truthful
from ..utils.translation import _
from .library import register, Import, Component, ComplexComponent, Tag


@register.era
class Icon(Tag):
    el = 'i'
    inline = True

    def get_defaults(self):
        return {'fixed': True, 'nodelist': ''}

    def resolve_attrs(self):
        return {
            'class': ' '.join(chain(
                ['fa', 'fa-' + self.props.name],
                map(
                    lambda z: 'fa-' + z[0].format(self.props.pop(z[1])),
                    filter(
                        lambda z: z[1] in self.props,
                        zip(
                            ('{0}x', 'li', 'lg', 'fw', 'spin', 'rotate-{0}'),
                            ('size', 'list', 'large', 'fixed', 'spin', 'rotate'))))))}


class MarkedList(Tag):
    el = 'ul'

    def get_items(self):
        return self.props.items

    def get_nodelist(self):
        return ''.join(map(
            lambda item: self.inject(Tag, {'el': 'li'}, item),
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
class ProgressBar(Tag):
    def get_defaults(self):
        return {'level': 'success'}

    def resolve_props(self):
        return {
            'class': 'progress',
            'value': str(int(self.props.value))}

    def DOM(self):
        return self.inject(
            Tag,
            {'attrs': {
                'class': 'progress-bar-' + self.props.level,
                'style': 'width: {0}%;'.format(self.props.value)}},
            self.props.value + '%')


@register.era
class Row(Tag):
    pass


@register.era
class Container(Tag):
    named = False

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
    named = False

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
    named = False

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
        return {'class': 'label-' + self.props.level}


@register.era
class Alert(Tag):
    def get_defaults(self):
        return {'level': 'primary', 'dismiss': True}

    def resolve_attrs(self):
        return {'class': 'alert-' + self.props.level}

    def get_nodelist(self):
        return self.show(Tag, {'el': 'span'}, super().get_nodelist())

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
        if 'size' in self.props:
            return {'class': 'well-' + self.props.size}
        return {}


@register.era
class Caption(Tag):
    el = 'span'

    def resolve_props(self):
        if isinstance(self.props.get('icon'), str):
            return {'icon': {'name': self.props.icon}}
        return {}

    def get_nodelist(self):
        if not 'icon' in self.props:
            return self.props.title
        return ''.join([
            self.inject(Icon, self.props.icon),
            self.inject(Tag, {'el': 'span'}, self.props.get(
                'title', self.props.nodelist))])


@register.era
class Panel(Tag):
    parts = ['title', 'body']

    def get_defaults(self):
        return {'level': 'default'}

    def resolve_attrs(self):
        return {'class': 'panel-' + self.props.level}

    def resolve_props(self):
        return {
            'class': 'panel',
            'has_heading': bool(self.props.get('title', self.props.get('caption')))}

    def render_heading(self, **kw):
        return self.inject(
            Tag, dict({'class': 'panel-heading'}, **kw), self.inject(
                Tag,
                {'el': 'h4', 'class': 'panel-title'},
                self.props.get('title') or self.inject(Caption, self.props.caption)))

    def render_body(self, **kw):
        return self.inject(
            Tag, dict({'class': 'panel-body'}, **kw), self.props.body)

    def get_nodelist(self):
        return ''.join(factual([
            self.props.has_heading and self.render_heading(),
            self.render_body()]))


class CollapsiblePanel(Panel):
    named = False

    def get_defaults(self):
        return dict(super().get_defaults(), collapse=None)

    def resolve_props(self):
        return dict(
            super().resolve_props(),
            href=''.join([self.props.prefix, str(self.props.pk)]))

    def render_heading(self, **kw):
        return super().render_heading(**{'attrs': {
            'class': 'collapsed' if not self.props.collapse else '',
            'href': '#' + self.props.href,
            'data-toggle': 'collapse',
            'data-parent': '#' + str(self.props.parent)}})

    def render_body(self, **kw):
        return self.show(
            Tag,
            {'attrs': {
                'id': self.props.href,
                'class': ' '.join(factual(
                    ['panel-collapse', 'collapse', self.props.collapse]))}},
            super().render_body())


class Accordion(Tag):
    panel = CollapsiblePanel

    def open_gen(self):
        yield True
        while True: yield False

    def get_defaults(self):
        return {
            'id': 'accordion',
            'class': 'panel-group',
            'open': self.open_gen()}

    def check_is_open(self, obj):
        return next(self.props.open)

    def get_nodelist(self):
        return ''.join(map(
            lambda obj: self.show(
                self.panel, dict({
                    'collapse': self.check_is_open(obj) and 'in',
                    'parent': self.props.id,
                    'prefix': self.props.prefix},
                    **pick(obj, 'pk', 'caption', 'body'))),
            self.get_objects()))


@register.era
class Navbar(Tag):
    el = 'nav'
    parts = ['head', 'brand', 'collapse', 'text']

    def get_defaults(self):
        return {
            'key': 'default',
            'container': False,
            'fixed': False,
            'margin': 20}

    def resolve_attrs(self):
        result = {'class': 'navbar-default'}
        if self.props.fixed:
            result['class'] = ' '.join([
                result['class'], 'navbar-fixed-{0}'.format(self.props.fixed)])
            if 'height' in self.props:
                result['style'] = 'min-height: {0}px;'.format(self.props.height)
        return result

    def get_nodelist(self):
        nodelist = ''.join(factual([
            self.inject(
                Tag,
                {'class': 'navbar-header'},
                ''.join([
                    self.props.head or self.inject(
                        Tag,
                        {'el': 'button', 'attrs': {
                            'class': 'navbar-toggle collapsed',
                            'data-toggle': 'collapse',
                            'data-target': '#' + self.props.key}},
                        self.inject(Icon, {'name': 'align-justify'})),
                    '' if not self.props.brand else self.inject(
                        Link,
                        {'url': '/', 'reverse': False, 'class': 'navbar-brand'},
                        self.props.brand)])),
            self.props.text and self.inject(
                Tag,
                {'el': 'p', 'class': 'navbar-text'},
                self.props.text),
            self.props.collapse and self.inject(
                Tag,
                {'attrs': {'id': self.props.key, 'class': 'navbar-collapse collapse'}},
                self.props.collapse)]))
        return nodelist if not self.props.container else self.inject(
            Container, {'fluid': self.props.container == 'fluid'}, nodelist)

    def tweak(self):
        if self.props.fixed:
            self.dom.before(self.inject(
                Tag, {'el': 'style'}, 'body {{padding-{0}: {1}px;}}'.format(
                    self.props.fixed, sum(map(int, [
                        self.props.get('height', 50),
                        self.props.margin])))))


class Table(Tag):
    el = 'table'

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

    def resolve_attrs(self):
        return {
            'class': self.get_class_set(
                'striped',
                'bordered',
                'hover',
                'condensed',
                'responsive',
                prefix='table')}

    def get_nodelist(self):
        body = list(self.get_tbody_items())
        if not len(list(body)):
            return _('(None)')
        return ''.join([
            self.inject(
                Tag,
                {'el': 'thead'},
                self.render_items([{'items': self.get_thead_items()}], cell='th')),
            self.inject(
                Tag,
                {'el': 'tbody'},
                self.render_items(body))])
