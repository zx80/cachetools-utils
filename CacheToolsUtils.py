"""
CacheTools Utilities

This code is public domain.
"""

from typing import Optional, Callable, Dict, List, Set, Any, Union, MutableMapping

import cachetools
import json


class MutMapMix:
    """Convenient MutableMapping Mixin, forward to _cache."""

    def __getitem__(self, key):
        return self._cache.__getitem__(key)

    def __setitem__(self, key, val):
        return self._cache.__setitem__(key, val)

    def __delitem__(self, key):
        return self._cache.__delitem__(key)

    def __len__(self):
        return self._cache.__len__()

    def __iter__(self):
        return self._cache.__iter__()


class KeyMutMapMix(MutMapMix):
    """Convenient MutableMapping Mixin with a key filter, forward to _cache."""

    def _key(self, key):
        return key

    def __getitem__(self, key):
        return self._cache.__getitem__(self._key(key))

    def __setitem__(self, key, val):
        return self._cache.__setitem__(self._key(key), val)

    def __delitem__(self, key):
        return self._cache.__delitem__(self._key(key))


class StatsCache(MutMapMix, MutableMapping):
    """Cache class to keep stats."""

    def __init__(self, cache: MutableMapping):
        self._reads, self._writes, self._dels, self._hits = 0, 0, 0, 0
        self._cache = cache

    def hits(self):
        return float(self._hits) / float(max(self._reads, 1))

    def __getitem__(self, key):
        # log.debug(f"get: {key} {key in self._cache}")
        self._reads += 1
        res = self._cache.__getitem__(key)
        self._hits += 1
        return res

    def __setitem__(self, key, val):
        self._writes += 1
        return self._cache.__setitem__(key, val)

    def __delitem__(self, key):
        self._dels += 1
        return self._cache.__delitem__(key)

    def clear(self):
        return self._cache.clear()


class PrefixedCache(KeyMutMapMix, MutableMapping):
    """Cache class to add a key prefix."""

    def __init__(self, cache: MutableMapping, prefix: Union[str, bytes] = ''):
        self._prefix = prefix
        self._cache = cache

    def _key(self, key):
        return self._prefix + str(key)


class JsonSerde:
    """JSON serialize/deserialize for MemCached."""

    def serialize(self, key, value):
        if isinstance(value, str):
            return value.encode('utf-8'), 1
        return json.dumps(value).encode('utf-8'), 2

    def deserialize(self, key, value, flags):
        if flags == 1:
            return value.decode('utf-8')
        if flags == 2:
            return json.loads(value.decode('utf-8'))
        raise Exception("Unknown serialization format")


class PrefixedMemCached(PrefixedCache):
    """MemCached-compatible wrapper class for cachetools with a key prefix."""

    def __init__(self, cache, prefix: str = ''):
        super().__init__(prefix=bytes(prefix, 'utf-8'), cache=cache)
        # should check that cache is really a pymemcache client?

    # memcached needs short (250 bytes) ASCII without control chars nor spaces
    def _key(self, key):
        import base64
        return self._prefix + base64.b64encode(str(key).encode('utf-8'))

    def __len__(self):
        return self._cache.stats()[b'curr_items']


class StatsMemCached(MutMapMix, MutableMapping):
    """Cache MemCached-compatible class with key prefix."""

    def __init__(self, cache):
        self._cache = cache

    def hits(self):
        """Return overall cache hit rate."""
        stats = self._cache.stats()
        return float(stats[b"get_hits"]) / max(stats[b"cmd_get"], 1)

    def __len__(self):
        return self._cache.stats()[b'curr_items']

    def clear(self):
        return self._cache.flush_all()


class PrefixedRedisCache(PrefixedCache):
    """Prefixed Redis wrapper class for cachetools."""

    def __init__(self, cache, prefix: str = ''):
        super().__init__(cache, prefix)

    def _key(self, key):
        return self._prefix + json.dumps(key)


class StatsRedisCache(MutableMapping):
    """TTL-ed Redis wrapper class for cachetools."""

    def __init__(self, cache, ttl=600):
        self._ttl = ttl
        # must be redis.Redis
        # NOTE we do not want to import redis at this point
        assert cache.__class__.__name__ == "Redis"
        self._cache = cache

    def hits(self):
        stats = self._cache.info(section="stats")
        return float(stats["keyspace_hits"]) / (stats["keyspace_hits"] + stats["keyspace_misses"])

    def _serialize(self, s):
        return json.dumps(s)

    def _deserialize(self, s):
        return json.loads(s)

    def __getitem__(self, index):
        val = self._cache.get(index)
        if val:
            return self._deserialize(val)
        else:
            raise KeyError()

    def __setitem__(self, index, value):
        return self._cache.set(index, self._serialize(value), ex=self._ttl)

    def __delitem__(self, index):
        return self._cache.delete(index)

    def __len__(self):
        return self._cache.dbsize()

    def __iter__(self):
        raise Exception("not implemented yet")

    def clear(self):
        return self._cache.flushdb()
