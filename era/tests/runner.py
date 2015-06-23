from django.test.runner import DiscoverRunner


class NoDbDiscoverRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        pass

    def teardown_databases(self, *args, **kwargs):
        pass
