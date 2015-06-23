from itertools import chain
import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--fix', dest='fixtures', default='')

    def db_action(self, action):
        return ' '.join([action, settings.DATABASES['default']['NAME']])

    def manage_action(self, action, *args):
        return ' '.join(chain(['python manage.py', action], args))

    def handle(self, *args, **kw):
        subprocess.call(
            '; '.join([
                self.db_action('dropdb'),
                self.db_action('createdb'),
                self.manage_action('migrate'),
                self.manage_action('loaddata', *chain(
                    ['initial'], kw['fixtures'].split(',')))]),
            shell=True)
