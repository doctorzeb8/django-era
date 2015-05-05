from django import forms
from django.templatetags.static import static
from bootstrap3_datetime.widgets import DateTimePicker
from .utils.functools import avg


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
