from functools import reduce
from itertools import chain

from django.core.urlresolvers import resolve, reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import OneToOneField
from django.forms.models import modelform_factory, inlineformset_factory
from django.http import Http404
from django.shortcuts import redirect
from django.utils.functional import cached_property
from django.views.generic.edit import FormMixin

from ..forms import FixedSelect
from ..components import Form
from ..utils.functools import just, call, swap, throw, \
    pluck, first, select, separate, emptyless, get, omit, pick, map_keys, map_values
from ..utils.translation import _, inflect, get_string, get_model_names
from .base import BaseView


class ModelFormMixin:
    @cached_property
    def model(self):
        return getattr(
            self,
            'model_class',
            hasattr(self.form_class, '_meta') \
            and self.form_class._meta.model or None)

    @cached_property
    def instance(self):
        return call(getattr(self, 'get_instance', lambda: None))

    def get_model_name(self, key='single', fn=get_string, model=None):
        return get(key, dict(
            zip(('single', 'plural'),
            map(fn, get_model_names(model or self.model)))))

    def get_model_fields(self, model=None):
        return pluck((model or self.model)._meta.fields[1:], 'name')

    def get_fields(self):
        return self.form_class and self.form_class._meta.fields \
            or getattr(self, 'fields', self.get_model_fields())

    def get_choices(self, model, field):
        return list(model._meta.get_field(field).choices)

    def get_relation_fields(self):
        return [] if not self.model else filter(
            lambda field: isinstance(field, OneToOneField),
            emptyless(map(
                lambda field: field in self.model._meta.get_all_field_names() \
                    and self.model._meta.get_field(field) or None,
                self.get_fields())))

    def get_form_class(self):
        return self.form_class or modelform_factory(
            self.model, fields=self.get_fields())

    def get_form_data(self, **kw):
        result = pick(kw, 'prefix', 'initial', 'instance')
        if self.request.POST:
            result['data'] = self.request.POST
        if self.request.FILES:
            result['files'] = self.request.FILES
        return result

    def get_form(self):
        form = self.get_form_class()(**self.get_form_kwargs())
        for field in pluck(self.get_relation_fields(), 'name'):
            form.fields.pop(field)
        return form

    def get_relation(self, field, **kw):
        kw = kw or {'fields': self.get_model_fields(field.rel.to)}
        form = modelform_factory(field.rel.to, **kw)(
            **self.get_form_data(
                prefix=field.name,
                instance=getattr(self.instance, field.name, None)))
        return {'field': field, 'form': form}

    def get_relations(self):
        return emptyless(map(
            lambda field: swap(field, getattr(
                self,
                'get_{0}_relation'.format(field.name),
                self.get_relation)),
            self.get_relation_fields()))


class FormsetsMixin(ModelFormMixin):
    def get_formsets(self):
        return []

    def fill_matrix(self, factory, fields):
        choices = dict(map(
            lambda field: (field, list(filter(
                lambda choice: not choice in list(map(
                    lambda instance: getattr(instance, field),
                    factory.model.objects.filter(
                        **{factory.fk.name: self.instance}))),
                map(first, self.get_choices(factory.model, field))))),
            fields))
        return list(map(
            lambda i: map_values(lambda c: select(i, c), choices),
            range(0, factory.extra)))

    def get_formset_factory(self, formset_model, **kw):
        if 'matrix' in kw:
            max_num = max(map(
                lambda field: len(self.get_choices(formset_model, field)),
                kw['matrix']))
            kw = dict({k: max_num for k in ('extra', 'max_num')}, **kw)
            kw['widgets'] = {f: FixedSelect() for f in kw.pop('matrix', [])}
        if not 'fields' in kw and not 'form' in kw:
            kw['fields'] = self.get_model_fields(formset_model)
        return inlineformset_factory(
            kw.pop('model', self.model), formset_model, **kw)

    def get_formset_data(self, factory, **kw):
        result = self.get_form_data(instance=self.instance, **kw)
        if 'matrix' in kw:
            result['initial'] = self.fill_matrix(factory, kw['matrix'])
        return result

    def inline_formset(self, formset_model, **kw):
        factory = self.get_formset_factory(formset_model, **kw.copy())
        prefix = self.get_model_name('plural', model=factory.model)
        get_data = getattr(self, 'get_{0}_formset_data'.format(prefix), self.get_formset_data)
        formset = factory(**get_data(factory, **dict(kw, prefix=prefix)))

        if formset.can_delete and formset.validate_min:
            for form in formset.forms[:formset.min_num]:
                form.fields['DELETE'].widget.attrs['disabled'] = True
        return formset


