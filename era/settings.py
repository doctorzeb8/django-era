import os
import sys
import django

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = []

SECRET_KEY = 'era'
TEST_RUNNER = 'era.tests.runner.NoDbDiscoverRunner'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(sys.modules.get('app').__file__)), '..')
CODENAME = os.path.basename(os.path.abspath(BASE_DIR))
INDEX_VIEW = 'app.views.IndexView'
MODULES = ['app']

USE_I18N = True
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locales'),
    os.path.join(os.path.dirname(django.__file__), 'contrib', 'admin', 'locale')
)

DATE_FORMAT = 'd.m.y'
TIME_FORMAT = 'H:M'
DATETIME_FORMAT = 'd.m.y H:M'
DATE_INPUT_FORMATS = ['%d.%m.%y']
DATETIME_INPUT_FORMATS = ['%d.%m.%y %H:%M']

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/uploads/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': CODENAME,
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangobower',
    'era'
]

BOWER_COMPONENTS_ROOT = BASE_DIR
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
