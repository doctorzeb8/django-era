from era import package_patterns, admin_urls, view_url
from django.contrib.auth import get_user_model


urlpatterns = package_patterns(
    __package__,
    'login',
    'logout',
    'profile',
    'registration',
    'reset',
    'confirm',
    'unlock')

urlpatterns += package_patterns(
    __package__, *admin_urls(get_user_model()))
