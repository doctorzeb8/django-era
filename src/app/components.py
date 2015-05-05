from bootstrap_themes import list_themes
from era.components import register, Menu


@register.era
class BootswatchMenu(Menu):
    def get_items(self):
        return [
            [self.context['theme']] + \
            list(map(
                lambda i: {'caption': {'title': i[0]}, 'url': '/' + i[0], 'reverse': False},
                list_themes()))]
