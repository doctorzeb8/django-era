from django.conf import settings
from django.views.generic.list import BaseListView
from ..components import ObjectsList, CRUD
from ..utils.functools import just, call
from .base import BaseView


class ListView(BaseView, BaseListView):
    components = {'content': ObjectsList}
    list_display = []

    def get_context_data(self, **kw):
        data = super().get_context_data(**kw)
        return dict(
            data,
            thead=self.get_thead_items(),
            tbody=self.get_tbody_items(data['object_list']))

    def get_thead_items(self):
        return map(
            lambda field: self.process_field(
                field,
                is_string=False,
                fn=lambda f: self.model._meta.get_field(f).verbose_name),
            self.list_display)

    def get_tbody_items(self, objects):
        return map(
            lambda item: {'pk': item.pk, 'fields': list(map(
                lambda field: self.display_field(item, field),
                map(
                    lambda field: self.process_field(
                        field,
                        is_string=True,
                        fn=lambda f: f.message),
                    self.list_display)))},
            objects)

    def display_field(self, item, field):
        method = 'get_{0}_display'.format(field)
        return call(getattr(
            self, method, lambda: call(getattr(
                item, method, lambda: getattr(
                    item, field)))))

    def process_field(self, field, is_string=True, fn=just):
        return field if is_string == isinstance(field, str) else fn(field)



class CRUDView(ListView):
    components = {'content': CRUD}
    editable = settings.CRUD_PATTERN
    list_filter = []
    list_editable = []
    actions = ('add', 'update', 'delete')

    add_action = {
        'icon': 'plus-square',
        'title': 'add',
        'level': 'success',
        'link': {'rel': 'add'}}
    delete_action = {
        'icon': 'minus-square',
        'title': 'delete',
        'level': 'danger'}
    update_action = {
        'icon': 'pencil-square',
        'title': 'update',
        'level': 'warning'}

    def get_context_data(self, **kw):
        return dict(
            super().get_context_data(**kw),
            actions=self.get_actions())

    def get_update_perm(self):
        return bool(self.list_editable)

    def get_actions(self):
        return map(
            lambda perm: dict(
                getattr(self, '_'.join([perm, 'action'])),
                **dict(
                    getattr(settings, '_'.join(['list', perm, 'action']).upper()),
                    **call(getattr(self, 'get_{0}_action'.format(perm), lambda: {})))),
            filter(
                lambda perm: call(getattr(
                    self,
                    'get_{0}_perm'.format(perm),
                    lambda: getattr(
                        self, '_'.join(['can', perm]), self.editable))),
                self.actions))
