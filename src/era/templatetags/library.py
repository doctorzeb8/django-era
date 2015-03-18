import re
from classytags.arguments import Argument, KeywordArgument, MultiKeywordArgument
from classytags.core import Options as BaseOptions
from classytags.core import Tag as BaseTag 
from django.template import Library
from ..utils.functools import omit, first
from ..utils.translation import normalize


register = Library()
register.ctag = lambda cls: register.tag(normalize(cls.__name__), cls)


class Prop(Argument):
    def __init__(self, name, default=None, **kwargs):
        kwargs = dict({'resolve': False}, **kwargs)
        if default is not None:
            kwargs['required'] = False
        super().__init__(name, default, **kwargs)


class Tweaks(MultiKeywordArgument):
    def __init__(self, name='tweaks', **kwargs):
        kwargs = dict({'required': False}, **kwargs)
        return super().__init__(name, **kwargs)


class Options:
    def __init__(self, *args, **kwargs):
        if kwargs.get('blocks', []):
            self.blocks = [(kwargs['blocks'][0], 'nodelist')]
            self.blocks += list(map(
                lambda b: (b[1], kwargs['blocks'][b[0] - 1]),
                enumerate(kwargs['blocks'][1:], start=1)))
        else:
            self.blocks = []
        self.args = list(args) + [KeywordArgument('class', required=False)]
        self.kwargs = kwargs


class Tag(BaseTag):
    def inject(self, cls, **kw):
        return cls().render_tag(self.context, **kw)

    def __init__(self, parser=None, tokens=None):
        self.blocks = {}
        self.options = self.get_options()
        parser and super().__init__(parser, tokens)           

    def get_options(self, **kw):
        return BaseOptions(*self.options.args, **dict(self.options.kwargs, **kw))

    def render_tag(self, context, **kw):
        self.context = context
        self.request = context['request']

        try:
            kw['class'] = kw.get(
                first(
                    lambda p: isinstance(p, Tweaks),
                    self.options.options[None]
                ).name).pop('class', None)
        except IndexError:
            pass

        self.props = dict(
            omit(kw, 'class'),
            **{k: v.render(context) for k, v in self.blocks.items()})

        result = self.DOM()
        if kw.get('class', None):
            el = result.split('>')[0]
            return '>'.join([
                not 'class' in el and (el + 'class="{0}"'.format(kw['class'])) \
                or re.sub(r'class="(.*)"', r'class="\g<1> {0}"'.format(kw['class']), el)] \
                + result.split('>')[1:])
        return result

    def fmt(self, string):
        return string.format(**self.props)

    def DOM(self):
        raise NotImplementedError


class BlockTag(Tag):
    def get_options(self):
        end_block = (
            'end-' + normalize(self.__class__.__name__),
            not self.options.blocks and 'nodelist' or self.options.kwargs['blocks'][-1])
        return super().get_options(blocks=list(self.options.blocks) + [end_block])
