from importlib import import_module
from itertools import chain
import re

from classytags.arguments import MultiKeywordArgument
from classytags.core import Options
from classytags.core import Tag as ClassyTag
from django.template import Library, TemplateSyntaxError
from django.template.loader import render_to_string

from ..utils.functools import call, unpack_args, reduce_dict, map_values, \
    truthful, factual, pick, omit
from ..utils.translation import normalize
from ..utils.urls import get_site_url

register = Library()
register.era = lambda cls: register.tag(normalize(cls.__name__), cls)


@register.filter
def get(d, k):
    return d.get(k)


@register.era
class Import(ClassyTag):
    def __init__(self, parser, tokens):
        for module in tokens.contents.split(' ')[1:]:
            path = '.'.join(chain(
                [module.split('.')[0]],
                ['components'],
                [] if not '.' in module else module.split('.')[1:]))
            try:
                parser.tags.update(import_module(path).register.tags)
            except ImportError:
                raise TemplateSyntaxError('can not import {0}'.format(path))

    def render(self, *args, **kw):
        return ''


class HTMLTag:
    def __init__(self, el):
        self.el = str(el)

    def __str__(self):
        return self.el

    def modify_tag(self, diff):
        tag, *rest = self.el.split('>')
        self.el = '>'.join([diff(tag)] + rest)

    def modify_content(self, content, fmt):
        self.el = re.sub(r'>(.*)<', fmt.format(content), self.el)

    def append(self, content):
        self.modify_content(content, r'>\g<1>{0}<')

    def prepend(self, content):
        self.modify_content(content, r'>{0}\g<1><')

    def add_attr(self, name, val=None):
        self.modify_tag(lambda tag: ' '.join([
            tag.endswith('/') and tag.rstrip('/') or tag,
            val is None and name or '{0}="{1}"'.format(name, val),
            tag.endswith('/') and '/' or '']))

    def add_class(self, *cls):
        if not any(cls):
            return
        if not self.has_attr('class'):
            self.add_attr('class', ' '.join(cls))
        else:
            self.modify_tag(
                lambda tag: re.sub(
                    r'class="([^"]*)"',
                    r'class="\g<1> {0}"'.format(' '.join(cls)),
                    tag))

    def has_attr(self, name):
        return name in self.el.split('>')[0]

    def empty(self):
        self.el = ''


class Props(dict):
    def __getattr__(self, name):
        if name in self:
            return self.get(name)
        raise AttributeError('Missing prop: ' + name)


class Component(ClassyTag):
    def __init__(self, parser=None, tokens=None):
        self.blocks = {}
        self.set_options()
        parser and super().__init__(parser, tokens)

    @classmethod
    def as_string(cls, request=None, **kw):
        return cls().render_tag({'request': request}, **kw)

    def inject(self, cls, props=None, nodelist=None):
        return '' if not cls else cls().render_tag(self.context, **dict(
            props or {}, **(nodelist is not None and {'nodelist': nodelist} or {})))

    def join(self, *components):
        return ''.join(map(lambda x: self.inject(x), components))

    def build(self, args, prefix='render'):
        return map(lambda arg: call(getattr(self, '_'.join([prefix, arg]))), args)

    def get_host(self, *args, **kw):
        return get_site_url(self.request, *args, **kw)

    def get_defaults(self):
        return {}

    def get_class_set(self, *args, prefix='', include=''):
        return ' '.join(factual(
            chain([include], map(
                lambda k: '-'.join(factual([prefix, k])),
                truthful(pick(self.props, *args)).keys()))))

    def resolve_props(self):
        return {}

    def set_options(self, **kw):
        self.options = Options(MultiKeywordArgument('mka', required=False), **kw)

    def set_props(self, **kw):
        self.props = Props(
            self.get_defaults(),
            **dict(kw, **map_values(lambda val: val.render(self.context), self.blocks)))
        self.props.update(self.resolve_props())

    def render_tag(self, context, mka=None, **kw):
        self.context = context
        self.request = context['request']
        self.set_props(**dict(mka or {}, **kw))
        return self.render_dom()

    def render_dom(self):
        self.dom = HTMLTag(self.DOM())
        self.tweak()
        return str(self.dom)

    def DOM(self):
        raise NotImplementedError

    def tweak(self):
        if not 'attrs' in self.props and 'class' in self.props:
            self.dom.add_class(self.props['class'])


class ComplexComponent(Component):
    parts = []

    def get_defaults(self):
        return {'nodelist': ''}

    def set_options(self, **kw):
        return super().set_options(**(kw or {'blocks': chain(
            [] if not self.parts else [(self.parts[0], 'nodelist')],
            [] if not self.parts else list(map(unpack_args(
                lambda i, b: (b, self.parts[i - 1])),
                enumerate(self.parts[1:], start=1))),
            [(
                'end-' + normalize(self.__class__.__name__),
                not self.parts and 'nodelist' or self.parts[-1])])}))


class TemplateComponent(Component):
    template = 'index.html'

    def render_dom(self):
        return render_to_string(self.template, dict(self.context, **self.props))


@register.era
class Inject(Component):
    def DOM(self):
        return '' if not self.props.component else self.inject(
            lambda: self.props.component,
            omit(self.props, 'component'))


@register.era
class Tag(ComplexComponent):
    el = 'div'
    nobody = False
    inline = False

    def get_nodelist(self):
        return self.props.nodelist

    def resolve_attrs(self):
        return {}

    def resolve_tag(self):
        attrs = dict(
            self.props.get('attrs', {}),
            **self.resolve_attrs())
        if 'id' in self.props:
            attrs['id'] = self.props.id
        if 'class' in self.props:
            attrs['class'] = ' '.join(factual([
                attrs.get('class', ''),
                self.props['class']]))
        return {
            'el': self.props.get('el', getattr(self, 'el')),
            'attrs': ' '.join(reduce_dict(
                lambda k, v: v and '{0}="{1}"'.format(k, v) or k,
                attrs))}

    def set_options(self):
        return super().set_options(**(
            (self.inline or self.nobody) and {'blocks': []} or {}))
    
    def set_props(self, **kw):
        super().set_props(**kw)
        self.props.update(self.resolve_tag())
        not self.nobody and self.props.update({'nodelist': self.get_nodelist()})

    def DOM(self):
        return ''.join([
            '<{el} {attrs}',
            '/>' if self.nobody else '>{nodelist}</{el}>']) \
        .format(**self.props)


@register.era
class Content(Component):
    def DOM(self):
        return self.inject(self.context['components'].get('content', None))
