from itertools import chain
from django.forms import widgets
from django.forms.widgets import CheckboxInput
from django.template.defaulttags import CsrfTokenNode

from ..forms import EmptyWidget
from ..utils.functools import call, unpack_args, factual, pluck, separate, \
    case, pick, omit, truthful
from .library import register, Component, Tag, ScriptedTag
from .markup import Row, Column, Table, Link, Button, Caption, Panel, Icon


class WidgetCaseMixin:
    def get_widgets(self, *args):
        return list(map(lambda x: getattr(widgets, x), args))

    def check_widget_in(self, *args):
        return self.props.field.field.widget.__class__ in self.get_widgets(*args)

    @property
    def is_text_input(self):
        return getattr(
            self.props.field.field.widget,
            'is_text_input',
            self.check_widget_in(
                'TextInput', 'NumberInput', 'EmailInput',
                'URLInput', 'PasswordInput', 'Textarea', 'Select'))

    @property
    def have_placeholder(self):
        return self.check_widget_in('TextInput', 'Textarea', 'NumberInput')


class RequiredAttrMixin:
    @property
    def need_required(self):
        return self.props.set_required and self.props.field.field.required


class Input(WidgetCaseMixin, RequiredAttrMixin, Component):
    def DOM(self):
        return self.props.field.as_widget()

    def tweak(self):
        super().tweak()
        if self.is_text_input:
            self.dom.add_class('form-control')
        if self.need_required:
            self.dom.add_attr('required')
        if self.props.inline:
            self.dom.add_attr('placeholder', self.props.field.label)
        elif self.have_placeholder:
            self.dom.add_attr('placeholder', self.props.field.help_text)


class Label(RequiredAttrMixin, Tag):
    el = 'label'
    named = False

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
    named = False

    @property
    def is_valid(self):
        return self.props.valid

    def get_defaults(self):
        return {'valid': None, 'inline': False}

    def resolve_attrs(self):
        return {'class': ' '.join(factual([
            'form-group',
            case(self.is_valid, {
                True: 'has-success',
                False: 'has-error', None: ''})]))}


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
        if self.props.field.help_text and not self.have_placeholder:
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


class FieldsetMixin:
    def render_fieldset(self, form, **props):
        [hidden, fields] = separate(lambda f: not f.is_hidden, form)
        return map(unpack_args(
            lambda i, field: ''.join([
                '' if i else ''.join(map(lambda f: f.as_widget(), hidden)),
                self.inject(Field, dict({'field': field}, **props))])),
            enumerate(fields))


class Formset(Table, FieldsetMixin):
    def get_slice(self):
        have_instances = any([f.instance.pk for f in self.props.formset.forms])
        return (0, -1 if self.props.formset.can_delete and not have_instances else None)

    def get_thead_items(self):
        return factual(map(
            lambda f: not f.is_hidden and f.label,
            self.props.formset.forms[0]))

    def get_form_fields(self, form):
        if self.props.formset.can_delete and not form.instance.pk:
            form.fields['DELETE'].widget = EmptyWidget()
        return tuple(form)

    def get_tbody_items(self):
        return map(
            lambda form: {'items': self.render_fieldset(
                self.get_form_fields(form),
                inline=False,
                set_label=False,
                set_required=False)},
            self.props.formset.forms)


class Action(Tag):
    def get_button_props(self):
        if not pick(self.props, 'link', 'onclick'):
            return dict({'type': 'submit'}, **pick(self.props, 'level'))
        return pick(self.props, 'level', 'onclick')

    def get_link_props(self):
        if isinstance(self.props.link, str):
            return {'url': self.props.link}
        return self.props.link

    def get_nodelist(self):
        result = self.inject(
            Button, self.get_button_props(), self.inject(
                Caption, pick(self.props, 'icon', 'title')))
        if 'link' in self.props:
            return self.inject(Link, self.get_link_props(), result)
        return result


@register.era
class Form(ScriptedTag, FieldsetMixin):
    el = 'form'
    inline = True
    named = False

    def get_defaults(self):
        return {
            'prefix': '',
            'action': self.request.get_full_path(),
            'method': 'POST',
            'novalidate': False,
            'inline': False,
            'panels': False,
            'spinner': False,
            'title': '',
            'splitters': [],
            'relations': [],
            'formsets': []}

    def get_context_prop(self, prop, default=None):
        return self.context.get(
            '_'.join(factual([self.props.prefix, prop])),
            default)

    def resolve_enctype(self):
        if any(map(
            lambda x: x.is_multipart(),
            chain(
                [self.props.form],
                pluck(self.props.relations, 'form'),
                self.props.formsets))):
            return 'multipart/form-data'
        return 'application/x-www-form-urlencoded'

    def resolve_props(self):
        return dict(
            truthful(dict(map(
                lambda p: (p, self.get_context_prop(p)),
                ['form', 'relations', 'formsets']))),
            **self.get_context_prop('props', {}))

    def split_fields(self):
        result = [[]]
        for field in self.props.form:
            result[-1].append(field)
            if field.name in self.props.splitters:
                result.append([])
        return result

    def render_panel(self, **kw):
        if self.props.panels:
            if kw['body']:
                return self.inject(Panel, kw)
        return kw['body']

    def render_fields(self):
        if self.props.splitters:
            columns = self.split_fields()
            result = ''.join(map(
                lambda column: self.inject(
                    Column,
                    {'md': int(12 / len(columns)), 'xs': 12},
                    ''.join(self.render_fieldset(
                        column,
                        **pick(self.props, 'inline')))),
                columns))
        else:
            result = ''.join(self.render_fieldset(
                self.props.form,
                **pick(self.props, 'inline')))
        return self.render_panel(caption={'title': self.props.title}, body=result)

    def render_relations(self):
        return ''.join(map(
            lambda relation: self.render_panel(
                caption={'title': relation['field'].verbose_name},
                body=''.join(
                    self.render_fieldset(
                        relation['form'],
                        set_required=relation['required']))),
            self.props.relations))

    def render_formsets(self):
        return ''.join(map(
            lambda formset: self.render_panel(
                caption={'title': formset.model._meta.verbose_name_plural},
                body=''.join([
                    str(formset.management_form),
                    self.inject(Formset, {'formset': formset})])),
            self.props.formsets))

    def render_actions(self):
        return self.inject(
            Group,
            {'class': 'actions'},
            ''.join(map(
                lambda action: self.inject(Action, action),
                self.props.actions)))

    def resolve_script(self):
        result = pick(self.props, 'spinner', 'action')
        if self.props.spinner:
            result['spinner'] = self.inject(Icon, {
                'name': self.props.spinner,
                'spin': True,
                'large': True})
        return result

    def get_nodelist(self):
        return ''.join(chain(
            [CsrfTokenNode().render(self.context)],
            map(
                lambda content: '' if not content else \
                    self.props.inline and content or \
                    self.inject(Row, {}, content),
                self.build(('fields', 'relations', 'formsets', 'actions')))))

    def resolve_attrs(self):
        return dict(
            self.props.novalidate and {'novalidate': None} or {}, **{
            'class': 'form',
            'method': self.props.method,
            'action': self.props.action,
            'enctype': self.resolve_enctype()})
