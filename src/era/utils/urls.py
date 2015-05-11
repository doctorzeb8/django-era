from itertools import chain
from django.conf.urls import url, patterns
from django.utils.module_loading import import_string
from .translation import capitalize


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
            r'^{0}/?$'.format('/'.join(chain([route], args or []))),
            view.as_view(),
            name=(url_name or route))
    return form_url


def crud_urls(route, object_name):
    return [
        view_url(
            route,
            args=['add'],
            url_name='-'.join([object_name, 'add']),
            view_name=object_name),
        view_url(route),
        view_url(
            route,
            args=[r'(?P<pk>[0-9]+)'],
            url_name='-'.join([object_name, 'update']),
            view_name=object_name),
        view_url(
            route,
            args=['delete'],
            url_name='-'.join([route, 'delete']))]


def package_patterns(package, *urls):
    if all([isinstance(x, str) for x in urls]):
        urls = map(view_url, urls)
    return patterns('', *list(map(lambda fn: fn(package), urls)))
