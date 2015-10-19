from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.utils.module_loading import import_string

from .utils.translation import _
from .utils.urls import exists_import, http_error


try:
    from app.urls import urlpatterns as index
    urlpatterns = index
except ImportError:
    urlpatterns = patterns('')

if not 'index' in [x.name for x in urlpatterns]:
    urlpatterns += patterns('', url(
        r'^$',
        import_string(settings.INDEX_VIEW).as_view(),
        name='index'))

urlpatterns += patterns('', *list(map(
    lambda app: url(r'', include(app + '.urls')),
    filter(
        lambda app: not app in ['app', __package__] \
            and exists_import('.'.join([app, 'urls'])),
        settings.MODULES))))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler403 = http_error(403, _('None available'))
handler404 = http_error(404, _('Page not found'))
handler500 = http_error(500, _('Server error'))
