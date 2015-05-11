import re
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy
from .functools import call, unidec, pluck


def normalize(string):
    return ''.join(map(
        lambda e: e[0] and re.sub(r'([A-Z])', r'-\g<1>', e[1]) or e[1],
        enumerate(string))).lower()

def capitalize(string):
    return ''.join(map(capfirst, string.split('-')))

def _(string):
    t = ugettext_lazy(string)
    t.message = string
    return t

def get_string(obj):
    return obj if isinstance(obj, str) else obj.message

def get_model_names(model):
    return (
        get_string(model._meta.verbose_name),
        get_string(model._meta.verbose_name_plural))

def verbose_choice(obj, f):
    return dict(obj._meta.get_field(f).choices).get(getattr(obj, f))

def verbose_choices(*args):
    return map(lambda a: (a.message, a), args)

def verbose_attr(obj, field):
    return (obj._meta.get_field(field).verbose_name, getattr(obj, field))
