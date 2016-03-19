from importlib import import_module
from itertools import chain
import json
import re

from classytags.arguments import MultiKeywordArgument
from classytags.core import Options
from classytags.core import Tag as ClassyTag
from django.template import Library, TemplateSyntaxError
from django.template.loader import render_to_string

from ..utils.functools import call, unpack_args, filter_dict, reduce_dict, map_values, \
    truthful, factual, pick, omit, factual
from ..utils.translation import normalize
from ..utils.urls import resolve, get_site_url

register = Library()
register.era = lambda cls: register.tag(normalize(cls.__name__), cls)


@register.era
class Import(ClassyTag):
    def __init__(self, parser, tokens):
        for module in tokens.contents.split(' ')[1:]:
            path = '.'.join(
                [module, 'components'] if not module.startswith('.') else \
                [module.split('.')[1], 'components'] + module.split('.')[2:])
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

    def after(self, content):
        self.el += content

    def before(self, content):
        self.el = content + self.el

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


class RequestUrlMixin:
    def check_active(self, *args):
        return resolve(self.request.path).url_name in args

    def get_host(self, *args, **kw):
        return get_site_url(self.request, *args, **kw)


class Component(RequestUrlMixin, ClassyTag):
    def __init__(self, parser=None, tokens=None, context=None):
        self.set_context(context or {})
        self.blocks = {}
        self.set_options()
        parser and super().__init__(parser, tokens)

    @classmethod
    def as_string(cls, request=None, **kw):
        # TODO: move to view.show
        obj = cls(context={'request': request})
        obj.set_props(kw)
        return obj.render_dom()

    def inject(self, *args, **kw):
        # TODO: deprecate
        return self.show(*args, **kw)

    def insert(self, cls, props=None, nodelist=None, **kw):
        obj = cls(context=self.context)
        if nodelist is not None:
            kw['nodelist'] = nodelist
        obj.set_props(props, **kw)
        return obj

    def show(self, cls, props=None, nodelist=None, **kw):
        return self.insert(cls, props, nodelist, **kw).render_dom()

    def render_tag(self, context=None, mka=None, **kw):
        if not self.context and context:
            self.set_context(context)
        self.set_props(
            dict(mka, **kw),
            **map_values(
                lambda val: val.render(self.context),
                self.blocks))
        return self.render_dom()

    def build(self, args, prefix='render'):
        return map(lambda arg: call(getattr(self, '_'.join([prefix, arg]))), args)

    def get_defaults(self):
        return {}

    def get_class_set(self, *args, prefix='', include=''):
        return ' '.join(factual(
            chain([include], map(
                lambda k: '-'.join(factual([prefix, k])),
                truthful(pick(self.props, *args)).keys()))))

    def resolve_props(self):
        return {}

    def set_context(self, context):
        self.context = context
        self.request = self.context.get('request')

    def set_options(self, **kw):
        self.options = Options(MultiKeywordArgument('mka', required=False), **kw)

    def set_props(self, d, **kw):
        self.props = Props(
            self.get_defaults(),
            **dict(d or {}, **kw))
        self.props.update(self.resolve_props())

    def render_dom(self):
        self.tune()
        self.dom = HTMLTag(self.DOM())
        self.tweak()
        return str(self.dom)

    def DOM(self):
        raise NotImplementedError

    def tune(self):
        pass

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
        self.context.update(self.props)
        return render_to_string(self.template, self.context)


@register.era
class Tag(ComplexComponent):
    el = 'div'
    nobody = False
    inline = False
    named = True

    @property
    def root(self):
        return Tag

    def get_nodelist(self):
        return self.props.nodelist

    def resolve_attrs(self):
        return {}

    def resolve_node_name(self):
        return ' '.join(map(
            lambda cls: normalize(cls.__name__),
            filter(
                lambda cls: getattr(cls, 'named', False),
                self.__class__.__mro__[:self.__class__.__mro__.index(self.root)])))

    def resolve_tag(self):
        attrs = dict(
            self.props.get('attrs', {}),
            **self.resolve_attrs())
        attrs.update(filter_dict(
            lambda k, v: v, {
            'id': self.props.get('id'),
            'class': ' '.join(factual([
                self.named and self.resolve_node_name(),
                attrs.get('class', ''),
                self.props.get('class', '')]))}))
        return {
            'el': self.props.get('el', getattr(self, 'el')),
            'attrs': ' '.join(reduce_dict(
                lambda k, v: v and '{0}="{1}"'.format(k, v) or k,
                attrs))}

    def set_options(self, **kw):
        return super().set_options(**dict(kw, **(
            (self.inline or self.nobody) and {'blocks': []} or {})))

    def DOM(self):
        return ''.join([
            '<{el} {attrs}',
            '/>' if self.nobody else '>{nodelist}</{el}>']) \
        .format(**self.props)

    def tune(self):
        self.props.update(self.resolve_tag())
        not self.nobody and self.props.update({'nodelist': self.get_nodelist()})

    def tweak(self):
        pass


class ScriptedTag(Tag):
    @property
    def root(self):
        return ScriptedTag

    def get_script(self):
        if 'script' in self.props:
            return self.props.script
        return self.__class__.__name__

    def resolve_script(self):
        return {}

    def DOM(self):
        return ''.join(factual([
            super().DOM(),
            self.get_script() is not None and self.inject(
                Tag, {'el': 'script'}, '$(function() {{{0}}})'.format(
                    ''.join([
                        self.get_script(),
                        '({0})'.format(', '.join([
                            '\'.{0}\''.format(self.resolve_node_name().split(' ')[-1]),
                            json.dumps(self.resolve_script())]))])))]))


@register.era
class Display(Component):
    def resolve_props(self):
        return {'cls': self.context['components'].get(self.props.component, None)}

    def DOM(self):
        if self.props.cls:
            return self.show(self.props.cls, omit(self.props, 'component', 'cls'))
        return ''


@register.era
class Content(Tag):
    el = 'main'
    inline = True

    def get_nodelist(self):
        return self.show(Display, {'component': 'content'})
