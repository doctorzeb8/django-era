from importlib import import_module
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.utils.module_loading import import_string


try:
    from app.urls import urlpatterns as index
    urlpatterns = index
except ImportError:
    urlpatterns = patterns('', url(
        r'^$',
        import_string(settings.INDEX_VIEW).as_view(),
        name='index'))

def test_fitness(app):
    try:
        if not app in ['app', __package__]:
            import_module(app + '.urls')
            return True
    except ImportError:
        pass
    return False

urlpatterns += patterns('', *list(map(
    lambda app: url(r'', include(app + '.urls')),
    filter(test_fitness, settings.MODULES))))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
