from classytags.arguments import KeywordArgument
from .library import register, Options, Prop, Tweaks, Tag, BlockTag


@register.ctag
class Heading(BlockTag):
    options = Options(Prop('size'))

    def DOM(self):
        return self.fmt('<h{size}>{nodelist}</h{size}>')


@register.ctag
class Icon(Tag):
    options = Options(Prop('name'), Tweaks())

    def DOM(self):
        return '<i class="fa fa-{0} {1}"></i>'.format(
            self.props['name'], not self.props['tweaks'] and '' or ' '.join(
                map(
                    lambda z: 'fa-' + z[0].format(self.props['tweaks'].get(z[1])),
                    filter(
                        lambda z: z[1] in self.props['tweaks'],
                        zip(
                            ('lg', 'fw', 'spin', 'rotate-{0}'),
                            ('large', 'fixed', 'spin', 'rotate'))))))


@register.ctag
class Caption(Tag):
    options = Options(Prop('icon'), Prop('title', resolve=True))

    def DOM(self):
        return ' '.join([
            self.inject(Icon, name=self.props['icon'], tweaks={}),
            '<span>{0}</span>'.format(self.props['title'])])
