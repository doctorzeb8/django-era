import operator
from functools import reduce
from itertools import chain
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import Count, Q
from django.db.models.fields import BooleanField, FieldDoesNotExist
from django.db.models.fields.related import ManyToOneRel
from django.shortcuts import redirect
from django.utils.functional import cached_property
from django.views.generic.list import BaseListView

from ..components import ChangeList
from ..utils.functools import just, call, first, pluck, pick, omit, \
    map_keys, map_values, reduce_dict, filter_dict
from ..utils.translation import _, get_string, get_model_names, verbose_choices
from .base import BaseView, DisplayAttrMixin


class ListView(DisplayAttrMixin, BaseView, BaseListView):
    list_display = []

    @property
    def columns(self, *args, **kw):
        if not hasattr(self, '_columns'):
            self._columns = self.get_list_view('display')
        return self._columns

    def get_column_key(self, column):
        if isinstance(column, str):
            return column
        return column.string.replace(' ', '_')

    def lookup_field(self, obj, field, next_obj=getattr, end_obj=getattr):
        if not '__' in field:
            return end_obj(obj, field)
        return self.lookup_field(
            next_obj(obj, field.split('__')[0]),
            '__'.join(field.split('__')[1:]),
            next_obj=next_obj,
            end_obj=end_obj)

    def get_model_field(self, field):
        try:
            return self.lookup_field(
                self.model,
                get_string(field),
                next_obj=lambda model, field: model._meta.get_field(field).rel.to,
                end_obj=lambda model, field: model._meta.get_field(field))
        except FieldDoesNotExist:
            return {'name': field}

    def get_list_view(self, op, value=None):
        return value or getattr(self, 'list_' + op)

    def display_column(self, field):
        if isinstance(field, dict):
            return field['name']
        elif isinstance(field, ManyToOneRel):
            return field.field.model._meta.verbose_name_plural
        else:
            return field.verbose_name

    def display_field(self, name, field, obj):
        if isinstance(field, dict):
            return self.display_attr(
                obj,
                get_string(field['name']).replace(' ', '_'),
                model=False)
        elif '__' in get_string(name):
            return self.lookup_field(obj, name, end_obj=self.display_attr)
        else:
            value = self.display_attr(obj, field.name)
            if isinstance(field, ManyToOneRel) and not isinstance(value, str):
                return value.count()
            return value

    def display_objects(self, objects, **kw):
        return list(map(
            lambda obj: dict({'pk': obj.pk}, **dict(map(
                lambda c: (
                    self.get_column_key(c),
                    self.display_field(c, self.get_model_field(c), obj)),
                kw.get('columns') or self.columns))),
            objects))


