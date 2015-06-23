from itertools import chain, groupby
from django.templatetags.static import static
from django.utils.text import capfirst

from ..utils.functools import just
from .library import register, Component, Tag
from .markup import Alert


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
class Script(Source):
    el = 'script'
    nobody = False
    inline = True

    def get_nodelist(self):
        return ''
        

@register.era
class Image(Source):
    el = 'img'


@register.era
class Messages(Component):
    def get_defaults(self):
        return {
            'capfirst': True,
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
                    (self.props.capfirst and capfirst or just)(message.message)),
                self.context['messages'])))
