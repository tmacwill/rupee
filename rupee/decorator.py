import functools
import hashlib
import pickle
import rupee.event

def _key(prefix, args=None, kwargs=None):
    args = args or []
    kwargs = kwargs or {}
    return '%s:%s' % (prefix, hashlib.sha1(pickle.dumps((args, kwargs))).hexdigest())

def _path(f):
    return '%s.%s' % (f.__module__, f.__name__)

def _dirty(cache, prefix, *args, **kwargs):
    args = args or []
    kwargs = kwargs or {}
    cache.delete(_key(prefix, args, kwargs))
    rupee.event.publish(prefix, *args, **kwargs)

def _dirty_multi(cache, prefix, items):
    if not isinstance(items, list):
        items = [items]

    cache.delete_multi([_key(prefix, item) for item in items])
    rupee.event.publish(prefix, items)

def cached(cache, ttl=3600, key=None):
    def wrap(f):
        nonlocal ttl
        nonlocal key
        if key is None:
            key = _path(f)

        def inner(*args, **kwargs):
            cache_key = _key(key, args, kwargs)
            result = cache.get(cache_key)
            if result:
                return result

            result = f(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        inner._ttl = ttl
        inner._key = key
        inner.dirty = functools.partial(_dirty, cache, key)
        return inner
    return wrap

def on_dirty(fn):
    def wrap(f):
        assert hasattr(fn, '_key')
        rupee.event.add_subscriber(fn._key, f)
        return f
    return wrap

def multi_cached(cache, ttl=3600, key=None):
    def wrap(f):
        nonlocal ttl
        nonlocal key
        if key is None:
            key = _path(f)

        def inner(items):
            one = False
            if not isinstance(items, list):
                items = [items]
                one = True

            # perform a bulk get on all of the given keys
            items = list(items)
            bulk_keys = [_key(key, item) for item in items]
            cached_result = cache.get_multi(bulk_keys)

            # determine which items are missing from the bulk cache get
            missed_items = []
            for i, item in enumerate(items):
                if cached_result.get(bulk_keys[i], None) is None:
                    missed_items.append(item)

            # if there are no missing items, then we're done
            if len(missed_items) == 0:
                result = {items[i]: cached_result[bulk_keys[i]] for i, _ in enumerate(items)}
                if one:
                    if len(result.values()) == 0:
                        return None
                    return list(result.values())[0]
                return result

            # pull all of the missing items from ground truth
            pull_result = f(missed_items)
            assert isinstance(pull_result, dict)
            cache.set_multi({_key(key, k): v for k, v in pull_result.items()}, ttl=ttl)

            # merge together cached and uncached results
            result = {}
            for i, item in enumerate(items):
                if cached_result.get(bulk_keys[i], None) is not None:
                    result[item] = cached_result[bulk_keys[i]]
                elif item in pull_result.keys():
                    result[item] = pull_result[item]

            if one:
                if len(result.values()) == 0:
                    return None
                return list(result.values())[0]

            return result

        inner._ttl = ttl
        inner._key = key
        inner.dirty = functools.partial(_dirty_multi, cache, key)
        return inner
    return wrap
