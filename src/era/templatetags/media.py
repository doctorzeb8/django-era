from itertools import chain, groupby
from django import forms
from django.templatetags.static import static

from ..utils.functools import just
from .library import register, Component, ComplexComponent, Tag


@register.era
class FormsMedia(Component):
    def DOM(self):
        types = (forms.Form, forms.ModelForm)
        media = [obj.media for obj in self.context.dicts[1].values() if isinstance(obj, types)]
        return '\n'.join([x for x, _y in groupby('\n'.join([str(m) for m in media]).split('\n'))])


class Include(Tag):
    el = 'link'
    nobody = True

    def get_defaults(self):
        return {'static': True}

    def get_url(self):
        return (self.props.static and static or just)(self.props.url)

    def resolve_attrs(self):
        return {'rel': self.rel, 'href': self.get_url()}


class Source(Include):
    def resolve_attrs(self):
        return {'src': self.get_url()}


@register.era
class Favicon(Include):
    rel = 'shortcut icon'


@register.era
class Stylesheet(Include):
    rel = 'stylesheet'


@register.era
class Script(Component):
    def DOM(self):
        return self.inject(
            Source,
            dict({'el': 'script', 'nobody': False}, **self.props),
            ' ')
        

@register.era
class Image(Source):
    el = 'img'
