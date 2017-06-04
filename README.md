# Rupee: Python ~~Cashing~~ Caching

Rupee is a simple, but fully-featured caching library for Python 3.

## Engines

Rupee supports caching using process memory, Redis, and Memcached.

For Redis support:

    pip install redis

For Memcached support, you can use `pylibmc`:

    pip install pylibmc

or `python-memcache`:

    pip install python-memcache

## Cache Access

You can create cache instances like this:

    memory = rupee.engine.Memory()
    memcached = rupee.engine.Memcached(['localhost:11211'])
    redis = rupee.engine.Redis('localhost:6379')

All instances conform to the same API, which offer the get/set/delete operations you'd expect:

    cache = rupee.engine.Memcached(['localhost:11211'])
    cache.set('foo', 'bar', ttl=3600)
    cache.set_multi({'baz': 1, 'qux': 2})
    cache.get('baz') == 1
    cache.get_multi(['foo', 'qux']) == {'foo': 'bar', 'qux': 2}
    cache.delete('qux')
    cache.delete_all(['foo', 'baz'])
    cache.delete_all_data()

## Cached Decorators

You can decorate functions to be cache their results:

    cache = rupee.engine.Redis('localhost:6379')

    @rupee.cached(cache, ttl=3600)
    def foo(bar, baz):
        return _some_expensive_thing(bar, baz)

To clear the cache entry for a function call:

    foo.dirty(1, 2)

For functions that perform bulk operations, you can use the multi-cache decorator:

    @rupee.multi_cached(cache):
    def get(items):
        return {item: _some_expensive_thing(item) for item in items}

Functions decorated with `multi_cached` must take a single list as an argument and return a dictionary keyed on the items in that list. Then, results for each item will be cached separately, and only the needed items will be passed to the function. To illustrate:

    get([1, 2, 3]) # calls _some_expensive_thing on 1, 2, and 3
    get([1, 2, 3]) # _some_expensive_thing is never called
    get([2, 3, 4]) # calls _some_expensive_thing only on 4
