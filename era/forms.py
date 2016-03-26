import json
from django import forms
from django.conf import settings
from django.templatetags.static import static
from django.utils import translation
from .utils.functools import first, avg


class EmptyWidget(forms.widgets.Widget):
    def render(self, *args, **kw):
        return ''


class Slider(forms.widgets.TextInput):
    class Media:
        css = {'all': [static('seiyria-bootstrap-slider/dist/css/bootstrap-slider.min.css')]}
        js = [
            static('seiyria-bootstrap-slider/dist/bootstrap-slider.min.js'),
            static('widgets/slider.js')]

    def __init__(self, attrs=None):
        attrs = attrs or {}
        if not 'range' in attrs:
            attrs['range'] = range(0, 100, 1)
        attrs.update(dict(zip(('min', 'max', 'step'), map(
            lambda a: getattr(attrs['range'], a),
            ('start', 'stop', 'step')))))
        attrs['value'] = attrs.pop('value', int(
            avg(attrs['range'].start, attrs.pop('range').stop)))
        super().__init__(dict(map(
            lambda t: ('data-slider-' + t[0], t[1]),
            attrs.items())))


class FrozenSelect(forms.widgets.Select):
    def render(self, name, value, attrs=None, choices=()):
        return ''.join([
            str(first([x[1] for x in self.choices if str(x[0]) == str(value)])),
            forms.widgets.HiddenInput().render(name, value)])


class DateTimePicker(forms.widgets.DateTimeBaseInput):
    is_text_input = True

    class Media:
        css = {'all': [static(
            'eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css')]}
        js = [static(
            'eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js')]

    def __init__(self, key='date', attrs=None, options=None):
        self.options = options or {}
        self.set_format(key)
        super().__init__(attrs)

    def set_format(self, key):
        self.format_key = '_'.join([key, 'input_formats']).upper()
        self.options['format'] = ''.join(map(
            lambda c: {
                'j': 'DDD',
                'd': 'DD',
                'B': 'MMMM',
                'b': 'MMM',
                'm': 'MM',
                'Y': 'YYYY',
                'y': 'YY',
                'H': 'HH',
                'I': 'hh',
                'M': 'mm',
                'S': 'ss',
                'p': 'a',
                'z': 'ZZ'} \
                .get(c, c),
            getattr(settings, '_'.join([key, 'format']).upper())))

    def get_icons(self):
        return {
            'time': 'fa fa-clock-o',
            'date': 'fa fa-calendar',
            'up': 'fa fa-arrow-up',
            'down': 'fa fa-arrow-down',
            'next': 'fa fa-arrow-right',
            'previous': 'fa fa-arrow-left'}

    def render(self, name, value, attrs):
        return ''.join([
            super().render(name, value, attrs),
            '''
            <script>
            $("#{0}").datetimepicker({1});
            $("#{0}").keydown(function(e) {{e.preventDefault()}});
            </script>
            '''.format(
                attrs['id'], json.dumps(dict({
                    'icons': self.get_icons(),
                    'locale': translation.get_language(),
                    'ignoreReadonly': True,
                    'stepping': 5
                    }, **(self.options or {}))))])
