from classytags.core import Tag, Options

from .buttons import *
from .containers import *
from .library import register, Options, Prop, Tag
from .navs import *
from .typography import *


@register.ctag
class Break(Tag):
    options = Options(Prop('x', 1))

    def DOM(self):
        return '<br />' * int(self.props['x'])
