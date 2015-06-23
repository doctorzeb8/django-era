from django import forms
from django.templatetags.static import static
from bootstrap3_datetime.widgets import DateTimePicker
from .utils.functools import first, avg


class EmptyWidget(forms.widgets.Widget):
    def render(self, *args, **kw):
        return ''


class Slider(forms.widgets.TextInput):
    class Media:
        css = {'all': (static('seiyria-bootstrap-slider/dist/css/bootstrap-slider.min.css'), )}
        js = (
            static('seiyria-bootstrap-slider/dist/bootstrap-slider.min.js'),
            static('widgets/slider.js'))

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


class FixedSelect(forms.widgets.Select):
    def render(self, name, value, attrs=None, choices=()):
        return ''.join([
            str(list(filter(lambda c: c[0] == value, self.choices))[0][1]),
            forms.widgets.HiddenInput().render(name, value)])
