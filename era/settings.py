import os
import sys
import django

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangobower',
    'era'
]

BOWER_INSTALLED_APPS = [
    'moment',
    'jquery#2',
    'underscore',
    'bootstrap',
    'seiyria-bootstrap-slider',
    'eonasdan-bootstrap-datetimepicker',
    'fontawesome',
    'jquery-query-object'
]

MODULES = [
    'app'
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader'
]

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages'
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder'
]

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
ROOT_URLCONF = 'era.urls'
WSGI_APPLICATION = 'app.wsgi.application'

INDEX_VIEW = 'app.views.IndexView'
USE_I18N = True

#DATE_FORMAT = 'd.m.Y'
#DATETIME_FORMAT = 'd.m.Y H:M'
DATE_INPUT_FORMAT = 'DD.MM.YY'
DATETIME_INPUT_FORMAT = 'DD.MM.YY HH:mm'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
TEST_RUNNER = 'era.tests.runner.NoDbDiscoverRunner'
SECRET_KEY = 'era'

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(sys.modules.get('app').__file__)), '..')
BOWER_COMPONENTS_ROOT = BASE_DIR
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/uploads/'
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locales'),
    os.path.join(os.path.dirname(django.__file__), 'contrib', 'admin', 'locale')
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.path.basename(os.path.abspath(BASE_DIR)),
    }
}
