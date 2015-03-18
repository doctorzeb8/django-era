from django.test import SimpleTestCase


class IsOkTestCase(SimpleTestCase):
    def assertOk(self, x):
        self.assertEqual(x, 'ok')