class CollectionView(ListView):
    autochoice = True
    components = {'content': ChangeList}
    list_filter = []
    list_counters = []
    list_sort = []
    list_search = []
    search_method = 'icontains'
    default_state = {}
    paginate_by = 15
    actions = [{
        'icon': 'plus-square',
        'title': _('Add'),
        'level': 'success',
        'link': {'rel': 'add'}}]

    @property
    def stateful(self):
        if not hasattr(self, '_stateful'):
            self._stateful = self.check_stateful()
        return self._stateful

    def check_stateful(self):
        return True

    def map_attr(self, attr):
        return attr.replace('__', '.')

    def map_state(self, key, method='filter'):
        return '-'.join([method, key])

    def get_default_state(self):
        return self.default_state

    def get_state(self, method):
        return map_keys(
            lambda k: k.replace('.', '__'),
            map_values(
                lambda v: v if not v in ('True', 'False') else v[0] == 'T',
                filter_dict(
                    lambda k, v: k in list(getattr(self, '_'.join([method, 'keys']))),
                    map_keys(
                        lambda k: k.split('-')[1],
                        filter_dict(
                            lambda k, v: k.startswith(method),
                            self.request.GET)))))

    def get_queryset(self, ignore_state=False, ignore_attrs=None):
        if not ignore_state and self.stateful:
            qs = self.queryset or self.model.objects.all()
            if self.states['filter']:
                qs = qs.filter(**filter_dict(
                    lambda k, v: not k in (ignore_attrs or []),
                    self.states['filter']))
            if 'search' in self.request.GET:
                for word in self.request.GET['search'].split():
                    qs = qs.filter(reduce(
                        operator.or_, map(
                        lambda lookup: Q(**{lookup: word}),
                        map(
                            lambda f: '__'.join([f, self.search_method]),
                            self.get_list_view('search')))))
            if not ignore_attrs and self.states['sort']:
                qs = qs.order_by(*reduce_dict(
                    lambda k, v: ('-' if v is False else '') + k,
                    self.states['sort']))
            return qs
        return super().get_queryset()

    def resolve_generic_filter(self, attr, choices, state):
        result = {'key': self.map_attr(attr)}
        if choices:
            result['choices'] = []
            values = pluck(
                self.get_queryset(ignore_state=(not state), ignore_attrs=[attr]),
                result['key'])
            for choice in choices:
                count = values.count(choice[0])
                if count:
                    result['choices'].append(list(chain(choice, [count])))
        return result

    def resolve_filter(self, attr, state):
        field = self.get_model_field(attr)
        if isinstance(field, BooleanField):
            result = self.resolve_generic_filter(
                attr,
                state is not None and [(True, _('Yes').lower()), (False, _('No').lower())],
                state)
        elif field.is_relation:
            result = self.resolve_generic_filter(
                attr + '__pk',
                state is not None and map(
                    lambda obj: (obj.pk, str(obj)),
                    field.rel.to.objects.all()),
                state)
        elif getattr(field, 'choices', []):
            result = self.resolve_generic_filter(
                attr,
                state is not None and field.choices,
                state)
        else:
            method = 'resolve_{0}_filter'.format(get_string(attr))
            result = getattr(self, method)(attr, state=state)
        return result

    def resolve_filters(self, **kw):
        return list(map(
            lambda name: dict({'name': name}, **self.resolve_filter(name, **kw)),
            self.get_list_view('filter')))

    def get_filters(self):
        return list(map(
            lambda f: dict(f, **{
                'title': self.display_column(self.get_model_field(f['name'])),
                'counters': f['name'] in self.get_list_view('counters')}),
            self.resolve_filters(state=True)))

    def get_actions(self):
        return self.actions

    def change_list_view(self, op, value=None):
        if self.stateful and op == 'display':
            value = list(filter(
                lambda f: not f in self.active_filters,
                (value or self.list_display)))
        return value

    def get_list_view(self, op, value=None):
        if not hasattr(self, '_list_view'):
            self._list_view = {}
        if not op in self._list_view:
            self._list_view[op] = super().get_list_view(
                op, self.change_list_view(op, value))
        return self._list_view[op]

    def define_state(self):
        self.sort_keys = list(map(
            self.map_attr,
            self.get_list_view('sort')))
        self.filter_keys = list(map(
            lambda f: f['key'],
            self.resolve_filters(state=None)))
        self.states = {k: self.get_state(k) for k in ('filter', 'sort')}
        self.active_filters = list(map(
            first,
            filter(
                lambda z: self.map_state(z[-1]) in self.request.GET,
                zip(self.get_list_view('filter'), self.filter_keys))))

    @property
    def redirection(self):
        if self.stateful:
            default_state = self.get_default_state()
            if not self.model.objects.count():
                return self.navigate('-'.join([
                    get_string(get_model_names(self.model)[0]),
                    'add']))
            elif not self.request.GET and default_state:
                kw = {}
                if 'filters' in default_state:
                    for f in self.resolve_filters(state=False):
                        if self.autochoice and len(f['choices']) == 1:
                            kw[self.map_state(f['key'])] = f['choices'][0][0]
                        elif f['key'] in default_state['filters']:
                            kw[self.map_state(f['key'])] = default_state['filters'][f['key']]
                if 'sort' in default_state:
                    kw.update(map_keys(
                        lambda k: self.map_state(k, 'sort'),
                        self.default_state['sort']))
                if kw:
                    return redirect('?'.join([self.request.path, urlencode(kw)]))
            self.define_state()

    def get(self, request, *args, **kw):
        return self.redirection or super().get(request, *args, **kw)

    def get_guide(self):
        return list(map(
            lambda name: [
                self.get_column_key(name),
                self.display_column(self.get_model_field(name)),
                name in self.get_list_view('sort') and self.map_attr(name)],
            self.columns))

    def get_context_data(self, **kw):
        data = super().get_context_data(**kw)
        if self.stateful:
            data.update({
                'guide': self.get_guide(),
                'filters': self.get_filters(),
                'actions': self.get_actions(),
                'search': bool(len(self.get_list_view('search')))})
        return dict(data, objects=self.display_objects(data['object_list']))
