import rupee
import rupee.engine
import unittest
import unittest.mock

redis_cache = rupee.engine.Redis()

def foo():
    return 5

def on_dirty_cached_foo_inner(one, two):
    return 5

def bar(items):
    return {item: item for item in items}

def _bar(items):
    return {item: item for item in items}

def on_dirty_multi_cached_bar_inner(items):
    return 5

@rupee.cached(redis_cache)
def cached_foo(one, two):
    return foo()

@redis_cache.cached()
def cached_foo_method(one, two):
    return foo()

@rupee.multi_cached(redis_cache)
def multi_cached_bar(items):
    return bar(items)

@rupee.on_dirty(cached_foo)
def on_dirty_cached_foo(one, two):
    return on_dirty_cached_foo_inner(one, two)

@rupee.on_dirty(multi_cached_bar)
def on_dirty_multi_cached_bar(items):
    return on_dirty_multi_cached_bar_inner(items)

class TestDecorator(unittest.TestCase):
    def setUp(self):
        redis_cache.delete_all_data()

    def test_cached(self):
        return_value = foo()
        with unittest.mock.patch('rupee.tests.test_decorator.foo', return_value=return_value) as mock_foo:
            # first execution should run foo
            self.assertEqual(cached_foo(1, 2), return_value)
            mock_foo.assert_called_once_with()

            # second execution should use cached results
            self.assertEqual(cached_foo(1, 2), return_value)
            mock_foo.assert_called_once_with()

        with unittest.mock.patch('rupee.tests.test_decorator.foo', return_value=return_value) as mock_foo:
            # different args should run foo again
            self.assertEqual(cached_foo(2, 3), return_value)
            mock_foo.assert_called_once_with()

    def test_cached_method(self):
        return_value = foo()
        with unittest.mock.patch('rupee.tests.test_decorator.foo', return_value=return_value) as mock_foo:
            # first execution should run foo
            self.assertEqual(cached_foo_method(1, 2), return_value)
            mock_foo.assert_called_once_with()

            # second execution should use cached results
            self.assertEqual(cached_foo_method(1, 2), return_value)
            mock_foo.assert_called_once_with()

        with unittest.mock.patch('rupee.tests.test_decorator.foo', return_value=return_value) as mock_foo:
            # different args should run foo again
            self.assertEqual(cached_foo_method(2, 3), return_value)
            mock_foo.assert_called_once_with()

    def test_cached_dirty(self):
        return_value = foo()
        with unittest.mock.patch('rupee.tests.test_decorator.foo', return_value=return_value) as mock_foo:
            # first execution should run foo
            self.assertEqual(cached_foo(1, 2), return_value)
            mock_foo.assert_called_once_with()

            # second execution should use cached results
            self.assertEqual(cached_foo(1, 2), return_value)
            mock_foo.assert_called_once_with()

        with unittest.mock.patch('rupee.tests.test_decorator.foo', return_value=return_value) as mock_foo:
            # dirtying the cache means we should run foo again
            cached_foo.dirty(1, 2)
            self.assertEqual(cached_foo(1, 2), return_value)
            mock_foo.assert_called_once_with()

            # second execution should use cached results
            self.assertEqual(cached_foo(1, 2), return_value)
            mock_foo.assert_called_once_with()

    def test_cached_on_dirty(self):
        return_value = 5
        with unittest.mock.patch(
            'rupee.tests.test_decorator.on_dirty_cached_foo_inner',
            return_value=return_value
        ) as mock_foo:
            # dirtying a cached function should call its subscriber
            cached_foo.dirty(1, 2)
            mock_foo.assert_called_once_with(1, 2)

    def test_multi_cached(self):
        return_value = {1: 1, 2: 2}
        with unittest.mock.patch('rupee.tests.test_decorator.bar', side_effect=_bar) as mock_bar:
            # first execution should run bar
            self.assertEqual(multi_cached_bar([1, 2]), return_value)
            mock_bar.assert_called_once_with([1, 2])

            # second execution should use cached results
            self.assertEqual(multi_cached_bar([1, 2]), return_value)
            mock_bar.assert_called_once_with([1, 2])

        with unittest.mock.patch('rupee.tests.test_decorator.bar', side_effect=_bar) as mock_bar:
            # different args should run bar again
            self.assertEqual(multi_cached_bar([2, 3]), {2: 2, 3: 3})
            mock_bar.assert_called_once_with([3])

    def test_multi_cached_dirty(self):
        return_value = {1: 1, 2: 2}
        with unittest.mock.patch('rupee.tests.test_decorator.bar', side_effect=_bar) as mock_bar:
            # first execution should run bar
            self.assertEqual(multi_cached_bar([1, 2]), return_value)
            mock_bar.assert_called_once_with([1, 2])

            # second execution should use cached results
            self.assertEqual(multi_cached_bar([1, 2]), return_value)
            mock_bar.assert_called_once_with([1, 2])

        with unittest.mock.patch('rupee.tests.test_decorator.bar', side_effect=_bar) as mock_bar:
            # dirtying the cache means we should run bar again
            multi_cached_bar.dirty([1, 2])
            self.assertEqual(multi_cached_bar([1, 2]), return_value)
            mock_bar.assert_called_once_with([1, 2])

            # second execution should use cached results
            self.assertEqual(multi_cached_bar([1, 2]), return_value)
            mock_bar.assert_called_once_with([1, 2])

        with unittest.mock.patch('rupee.tests.test_decorator.bar', side_effect=_bar) as mock_bar:
            # dirtying part of the cache should run part of bar again
            multi_cached_bar.dirty([1])
            self.assertEqual(multi_cached_bar([1, 2]), return_value)
            mock_bar.assert_called_once_with([1])

    def test_multi_cached_on_dirty(self):
        return_value = 5
        with unittest.mock.patch(
            'rupee.tests.test_decorator.on_dirty_multi_cached_bar_inner',
            return_value=return_value
        ) as mock_bar:
            # dirtying a cached function should call its subscriber
            multi_cached_bar.dirty([1, 2])
            mock_bar.assert_called_once_with([1, 2])
