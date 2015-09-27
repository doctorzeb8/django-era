from functools import reduce, wraps
from itertools import chain, tee
from random import choice
from string import digits
from django.utils.functional import curry


def just(*x, **kw):
    return len(x) and x[0] or kw

def call(fn):
    return fn()

def swap(a, fn):
    return fn(a)

def unpack_args(fn):
    return lambda t: fn(*t)

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
            TypeError('wrapper get *args'))))


def pluck(l, k):
    return list(map(
        lambda o: o.get(k) if isinstance(o, dict) \
        else reduce(lambda x, y: getattr(x, y, None), k.split('.'), o), l))

def first(seq):
    return list(seq)[0]

def select(i, l):
    return l[i - len(l) * int(i / len(l))]

def factual(l):
    return list(filter(bool, l))

def separate(fn, lx):
    return map(list, map(
        unpack_args(
            lambda i, ly: filter(
                lambda el: bool(i) == fn(el),
                ly)),
        enumerate(tee(lx, 2))))


def case(k, *dl, **kw):
    return dict(len(dl) and dl[0] or {}, **kw).get(k)

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
    return bool(v)

def filter_dict(fn, d):
    return dict_copy(fn)(d)

def reduce_dict(fn, d):
    return map(unpack_args(fn), d.items())

@unidec
def dict_map(fnx, fny, d):
    return dict(reduce_dict(lambda k, v: fnx(k, v, fny), d))

@dict_map
def map_keys(k, v, fn):
    return (fn(k), v)

@dict_map
def map_values(k, v, fn):
    return (k, fn(v))


def avg(*args):
    return reduce(lambda x, y: x + y, args) / len(args)

def random_str(length=6, source=digits):
    return ''.join(map(lambda i: choice(source), range(0, length)))
