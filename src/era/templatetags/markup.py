from itertools import chain
from django.core.urlresolvers import reverse
from django.utils.text import capfirst

from ..utils.functools import just, emptyless, reduce_dict, omit, pick
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
                            ('li', 'lg', 'fw', 'spin', 'rotate-{0}'),
                            ('list', 'large', 'fixed', 'spin', 'rotate'))))))})


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
            'c': self.props.ruler and 'h' or 'b'}

    def DOM(self):
        return self.props.x * '<{0}r />'.format(self.props.c)


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
        return {'url': 'index', 'args': [], 'kwargs': {}, 'reverse': True, 'newtab': False}

    def resolve_attrs(self):
        return {
            'target': self.props.newtab and '_blank' or '_self',
            'href': (self.props.reverse and reverse or just)(
                self.props.url, **pick(self.props, 'args', 'kwargs'))}


@register.era
class Button(Tag):
    el = 'button'

    def get_defaults(self):
        return {'level': 'primary', 'type': 'button', 'name': 'button'}

    def resolve_attrs(self):
        return {'type': self.props.type, 'class': 'btn btn-' + self.props.level}


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
            'class': ' '.join(emptyless([
                'well', 
                '' if not 'size' in self.props else 'well-' + self.props.size]))}


@register.era
class Caption(Component):
    def DOM(self):
        if not 'icon' in self.props:
            return self.props.title
        return ''.join([
            self.inject(Icon, {'name': self.props.icon}),
            self.inject(Tag, {'el': 'span'}, self.props.title)])


@register.era
class Panel(ComplexComponent):
    parts = ['title', 'body']

    def get_defaults(self):
        return {'level': 'primary'}

    def DOM(self):
        return self.inject(
            Tag,
            {'class': 'panel panel-' + self.props.level},
            ''.join([
                self.inject(
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
                    '' if not 'brand' in self.props else self.inject(
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


@register.era
class Messages(Component):
    def get_defaults(self):
        return {
            'dismiss': True,
            'levels': {
                10: 'primary',
                20: 'info',
                25: 'success',
                30: 'warning',
                40: 'danger'}}

    def DOM(self):
        return self.inject(
            Tag, {'class': 'messages'}, ''.join(map(
                lambda message: self.inject(
                    Alert, {
                        'level': self.props.levels.get(message.level),
                        'dismiss': self.props.dismiss},
                    message.message),
                self.context['messages'])))
