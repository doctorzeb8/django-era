from itertools import chain
import re

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.module_loading import import_string
from django.views.generic.base import TemplateResponseMixin, View, RedirectView
from django.views.generic.edit import FormMixin
from django.views.generic.list import BaseListView

from .forms import forms
from .utils.functools import throw, unpack_args, omit, pick, select
from .utils.translation import normalize


class BaseViewMixin:
    @property
    def about(self):
        return re.sub(r'-view$', '', normalize(self.__class__.__name__))

    def send_message(self, level, content):
        content and getattr(messages, level)(self.request, content)

    def navigate(self, name):
        return redirect(reverse(name))


TemplateViewMixins = chain(
    [BaseViewMixin],
    list(map(import_string, settings.TEMPLATE_VIEW_MIXINS)),
    [TemplateResponseMixin, View])


class TemplateView(*TemplateViewMixins):
    components = {}

    def get(self, request, *args, **kwargs):
        return getattr(super(), 'get', lambda r: None)(request) \
            or self.render_to_response(self.get_context_data())

    def get_components(self):
        return {}

    def get_context_data(self, **kw):
        return dict(
            super().get_context_data(**kw),
            components=dict(self.components, **self.get_components()))

    def get_template_names(self):
        return list(map(lambda x: x + '.html', [self.about, 'index']))


class FormView(TemplateView, FormMixin):
    form_class = forms.Form
    form_props = {}
    formsets = []
    truthtables = {}
    success_message = None
    success_redirect = 'index'

    def post(self, request):
        members = self.get_members()
        is_valid = all([
            members['form'].is_valid(),
            all([f.is_valid() for f in members['formsets']])])
        if is_valid and hasattr(members['form'], 'save'):
            members['form'].save(commit=False)
        method = 'process_{0}valid'.format('' if is_valid else 'in')
        return getattr(self, method)(**members)

    def get_members(self):
        return {
            'form': self.get_form(self.get_form_class()),
            'formsets': list(map(lambda p: self.get_formset(p), self.formsets))}

    def get_form_props(self):
        return self.form_props

    def get_context_data(self, **members):
        return dict(
            super().get_context_data(), **dict(
                members or self.get_members(),
                form_props=self.get_form_props()))

    def get_formset_method(self, suffix, prefix, **kw):
        fmt = lambda s: s.format(prefix, suffix)
        method = getattr(
            self,
            fmt('get_{0}_formset_{1}'),
            kw.get('fallback', lambda: throw(
                NotImplemented(fmt('can not get {0} formset {1}')))))
        return method(**dict({'prefix': prefix}, **omit(kw, 'fallback')))

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


class ListView(TemplateView, BaseListView):
    pass
