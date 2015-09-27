import re
import sys
from django.utils.text import capfirst
from django.utils.translation import get_language, ugettext_lazy
from ..functools import factual


def _(string, context=None):
    t = ugettext_lazy(': '.join(factual([context, string])))
    t.string = string
    return t


def get_string(obj):
    return obj if isinstance(obj, str) else obj.string


def normalize(string):
    return ''.join(map(
        lambda e: e[0] and re.sub(r'([A-Z])', r'-\g<1>', e[1]) or e[1],
        enumerate(string))).lower()


def capitalize(string):
    return ''.join(map(capfirst, string.split('-')))


def inflect(string):
    inflector = sys.modules.get('.'.join([__package__ or __name__, get_language()]))
    return inflector and inflector.inflect(string) or string