class FormView(BaseView, FormsetsMixin, FormMixin):
    use_prefix = False
    components = {'content': Form}
    form_props = {}
    success_redirect = 'index'
    success_message = None
    actions = [{
        'icon': 'check-square',
        'title': _('Save'),
        'level': 'success'}]

    @property
    def url_match(self):
        return resolve(self.request.path)

    def get_attrs_dict(self, *attrs):
        return dict(map(lambda x: (x, call(getattr(self, 'get_' + x))), attrs))

    def get_prefix(self):
        return self.prefix or (self.use_prefix and self.about or None)

    def get_form_kwargs(self):
        return self.get_form_data(**dict(
            {} if not self.instance else {'instance': self.instance},
            **self.get_attrs_dict('prefix', 'initial')))

    def get_members(self):
        result = self.get_attrs_dict('form', 'relations', 'formsets')
        return result

    def get_all_forms(self, **kw):
        return chain(
            [kw['form']],
            pluck(kw['relations'], 'form'),
            *pluck(kw['formsets'], 'forms'))

    def get_media(self, **kw):
        return reduce(
            lambda x, y: x + y,
            pluck(self.get_all_forms(**kw), 'media'))

    def get_actions(self):
        return self.actions

    def get_form_props(self):
        return dict(self.form_props, actions=self.get_actions())

    def get_context_data(self, **kw):
        members = kw or self.get_members()
        return dict(
            super().get_context_data(**members),
            **map_keys(
                lambda key: key if not self.use_prefix else '_'.join(
                    [self.get_prefix(), key]),
                dict(
                    members,
                    props=self.get_form_props())))

    def get_success_message(self, **kw):
        return self.success_message

    def get_success_redirect(self, **kw):
        return reverse(getattr(self, 'success_redirect', self.url_match.url_name))

    def success_finish(self, **kw):
        self.send_message('success', self.get_success_message(**kw))
        return redirect(self.get_success_redirect(**kw))

    def save_relations(self, form, *relations):
        for rel in relations:
            if rel['form'].has_changed():
                setattr(form.instance, rel['field'].name, rel['form'].save())

    def save_form(self, form):
        hasattr(form, 'instance') and form.instance.save()

    def save_formsets(self, form, *formsets):
        for formset in formsets:
            formset.instance = form.instance
            formset.save()

    def process_valid(self, **kw):
        self.save_relations(kw['form'], *kw['relations'])
        self.save_form(kw['form'])
        self.save_formsets(kw['form'], *kw['formsets'])
        return self.success_finish(**kw)

    def process_invalid(self, **kw):
        errors = chain(*map(call, pluck(
            self.get_all_forms(**kw), 'non_field_errors')))
        for message in errors:
            self.send_message('error', message)
        return self.render_to_response(self.get_context_data(**kw))

    def check_is_valid(self, **kw):
        return all(map(lambda x: x.is_valid(), self.get_all_forms(**kw)))

    def process(self, **kw):
        if self.check_is_valid(**kw):
            map(
                lambda x: x.save(commit=False),
                chain(
                    hasattr(kw['form'], 'save') and [kw['form']] or [],
                    *pluck(kw['relations'], 'form')))
            return self.process_valid(**kw)
        return self.process_invalid(**kw)

    def post(self, request, *args, **kw):
        return self.process(**self.get_members())


class ObjectView(FormView):
    def get_instance(self):
        pk = self.url_match.kwargs.get('pk')
        try:
            return pk and self.model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404

    def get_form_props(self):
        return dict(
            super().get_form_props(),
            panels=True,
            title=self.instance and str(self.instance) or self.model._meta.verbose_name)

    def get_success_redirect(self, **kw):
        return reverse(self.get_model_name('plural'))

    def get_success_message(self, **kw):
        return inflect(_(
            'The %(name)s "%(obj)s" was changed successfully.' \
            if self.url_match.kwargs else \
            'The %(name)s "%(obj)s" was added successfully.') % {
                'name': self.get_model_name(fn=just),
                'obj': str(kw['form'].instance)})
