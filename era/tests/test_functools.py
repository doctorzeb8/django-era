from ..utils.functools import unidec, pluck, separate, pick, omit, truthful, avg
from .base import SimpleTestCase, IsOkTestCase


class UnidecTestCase(IsOkTestCase):
    def test_default_behaviour(self):
        self.assertOk(
            unidec(lambda fn, a: fn(a) + 'k') \
            (lambda a: a[1:])('oo'))

    def test_with_params(self):
        self.assertOk(
            unidec(lambda fn, a, **f: f['w'] + fn(a))(w='o') \
            (lambda a: a[1:])('kk'))


class AvgTestCase(SimpleTestCase):
    def test(self):
        self.assertEqual(avg(4, 6, 8), 6)


class SeparateTestCase(SimpleTestCase):
    def test(self):
        [even, odd] = separate(lambda x: bool(x % 2), [1, 2, 3, 4, 5])
        self.assertEqual(even, [2, 4])
        self.assertEqual(odd, [1, 3, 5])


class DictCopyTestCase(SimpleTestCase):
    def test_pick(self):
        self.assertEqual(
            pick({0: 1, 2: 4}, 0), {0: 1})

    def test_omit(self):
        self.assertEqual(
            omit({0: 1, 2: 4}, 0), {2: 4})

    def test_truthful(self):
        self.assertEqual(
            truthful({1: True, 2: False, 3: 'yes', 4: []}), {1: True, 3: 'yes'})


class PluckTestCase(SimpleTestCase):
    def test_dict(self):
        self.assertEqual(
            pluck([{0: 0}, {0: 1, 1: 1}, {0: 2, 1: 1, 2: 2}], 0),
            [0, 1, 2])

    def test_obj(self):
        class O:
            def __init__(self, x):
                self.x = x

        self.assertEqual(
            pluck([O(1), O(2), O(3)], 'x'),
            [1, 2, 3])
