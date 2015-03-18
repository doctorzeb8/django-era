from .library import register, Options, Prop, Tag, BlockTag
from .typography import Caption


@register.ctag
class Button(BlockTag):
    options = Options(
        Prop('level', 'primary'),
        Prop('type', 'button'))

    def DOM(self):
        return '<button type={type} class="btn btn-{level}">{nodelist}</button>'.format(
            **self.props)
