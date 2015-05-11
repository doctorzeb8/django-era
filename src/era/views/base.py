import re
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic.base import TemplateResponseMixin, View
from ..utils.translation import normalize


class BaseViewMixin:
    @property
    def about(self):
        return re.sub(r'-view$', '', normalize(self.__class__.__name__))

    def send_message(self, level, content):
        content and getattr(messages, level)(self.request, content)

    def navigate(self, name):
        return redirect(reverse(name))


class BaseView(BaseViewMixin, TemplateResponseMixin, View):
    components = {}
    page_title = settings.TITLE

    def get(self, request, *args, **kwargs):
        return getattr(super(),  'get', lambda r: None)(request) \
            or self.render_to_response(self.get_context_data())

    def get_page_title(self):
        return self.page_title

    def get_components(self):
        return {}

    def get_context_data(self, **kw):
        return dict(
            getattr(super(), 'get_context_data', lambda **x: x)(**kw),
            page_title=self.get_page_title(),
            components=dict(self.components, **self.get_components()))

    def get_template_names(self):
        return list(map(lambda x: x + '.html', [self.about, 'index']))
