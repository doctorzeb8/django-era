from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader, Context, RequestContext
from .utils.functools import unidec


def render(*templates, **ctx):
    return loader.select_template(map(lambda t: t + '.html', templates)).render(
        'request' in ctx and RequestContext(ctx.pop('request'), ctx) or Context(ctx))


@unidec
def view(fn, request, *args, **kwargs):
    response = fn(request, *args)
    if isinstance(response, (HttpResponseRedirect, JsonResponse)):
        return response
    return HttpResponse(render(kwargs.pop('template', fn.__name__), 'index', **dict(
        response, **dict({'request': request}, **kwargs))))
