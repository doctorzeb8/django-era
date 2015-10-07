from .functools import unidec


@unidec
def o_O(fn, *args, **kw):
    import ipdb
    locals().update(fn.__globals__)
    closure = [x.cell_contents for x in fn.__closure__ or []]
    ipdb.set_trace()
    return fn(*args, **kw)


__builtins__['o_O'] = o_O
