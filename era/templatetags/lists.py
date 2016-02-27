from itertools import chain
from django.conf import settings
from django.core.urlresolvers import resolve

from ..utils.functools import call, unpack_args, factual, just, pick, first
from ..utils.translation.string import _
from .library import Component, Tag, ScriptedTag
from .markup import MarkedList, Break, Link, Icon, Caption, Column, Panel, Table
from .forms import Action


class QuerySetKey(Link):
    def get_defaults(self):
        return dict(super().get_defaults(), replace=False, collapse=False, clean=[])

    def get_url(self):
        qd = self.request.GET.copy()
        if self.props.replace:
            for key in qd.copy().keys():
                if key.startswith(self.props.method):
                    qd.pop(key)
        if self.props.value is None:
            self.props.clean.append(self.props.argument)
        else:
            qd[self.props.argument] = self.props.value
        for arg in self.props.clean:
            arg in qd and qd.pop(arg)
        return '?'.join([self.request.path, qd.urlencode()]).rstrip('?')

    def resolve_props(self):
        return {
            'reverse': False,
            'argument': '-'.join(factual([self.props.method, self.props.key]))}

    def resolve_attrs(self):
        if (self.props.value is None and not self.props.argument in self.request.GET) \
        or str(self.props.value) == self.request.GET.get(self.props.argument):
            return {}
        return super().resolve_attrs()

    def DOM(self):
        if not self.props.attrs:
            if not self.props.collapse:
                return self.props.nodelist
            return ''
        return super().DOM()


class QuerySetFilter(Panel):
    def render_key(self, value, name, count=None):
        return self.inject(
            QuerySetKey, dict({
                'method': 'filter',
                'key': self.props.key,
                'clean': ['page'],
                'value': value,
                'collapse': value is None}),
            ' '.join([
                str(name),
                '({0})'.format(count) if self.props.counters and count else '']))

    def render_clear(self):
        if not self.props.get('ignore_length', False) and len(self.props.choices) == 1:
            return ''
        return self.render_key(None, self.inject(
            Icon, {'name': 'remove', 'class': 'qs-clear pull-right'}))

    def render_title(self):
        return ''.join([str(self.props.title), self.render_clear()])

    def render_keys(self):
        return self.inject(
            Break, {'join': map(
                unpack_args(self.render_key),
                self.props.choices)})

    def resolve_props(self):
        return dict(super().resolve_props(), **{
            'title': self.render_title(),
            'body': self.render_keys()})


class SortableTable(Table):
    def render_arrow(self, title, key):
        if not key:
            return title
        method = 'sort'
        value = self.request.GET.get('-'.join([method, key]))

        if value is None:
            value = True
            icon = None
        elif value == 'True':
            value = False
            icon = 'angle-double-down'
        else:
            value = True
            icon = 'angle-double-up'
        return self.inject(
            QuerySetKey,
            {'method': method, 'key': key, 'value': value, 'replace': True},
            title if icon is None else self.inject(
                Caption, {'title': title, 'icon': icon}))

    def render_content(self, content, cell):
        if cell == 'th':
            return self.render_arrow(*content)
        return super().render_content(content, cell)


class Paginator(MarkedList):
    def resolve_props(self):
        return {'page': self.context['page_obj'], 'class': 'pager'}

    def render_arrow(self, control, direction):
        if not call(getattr(self.props.page, 'has_' + control)):
            return ''
        return self.inject(
            QuerySetKey,
            {
                'method': 'page',
                'key': '',
                'value': call(getattr(self.props.page, control + '_page_number'))},
            self.inject(Icon, {'name': 'angle-double-' + direction}))

    def get_items(self):
        return [
            self.render_arrow('previous', 'left'),
            self.inject(
                Tag, {'el': 'span'}, ' / '.join(map(str, [
                    self.props.page.number,
                    self.props.page.paginator.num_pages]))),
            self.render_arrow('next', 'right')]


class SearchLine(ScriptedTag):
    el = 'input'
    nobody = True

    def resolve_attrs(self):
        return {'class': 'form-control', 'placeholder': _('Search')}


class ChangeList(Component):
    def resolve_props(self):
        return dict(self.context.dicts[2], **settings.ERA_COLLECTIONS)

    def get_location_qs(self):
        return {'next': self.request.get_full_path()}

    def render_objects(self):
        return list(map(
            lambda obj: {'items': chain(
                [self.inject(
                    Link,
                    {'rel': str(obj['pk']), 'qs': self.get_location_qs()},
                    obj.get(first(first(self.props.guide))))],
                map(
                    lambda k: obj.get(k),
                    list(map(first, self.props.guide))[1:]))},
            self.props.objects))

    def render_table(self, component):
        return self.inject(
            component, {
                'thead': map(lambda c: c[1:], self.props.guide),
                'tbody': self.render_objects()})

    def render_queryset(self):
        table = self.render_table(SortableTable)
        if self.context['is_paginated']:
            return ''.join([table, self.inject(Paginator)])
        return table

    def render_actions(self):
        result = ''
        for action in self.props.actions:
            action['link']['qs'] = self.get_location_qs()
            result += self.inject(Action, action)
        return result

    def render_search(self):
        return '' if not self.props.search else self.inject(SearchLine)

    def render_filters(self):
        result = []
        for f in self.props.filters:
            if f['choices']:
                result.append(self.inject(QuerySetFilter, f))
        return result

    def render_panel(self):
        return ''.join(chain(*self.build(('actions', 'search', 'filters'))))

    def DOM(self):
        return ''.join(self.props.reference([
            self.inject(Column, {'md': 9, 'class': 'list-qs'}, self.render_queryset()),
            self.inject(Column, {'md': 3, 'class': 'list-panel'}, self.render_panel())]))
