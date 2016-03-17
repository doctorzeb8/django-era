from itertools import chain
import re

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import resolve, reverse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateResponseMixin, View
from ..utils.translation import normalize
from ..utils.urls import dispatch_decorator


class BaseViewMixin:
    keywords = []

    @property
    def about(self):
        return ' '.join(chain(
            self.keywords,
            [re.sub(r'-view$', '', normalize(self.__class__.__name__))]))

    @property
    def url_match(self):
        return resolve(self.request.path)

    def send_message(self, level, content):
        content and getattr(messages, level)(self.request, content)

    def navigate(self, name):
        return redirect(reverse(name))

    def reload(self):
        return redirect(self.request.get_full_path())


class BaseView(BaseViewMixin, TemplateResponseMixin, View):
    decorators = []
    components = {}
    page_title = settings.TITLE

    @dispatch_decorator
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_decorators(self):
        return self.decorators

    def get(self, request, *args, **kwargs):
        return getattr(super(),  'get', lambda r: None)(request) \
            or self.render_to_response(self.get_context_data())

    def get_page_title(self, **kw):
        return self.page_title

    def get_media(self, **kw):
        return ''

    def get_components(self, **kw):
        return {}

    def get_context_data(self, **kw):
        return dict(
            getattr(super(), 'get_context_data', lambda **x: x)(**kw),
            codename=settings.CODENAME,
            page_title=self.get_page_title(**kw),
            media=self.get_media(**kw),
            components=dict(self.components, **self.get_components(**kw)))

    def get_template_names(self):
        return list(map(lambda x: x + '.html', [self.about, 'index']))


class DisplayAttrMixin:
    def display_attr(self, obj, attr, **kw):
        method = 'get_{0}_display'.format(attr)
        if isinstance(obj, self.model) and hasattr(self, method):
            return getattr(self, method)(obj)
        elif kw.get('model', True) and hasattr(obj, method):
            return getattr(obj, method)()
        elif kw.get('direct', True):
            return getattr(obj, attr)
        raise AttributeError('Missing display data for "{0}"'.format(attr))
