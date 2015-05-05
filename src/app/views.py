from django.shortcuts import redirect
from era.views import TemplateView


class Index(TemplateView):
    def get(self, request, theme='spacelab'):
        return self.render_to_response({'theme': theme})
