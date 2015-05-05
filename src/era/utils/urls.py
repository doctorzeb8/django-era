from itertools import chain
from django.conf.urls import url, patterns
from django.utils.module_loading import import_string
from .translation import capitalize


def view_url(route, args=None, suffix=True):
    def form_url(package):
        view = import_string(
            '.'.join([
                package,
                'views',
                ''.join([
                    capitalize(route),
                    suffix and 'View' or ''])]))
        return url(
            r'^{0}/?$'.format('/'.join(chain([route], args or []))),
            view.as_view(),
            name=route)
    return form_url


def package_patterns(package, *urls):
    if all([isinstance(x, str) for x in urls]):
        urls = map(view_url, urls)
    return patterns('', *list(map(lambda fn: fn(package), urls)))
