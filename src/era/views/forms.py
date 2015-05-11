from itertools import chain
from django.conf import settings
from django.core.urlresolvers import resolve
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.views.generic.edit import FormMixin
from ..components import Form
from ..forms import forms
from ..utils.functools import throw, emptyless, unpack_args, omit, pick, select, reduce_dict
from ..utils.translation import get_string
from .base import BaseView


class FormView(BaseView, FormMixin):
    use_prefix = False
    components = {'content': Form}
    form_class = forms.Form
    form_props = {}
    formsets = []
    truthtables = {}
    success_redirect = 'index'
    success_message = settings.SUCCESS_SAVE_MESSAGE
    actions = [dict(
        {'icon': 'check-square', 'title': 'save', 'level': 'success'},
        **settings.FORM_SUBMIT_ACTION)]

    def post(self, request, *args, **kw):
        members = self.get_members()
        is_valid = all([
            members['form'].is_valid(),
            all([f.is_valid() for f in members['formsets']])])
        if is_valid and hasattr(members['form'], 'save'):
            members['form'].save(commit=False)
        method = 'process_{0}valid'.format('' if is_valid else 'in')
        return getattr(self, method)(**members)

    def get_prefix(self):
        return self.prefix or (self.use_prefix and self.about or None)

    def get_instance(self):
        return None

    def get_members(self):
        return {
            'form': self.get_form(self.get_form_class()),
            'formsets': list(map(lambda p: self.get_formset(p), self.formsets))}

    def get_actions(self):
        return self.actions

    def get_form_kwargs(self):
        instance = self.get_instance()
        return dict(
            super().get_form_kwargs(),
            **(instance and {'instance': instance} or {}))

    def get_form_props(self):
        return dict(self.form_props, actions=self.get_actions())

    def get_context_data(self, **members):
        return dict(
            super().get_context_data(), **dict(reduce_dict(
                lambda k, v: (
                    k if not self.use_prefix else '_'.join(
                        [self.get_prefix(), k]),
                    v),
                dict(
                    members or self.get_members(),
                    props=self.get_form_props()))))

    def get_formset_method(self, suffix, prefix, **kw):
        fmt = lambda s: s.format(get_string(prefix), suffix)
        method = getattr(
            self,
            fmt('get_{0}_formset_{1}'),
            kw.get('fallback', lambda: throw(
                NotImplemented(fmt('can not get {0} formset {1}')))))
        return method(**dict(
            {'prefix': prefix, 'instance': self.get_instance()},
            **omit(kw, 'fallback')))

    def get_truthtables(self, **kw):
        return list(map(
            lambda i: dict(map(
                lambda field: (field, select(i, list(map(
                    lambda x: x[0],
                    kw['cls'].form._meta.model._meta.get_field(field).choices)))),
                self.truthtables[kw['prefix']])),
            range(0, kw['cls'].extra)))

    def get_formsets_data(self, **kw):
        result = pick(kw, 'prefix', 'instance')
        if self.truthtables:
            result['initial'] = self.get_truthtables(**kw)
        if self.request.POST:
            result['data'] = self.request.POST
        if self.request.FILES:
            result['files'] = self.request.FILES
        return result

    def get_formset(self, prefix):
        cls = self.get_formset_method('class', prefix)
        return cls(**self.get_formset_method(
            'data', prefix, cls=cls, fallback=self.get_formsets_data))

    def process_valid(self, form, formsets):
        if hasattr(form, 'instance'):
            form.instance.save()
        for formset in formsets:
            formset.save()
        self.send_message('success', self.success_message)
        return self.navigate(self.success_redirect)

    def process_invalid(self, **kw):
        return self.render_to_response(self.get_context_data(**kw))


class ObjectView(FormView):
    def get_actions(self):
        return chain(
            [dict({
                'icon': 'caret-square-o-left',
                'title': 'back',
                'level': 'default',
                'onclick': 'history.back()'},
                **settings.FORM_BACK_ACTION)],
            super().get_actions())

    def get_instance(self):
        pk = resolve(self.request.path).kwargs.get('pk')
        try:
            return pk and self.form_class._meta.model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise Http404

    def get_form_props(self):
        return dict(super().get_form_props(), panels=True)
