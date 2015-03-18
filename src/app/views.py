from django.shortcuts import redirect
from era import view


@view
def index(request, theme='spacelab'):
    return {'theme': theme}
