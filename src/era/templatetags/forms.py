from itertools import chain
from django.forms import widgets
from django.forms.widgets import TextInput, Textarea, CheckboxInput
from django.template.defaulttags import CsrfTokenNode

from ..utils.functools import call, emptyless, pick, unpack_args, separate
from .library import register, Component, Tag
from .markup import Row, Column
from .tables import Table


class WidgetCaseMixin:
    @property
    def text_input_widgets(self):
        return list(map(
            lambda x: getattr(widgets, x),
            [
                'TextInput', 'NumberInput', 'EmailInput',
                'URLInput', 'PasswordInput', 'Textarea', 'Select']))

    def check_widget_in(self, *args):
        return self.props.field.field.widget.__class__ in args


class RequiredAttrMixin:
    @property
    def need_required(self):
        return self.props.set_required and self.props.field.field.required


class Input(WidgetCaseMixin, RequiredAttrMixin, Component):
    def DOM(self):
        return self.props.field.as_widget()

    def tweak(self):
        super().tweak()
        if self.check_widget_in(*self.text_input_widgets):
            self.dom.add_class('form-control')
        if self.need_required:
            self.dom.add_attr('required')
        if self.props.inline:
            self.dom.add_attr('placeholder', self.props.field.label)
        elif self.props.field.help_text and self.check_widget_in(TextInput, Textarea):
            self.dom.add_attr('placeholder', self.props.field.help_text)


class Label(RequiredAttrMixin, Tag):
    el = 'label'

    def resolve_attrs(self):
        return {
            'for': self.props.field.id_for_label,
            'class': ' '.join([
                'control-label',
                self.need_required and 'required' or ''])}

    def get_nodelist(self):
        return ''.join(map(str, [
            self.props.get('nodelist', ''),
            self.props.field.label]))


class Group(Tag):
    @property
    def is_valid(self):
        return self.props.valid

    def get_defaults(self):
        return {'valid': None, 'inline': False}

    def resolve_attrs(self):
        return {'class': ' '.join(emptyless([
            'form-group',
            {True: 'has-success', False: 'has-error', None: ''}.get(self.is_valid),
            self.props.get('class', '')]))}


class Field(WidgetCaseMixin, Group):
    def get_defaults(self):
        return dict(super().get_defaults(), **{
            'set_label': True,
            'set_required': True})

    @property
    def is_valid(self):
        return (False if self.props.field.errors else True) \
            if hasattr(self.props.field.form, 'cleaned_data') else None

    def inject_control(self, control, nodelist=None):
        return self.inject(
            control, pick(self.props, 'field', 'inline', 'set_required'), nodelist)

    def get_help_block(self):
        if self.props.field.help_text and not self.check_widget_in(TextInput, Textarea):
            return self.inject(
                Tag,
                {'el': 'span', 'class': 'help-block'},
                self.props.field.help_text)

    def get_nodelist(self):
        if isinstance(self.props.field.field.widget, CheckboxInput):
            if not self.props.set_label:
                return self.inject_control(Input)
            return self.inject(
                Tag,
                {'class': 'checkbox'},
                self.inject_control(Label, self.inject_control(Input)))
        return ''.join([
            '' if (self.props.inline or not self.props.set_label) \
                else self.inject_control(Label),
            self.inject_control(Input),
            '' if self.is_valid is not False else self.inject(
                Tag,
                {'el': 'span', 'class': 'help-block'},
                '<br />'.join(map(str, self.props.field.errors))),
            self.get_help_block() or ''])


class Formset(Table):
    @property
    def hslice(self):
        have_instances = any([f.instance.pk for f in self.props.formset.forms])
        return (0, -1 if self.props.formset.can_delete and not have_instances else None)

    def get_form_fields(self, form):
        draw_last = lambda: not (self.props.formset.can_delete and not form.instance.pk)
        [hidden, fields] = separate(lambda f: not f.is_hidden, form)

        return map(unpack_args(
            lambda i, field: ''.join([
                '' if i else ''.join(map(lambda f: f.as_widget(), hidden)),
                '' if len(fields) == (i + 1) and not draw_last() else self.inject(
                    Field, {
                        'field': field,
                        'inline': False,
                        'set_label': False,
                        'set_required': False})])),
            enumerate(fields))

    def get_head_items(self):
        return emptyless(map(
            lambda f: not f.is_hidden and f.label,
            self.props.formset.forms[0]))

    def get_body_items(self):
        return map(
            lambda form: {'items': self.get_form_fields(form)},
            self.props.formset.forms)


@register.era
class Form(Tag):
    el = 'form'

    def get_defaults(self):
        return {
            'action': self.request.path,
            'form': self.context.get('form'),
            'formsets': self.context.get('formsets', []),
            'method': 'POST',
            'novalidate': False,
            'inline': False,
            'splitters': ''}

    def inject_field(self, field):
        return self.inject(
            Field, dict({'field': field}, **pick(self.props, 'inline')))

    def split_fields(self):
        result = [[]]
        for field in self.props.form:
            result[-1].append(field)
            if field.name in self.props.splitters.split(' '):
                result.append([])
        return result

    def render_fields(self):
        if self.props.splitters:
            columns = self.split_fields()
            return ''.join(map(
                lambda column: self.inject(
                    Column,
                    {'md': int(12 / len(columns))},
                    ''.join(map(self.inject_field, column))),
                columns))
        return ''.join(map(self.inject_field, self.props.form))

    def render_formsets(self):
        return ''.join(map(
            lambda formset: ''.join([
                str(formset.management_form),
                self.inject(Formset, {'formset': formset})]),
            self.props.formsets))

    def render_buttons(self):
        return self.inject(
            Group, {'class': 'buttons'}, self.props.nodelist)

    def get_nodelist(self):
        return ''.join(chain(
            [CsrfTokenNode().render(self.context)],
            map(
                lambda content: '' if not content else \
                    self.props.inline and content \
                    or content and self.inject(Row, {}, content),
                map(
                    lambda x: call(getattr(self, 'render_' + x)),
                    ['fields', 'formsets', 'buttons']))))

    def resolve_attrs(self):
        return dict(
            self.props.novalidate and {'novalidate': None} or {}, **{
            'class': 'form',
            'method': self.props.method,
            'action': self.props.action,
            'enctype': 'multipart/form-data' if self.props.form.is_multipart() \
                or any(map(lambda form: form.is_multipart(), self.props.formsets)) \
                else 'application/x-www-form-urlencoded'})
