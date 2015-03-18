from functools import reduce, wraps
from random import choice
from string import digits
from django.utils.functional import curry


def avg(*args):
    return reduce(lambda x, y: x + y, args) / len(args)

def random_str(length=6, source=digits):
    return ''.join(map(lambda i: choice(source), range(0, length)))

def throw(exception):
    raise exception

def unidec(fnx):
    '''
    @unidec
    def render(view, request, flag=True):
        pass

    @render
    def first_view(request):
        pass

    @render(flag=False)
    def second_view(request):
        pass
    '''

    return lambda *ax, **kx: (
        wraps(ax[0])(lambda *ay, **ky: fnx(ax[0], *ay, **ky)) \
        if len(ax) == 1 and not kx and callable(ax[0]) else \
        lambda fny: wraps(fny)(lambda *ay, **ky: \
        fnx(fny, *ay, **dict(kx, **ky)) if not ax else throw(
            DeprecationWarning('wrapper get *args'))))

@unidec
def dict_copy(fn, d, *a):
    return {k: v for k, v in d.items() if fn(k, v, *a)}

@dict_copy
def pick(k, v, *a):
    return k in a

@dict_copy
def omit(k, v, *a):
    return not k in a

@dict_copy
def truthful(k, v, *a):
    return v is True

def pluck(l, k):
    return map(lambda o: o.get(k) if isinstance(o, dict) else getattr(o, k), l)

def first(f, l):
    return list(filter(f, l))[0]
