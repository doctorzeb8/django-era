from itertools import chain
from django.core.urlresolvers import resolve
from ..utils.functools import call, pick
from .library import Component, Tag
from .markup import Table, Column, Link
from .forms import Action


class ObjectsList(Component):
    def resolve_props(self):
        return self.context.dicts[1]

    def render_row(self, row):
        return {'items': row['fields']}

    def render_queryset(self):
        return self.inject(
            Table, {
                'thead': self.props.thead,
                'tbody': map(self.render_row, self.props.tbody)})

    def DOM(self):
        return self.render_queryset()


class CRUD(ObjectsList):
    def render_row(self, row):
        return {'items': chain(
            [self.inject(Link, {'rel': str(row['pk'])}, row['fields'][0])],
            row['fields'][1:])}

    def render_actions(self):
        return ''.join(map(
            lambda action: self.inject(Action, action),
            self.props.actions))

    def render_panel(self):
        return ''.join([self.render_actions()])

    def DOM(self):
        return ''.join([
            self.inject(Column, {'md': 9, 'class': 'list-qs'}, self.render_queryset()),
            self.inject(Column, {'md': 3, 'class': 'list-panel'}, self.render_panel())])
