from django.shortcuts import redirect
from era.views import BaseView


class Index(BaseView):
    def get(self, request, theme='spacelab'):
        return self.render_to_response({'theme': theme})
