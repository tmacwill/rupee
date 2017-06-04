import pickle
import time

import rupee.decorator

def default_deserialize(o):
    if not o:
        return o

    return pickle.loads(o)

def default_serialize(o):
    return pickle.dumps(o)

class _Engine:
    def __init__(self, prefix='', serialize=None, deserialize=None):
        self.prefix = prefix
        self.serialize = serialize or default_serialize
        self.deserialize = deserialize or default_deserialize

    def _key(self, key):
        return '%s:%s' % (self.prefix, key)

    def cached(self, ttl=3600, key=None):
        return rupee.decorator.cached(self, ttl=ttl, key=key)

    def delete(self, key):
        raise NotImplementedError()

    def delete_all_data(self):
        raise NotImplementedError()

    def delete_multi(self, keys):
        raise NotImplementedError()

    def get(self, key):
        raise NotImplementedError()

    def get_multi(self, keys):
        raise NotImplementedError()

    def set(self, key, value, ttl=None):
        raise NotImplementedError()

    def set_multi(self, value_map, ttl=None):
        raise NotImplementedError()

class Memcached(_Engine):
    def __init__(self, servers, prefix, serialize=None, deserialize=None):
        super().__init__(prefix, serialize, deserialize)

        import pylibmc
        self.store = pylibmc.Client(servers, binary=True)

    def delete(self, key):
        self.store.delete(self._key(key))

    def delete_all_data(self):
        self.store.flush_all()

    def delete_multi(self, keys):
        self.store.delete_multi([self._key(key) for key in keys])

    def get(self, key):
        return self.deserialize(self.store.get(self._key(key)))

    def get_multi(self, keys):
        data = self.store.get_multi([self._key(k) for k in keys])
        result = {}
        for key in keys:
            result[key] = None
            if self._key(key) in data:
                result[key] = self.deserialize(data[self._key(key)])

        return result

    def set(self, key, value, ttl=0):
        self.store.set(self._key(key), self.serialize(value), time=ttl)

    def set_multi(self, value_map, ttl=0):
        self.store.set_multi({self._key(k): self.serialize(v) for k, v in value_map.items()}, time=ttl)

class Memory(_Engine):
    def __init__(self, serialize=None, deserialize=None):
        super().__init__('', serialize, deserialize)
        self._data = {}

    def delete_all_data(self):
        self._data = {}

    def delete(self, key):
        self._data.pop(key, None)

    def delete_multi(self, keys):
        for key in keys:
            self._data.pop(key, None)

    def get(self, key):
        value, ttl = self._data.get(key, (None, None))
        if ttl and time.time() > ttl:
            self.delete(key)
            return None

        return value

    def get_multi(self, keys):
        return {key: self.get(key) for key in keys}

    def set(self, key, value, ttl=None):
        self._data[key] = (value, time.time() + ttl) if ttl else (value, None)

    def set_multi(self, value_map, ttl=None):
        for k, v in value_map.items():
            self.set(k, v, ttl)

class Redis(_Engine):
    def __init__(self, server='localhost:6379', db=0, prefix='', serialize=None, deserialize=None):
        super().__init__(prefix, serialize, deserialize)

        import redis
        server_parts = server.split(':')
        self.store = redis.StrictRedis(
            db=db,
            host=server_parts[0],
            port=server_parts[1]
        )

    def delete(self, key):
        self.store.delete(self._key(key))

    def delete_all_data(self):
        self.store.flushdb()

    def delete_multi(self, keys):
        pipe = self.store.pipeline()
        for key in keys:
            pipe.delete(self._key(key))

        pipe.execute()

    def get(self, key):
        data = self.store.get(self._key(key))
        if data is None:
            return data

        return self.deserialize(data)

    def get_multi(self, keys):
        pipe = self.store.pipeline()
        for key in keys:
            pipe.get(self._key(key))

        return {k: self.deserialize(v) if v is not None else None for k, v in zip(keys, pipe.execute())}

    def set(self, key, value, ttl=None):
        k = self._key(key)
        self.store.set(k, self.serialize(value))

        if ttl is not None:
            self.store.expire(k, ttl)

    def set_multi(self, value_map, ttl=None):
        pipe = self.store.pipeline()
        for key, value in value_map.items():
            k = self._key(key)
            pipe.set(k, self.serialize(value))

            if ttl is not None:
                pipe.expire(k, ttl)

        return pipe.execute()
