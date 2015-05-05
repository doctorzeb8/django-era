from django.conf.urls import patterns, url
from .views import Index

urlpatterns = patterns(
    '',
    url(r'^(\S+)/?$', Index.as_view()),
    url(r'^/?$', Index.as_view()))
