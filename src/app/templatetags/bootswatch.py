from bootstrap_themes import list_themes
from era.templatetags.library import register
from era.templatetags.navs import Menu


@register.ctag
class BootswatchMenu(Menu):
    def get_items(self):
        return [
            [self.context['theme']] + \
            list(map(
                lambda i: {'title': i[0], 'url': '/' + i[0]},
                list_themes()))]
