from importlib import import_module
from itertools import chain
from functools import reduce

from django.conf.urls import url, patterns
from django.shortcuts import render
from django.utils.module_loading import import_string

from .functools import unidec
from .translation import capitalize, get_string, get_model_names


def get_site_url(request):
    return 'http{0}://{1}'.format(
        's' if request.is_secure() else '',
        request.get_host())


def exists_import(target):
    try:
        return import_module(target)
    except ImportError as error:
        if error.name != target:
            raise error


def view_url(route, args=None, url_name=None, view_name=None, view_suffix='View'):
    def form_url(package):
        view = import_string(
            '.'.join([
                package,
                'views',
                ''.join([
                    capitalize(view_name or route),
                    view_suffix])]))
        return url(
            r'^{0}/?$'.format('/'.join(chain([route], args or [])).lstrip('/')),
            view.as_view(),
            name=(url_name or route))
    return form_url


def admin_urls(*models):
    def get_model_urls(model):
        (object_name, namespace) = map(get_string, get_model_names(model))
        return [
            view_url(
                namespace,
                args=['add'],
                url_name='-'.join([object_name, 'add']),
                view_name=object_name),
            view_url(
                namespace,
                view_name=namespace + (object_name == namespace and '-plural' or '')),
            view_url(
                namespace,
                args=[r'(?P<pk>[0-9]+)'],
                url_name='-'.join([object_name, 'edit']),
                view_name=object_name),
            view_url(
                namespace,
                args=['delete'],
                url_name='-'.join([namespace, 'delete']))]
    return chain(*map(get_model_urls, models))


def package_patterns(package, *urls):
    if all([isinstance(x, str) for x in urls]):
        urls = map(view_url, urls)
    return patterns('', *list(map(lambda fn: fn(package), urls)))


@unidec
def dispatch_decorator(fnx, view, request, *args, **kwargs):
    decorator = reduce(
        lambda seq, fny: fny(seq),
        reversed(list(chain(
            getattr(view, 'decorators', []),
            [lambda req, *a, **kw: fnx(view, req, *a, **kw)]))))
    return decorator(request, *args, **kwargs)


def http_error(code, title):
    return lambda req: render(
        req,
        'errors.html',
        {'code': code, 'page_title': title.lower()},
        status=code)
