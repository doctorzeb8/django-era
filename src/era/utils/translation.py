import re
from django.utils.translation import ugettext_lazy
from .functools import unidec, pluck


def normalize(string):
    return ''.join(map(
        lambda e: e[0] and re.sub(r'([A-Z])', r'-\g<1>', e[1]) or e[1],
        enumerate(string))).lower()

def _(string):
    t = ugettext_lazy(string)
    t.message = string
    return t

def verbose_choice(obj, f):
    return dict(obj._meta.get_field(f).choices).get(getattr(obj, f))

def verbose_choices(*args):
    return map(lambda a: (a.message, a), args)


@unidec
def verbose_serialize(fn, *args):
    obj = args and args[0]
    result = fn(*args) or {}
    return map(
        lambda f: (
            obj._meta.get_field(f).verbose_name,
            getattr(obj, 'get_{0}_display'.format(f), lambda: getattr(obj, f))()),
        result.get(
            'fields',
            filter(
                lambda f: not f in result.get('exclude', []),
                pluck(obj._meta.fields, 'name'))))
