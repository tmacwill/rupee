import warnings
import unittest

import rupee.engine

class _Base(object):
    cache = None

    data = {
        'int': 123,
        'string': 'foo',
        'list': [1, 2, 3],
        'dict': {'foo': 'bar', 'baz': 5}
    }

    def setUp(self):
        self.cache.delete_all_data()
        warnings.simplefilter('ignore', ResourceWarning)

    def test_single(self):
        for key, value in self.data.items():
            self.assertEqual(self.cache.get(key), None)
            self.cache.set(key, value)
            self.assertEqual(self.cache.get(key), value)
            self.cache.delete(key)
            self.assertEqual(self.cache.get(key), None)

    def test_multi(self):
        keys = self.data.keys()
        for key, value in self.data.items():
            self.cache.delete(key)

        self.cache.set_multi(self.data)
        self.assertEqual(self.cache.get_multi(keys), self.data)

        self.cache.delete_multi(keys)
        deleted = self.cache.get_multi(keys)
        for key, value in deleted.items():
            self.assertEqual(value, None)

class TestMemcached(_Base, unittest.TestCase):
    cache = rupee.engine.Memcached([('localhost:11211')], prefix='test')

class TestMemory(_Base, unittest.TestCase):
    cache = rupee.engine.Memory()

class TestRedis(_Base, unittest.TestCase):
    cache = rupee.engine.Redis(prefix='test')
