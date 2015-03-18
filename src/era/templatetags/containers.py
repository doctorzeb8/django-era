from .library import register, Options, Prop, BlockTag


@register.ctag
class Container(BlockTag):
    options = Options(Prop('postfix', ''))

    def DOM(self):
        return '<div class="container{0}">{nodelist}</div>'.format(
            (self.props['postfix'] and '-' or '') + self.props['postfix'],
            **self.props)

@register.ctag
class Panel(BlockTag):
    options = Options(
        Prop('level', 'primary'),
        blocks=('title', 'body'))

    def DOM(self):
        return \
        '''
        <div class="panel panel-{level}"">
            <div class="panel-heading">
                <h3 class="panel-title">{title}</h3>
            </div>
            <div class="panel-body">
                {body}
            </div>
        </div>
        '''.format(**self.props)
