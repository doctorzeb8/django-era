from ..functools import case


def get_model_names(model):
    return [model._meta.verbose_name, model._meta.verbose_name_plural]

def verbose_choices(*args):
    return map(lambda a: (a.string, a), args)

def verbose_choice(obj, f):
    return case(
        getattr(obj, f),
        dict(obj._meta.get_field(f).choices))

def verbose_attr(obj, field):
    return (obj._meta.get_field(field).verbose_name, getattr(obj, field))
