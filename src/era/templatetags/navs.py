from ..utils.functools import truthful, pick
from .containers import Container
from .library import register, Options, Prop, Tweaks, Tag, BlockTag
from .typography import Icon


@register.ctag
class Navbar(BlockTag):
    options = Options(Tweaks(), blocks=['head', 'brand', 'collapse'])

    def DOM(self):
        self.props['id'] = self.props['tweaks'].pop('id', 'default')
        self.props['icon'] = self.inject(Icon, name='align-justify', tweaks={})
        if self.props['brand']:
            self.props['brand'] = self.fmt('<a href="/" class="navbar-brand">{brand}</a>')       

        nav = self.fmt('''
            <div class="navbar-header">
                <button
                    class="navbar-toggle collapsed"
                    data-toggle="collapse"
                    data-target="{id}">
                    {icon}
                </button>
                {head}{brand}
            </div>
            <div id={id} class="navbar-collapse collapse">{collapse}</div>
            ''')

        container = self.props['tweaks'].get('container', False)
        if container:
            nav = self.inject(
                Container,
                nodelist=nav,
                postfix='' if container is True else container)
        return '<nav class="navbar navbar-default">{0}</nav>'.format(nav)


class Menu(Tag):
    options = Options(Tweaks())

    def get_items(self):
        raise NotImplementedError

    def render_items(self):
        return ''.join(map(self.render_item, self.get_items()))

    def render_item(self, i):
        if isinstance(i, list):
            return self.inject(DropdownMenu, toggle=i[0], menu=i[1:])
        elif i.get('divider', False):
            return self.inject(MenuDivider)

        props = dict({'disabled': False, 'active': False, 'include': True}, **i)
        if not props['disabled'] and not 'url' in props:
            try:
                if props['include']:
                    props['url'] = reverse(data.get('url_name', None))
                    props['active'] = \
                        resolve(self.request.path.url_name) == props.get('url_name', None)
            except NoReverseMatch:
                data['url'] = '#'

        if props['include'] is None:
            props['include'] = data['active']
        if not props['include']:
            return ''
        return '<li class="{0}"><a href="{url}">{title}</a></li>'.format(
            ''.join(truthful(pick(props, 'disabled', 'active')).keys()),
            **props)

    def DOM(self):
        return '<ul class="nav">{1}</ul>'.format(
            ' '.join(map(
                lambda k: 'nav-' + k,
                truthful(self.props['tweaks']).keys())),
            self.render_items())


class DropdownMenu(BlockTag, Menu):
    options = Options(blocks=['toggle', 'menu'])

    def get_items(self):
        return self.props['menu']

    def DOM(self):
        if isinstance(self.props['menu'], list):
            self.props['menu'] = self.render_items()

        return self.fmt('''
            <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                    {toggle}
                    <span class="caret"></span>
                </a>
                <ul class="dropdown-menu">{menu}</ul>
            </li>
            ''')
