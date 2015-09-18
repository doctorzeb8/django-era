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

from ..components import ObjectsList, ChangeList
from ..utils.functools import just, call, first, pluck, \
    map_keys, map_values, reduce_dict, filter_dict
from ..utils.translation import _, get_string, get_model_names, verbose_choices
from .base import BaseView


class ListView(BaseView, BaseListView):
    components = {'content': ObjectsList}
    list_display = []

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

    def lookup_field_display(self, obj, field, model=True):
        method = 'get_{0}_display'.format(field)
        if isinstance(obj, self.model) and hasattr(self, method):
            return getattr(self, method)(obj)
        elif model:
            return call(getattr(obj, method, lambda: getattr(obj, field)))
        raise AttributeError('Missing display data for "{0}"'.format(field))

    def display_column(self, field):
        if isinstance(field, dict):
            return field['name']
        elif isinstance(field, ManyToOneRel):
            return field.field.model._meta.verbose_name_plural
        else:
            return field.verbose_name

    def display_field(self, name, field, obj):
        if isinstance(field, dict):
            return self.lookup_field_display(
                obj,
                get_string(field['name']).replace(' ', '_'),
                model=False)
        elif '__' in get_string(name):
            return self.lookup_field(obj, name, end_obj=self.lookup_field_display)
        else:
            value = self.lookup_field_display(obj, field.name)
            if isinstance(field, ManyToOneRel) and not isinstance(value, str):
                return value.count()
            return value

    def get_thead_items(self):
        return list(map(
            self.display_column, map(
                self.get_model_field,
                self.get_list_view('display'))))

    def get_tbody_items(self, objects):
        return list(map(
            lambda obj: {
                'pk': obj.pk,
                'fields': list(map(
                    lambda name: self.display_field(
                        name, self.get_model_field(name), obj),
                    self.get_list_view('display')))},
            objects))

    def get_context_data(self, **kw):
        data = super().get_context_data(**kw)
        return dict(
            data,
            thead=self.get_thead_items(),
            tbody=self.get_tbody_items(data['object_list']))


class AdminView(ListView):
    components = {'content': ChangeList}
    list_filter = []
    list_counters = []
    list_sort = []
    list_search = []
    actions = [{
        'icon': 'plus-square',
        'title': _('Add'),
        'level': 'success',
        'link': {'rel': 'add'}}]

    @property
    def objects(self):
        if not hasattr(self, '_objects'):
            self._objects = self.get_queryset(ignore_state=True)
        return self._objects

    @property
    def filters(self):
        return self.get_filters()

    @property
    def filter_keys(self):
        return map(
            first, map(
                lambda name: self.get_filter(name, self.get_model_field(name)),
                self.get_list_view('filter')))

    @property
    def sort_keys(self):
        return map(
            lambda name: name.replace('__', '.'),
            self.get_list_view('sort'))

    @property
    def active_filters(self):
        return list(map(
            first, filter(
                lambda f: f[1] in self.request.GET,
                zip(
                    self.list_filter,
                    map(
                        lambda key: '-'.join(['filter', key]),
                        self.filter_keys)))))

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

    def get_queryset(self, ignore_state=False):
        qs = self.model.objects.all() if self.queryset is None else self.queryset
        if not ignore_state:
            states = {k: self.get_state(k) for k in ('filter', 'sort')}
            if states['filter']:
                qs = qs.filter(**states['filter'])
            if states['sort']:
                qs = qs.order_by(*reduce_dict(
                    lambda k, v: ('-' if v is False else '') + k,
                    states['sort']))
            if 'search' in self.request.GET:
                for word in self.request.GET['search'].split():
                    qs = qs.filter(reduce(
                        operator.or_, map(
                        lambda lookup: Q(**{lookup: word}),
                        map(
                            lambda f: '__'.join([f, 'icontains']),
                            self.get_list_view('search')))))
        return qs

    def get_list_view(self, op, value=None):
        if op == 'display':
            value = list(filter(
                lambda f: not f in self.active_filters,
                (value or self.list_display)))
        return super().get_list_view(op, value)

    def get_actions(self):
        return self.actions

    def get_generic_filter(self, name, choices):
        result = []
        name = name.replace('__', '.')
        values = pluck(self.objects, name)
        for choice in choices:
            count = values.count(choice[0])
            if count:
                result.append(list(chain(choice, [count])))
        return [name, result]

    def get_filter(self, name, field):
        storage = '_{0}_filter'.format(name)
        if not hasattr(self, storage):
            if isinstance(field, BooleanField):
                result = self.get_generic_filter(
                    name, [(True, _('Yes')), (False, _('No'))])
            elif field.is_relation:
                result = self.get_generic_filter(
                    name + '__pk', map(
                        lambda obj: (obj.pk, str(obj)),
                        field.rel.to.objects.all()))
            elif hasattr(field, 'choices'):
                result = self.get_generic_filter(name, field.choices)
            else:
                method = 'get_{0}_filter'.format(get_string(name))
                result = getattr(self, method)(name, field)
            setattr(self, storage, result)
        return getattr(self, storage)

    def get_filters(self):
        return list(map(
            lambda name: chain(
                [self.display_column(self.get_model_field(name))],
                self.get_filter(name, self.get_model_field(name)),
                [name in self.get_list_view('counters')]),
            self.get_list_view('filter')))

    def get_thead_items(self):
        return map(
            lambda name: [
                self.display_column(self.get_model_field(name)),
                name in self.get_list_view('sort') and name.replace('__', '.')],
            self.get_list_view('display'))

    def get_context_data(self, **kw):
        return dict(
            super().get_context_data(**kw),
            actions=self.get_actions(),
            filters=self.filters,
            search=bool(len(self.get_list_view('search'))))

    def get_redirect_features(self):
        if not self.objects:
            return self.navigate('-'.join([
                get_string(get_model_names(self.model)[0]),
                'add']))
        if self.list_filter and not self.request.GET:
            kw = {}
            for (title, key, choices, counters) in self.filters:
                choices = list(map(first, choices))
                if len(choices) == 1:
                    kw['-'.join(['filter', key])] = choices[0]
            if kw:
                return redirect('?'.join([self.request.path, urlencode(kw)]))

    def get(self, request, *args, **kwargs):
        return self.get_redirect_features() \
            or super().get(request, *args, **kwargs)
