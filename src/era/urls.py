from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.utils.module_loading import import_string


urlpatterns = patterns(
    '',
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)))

try:
    from app.urls import urlpatterns as index
    urlpatterns += index
except ImportError:
    urlpatterns += patterns('', url(
        r'^$',
        import_string(settings.INDEX_VIEW).as_view(),
        name='index'))

urlpatterns += patterns('', *list(map(
    lambda app: url(r'', include(app + '.urls')),
    filter(
        lambda app: not app in ['app', __package__],
        settings.MODULES))))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
