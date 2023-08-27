"""
CacheTools Utilities. This code is public domain.
"""

from typing import Any, Callable, MutableMapping as MutMap

import cachetools
import json

from importlib.metadata import version as pkg_version
__version__ = pkg_version("CacheToolsUtils")

import logging
log = logging.getLogger(__name__)


#
# UTILS
#

_NO_DEFAULT = object()


class _MutMapMix:
    """Convenient MutableMapping Mixin, forward to _cache."""

    def __contains__(self, key):
        return self._cache.__contains__(key)

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


class _KeyMutMapMix(_MutMapMix):
    """Convenient MutableMapping Mixin with a key filter, forward to _cache."""

    def __contains__(self, key):
        return self._cache.__contains__(self._key(key))

    def __getitem__(self, key):
        return self._cache.__getitem__(self._key(key))

    def __setitem__(self, key, val):
        return self._cache.__setitem__(self._key(key), val)

    def __delitem__(self, key):
        return self._cache.__delitem__(self._key(key))


class _StatsMix:
    """Convenient Mixin to forward stats methods to _cache."""

    def hits(self):
        return self._cache.hits()

    def reset(self):
        return self._cache.reset()


#
# CACHETOOLS EXTENSIONS
#

class DictCache(_MutMapMix):
    """Cache class based on dict."""

    def __init__(self):
        self._cache = dict()


class LockedCache(_MutMapMix, _StatsMix, MutMap):
    """Cache class with a lock.

    :param cache: actual cache.
    :param lock: lock (context manager) to use

    The locked layer should be the last one before the actual cache.

    .. code-block: python

       import threading
       import cachetools as ct
       import CacheToolsUtils as ctu
       cache = ctu.LockedCache(ct.LFUCache(), threading.RLock())
    """

    def __init__(self, cache: MutMap, lock):
        self._cache = cache
        self._lock = lock

    def __contains__(self, key):
        with self._lock:
            return self._cache.__contains__(key)

    def __getitem__(self, key):
        with self._lock:
            return self._cache.__getitem__(key)

    def __setitem__(self, key, val):
        with self._lock:
            return self._cache.__setitem__(key, val)

    def __delitem__(self, key):
        with self._lock:
            return self._cache.__delitem__(key)


class PrefixedCache(_KeyMutMapMix, _StatsMix, MutMap):
    """Cache class to add a key prefix.

    :param cache: actual cache.
    :param prefix: prefix to prepend to keys.
    """

    def __init__(self, cache: MutMap, prefix: str|bytes = ""):
        self._prefix = prefix
        self._cache = cache

    def _key(self, key):
        return self._prefix + str(key)


class StatsCache(_MutMapMix, MutMap):
    """Cache class to keep stats.

    :param cache: actual cache.

    .. code-block: python

       import cachetools as ct
       import CacheToolsUtils as ctu
       cache = ctu.StatsCache(ct.LRUCache())
       ...

    Note that CacheTools ``cached`` decorator with ``info=True`` provides
    hits, misses, maxsize and currsize information.
    However, this only works for its own classes.
    """

    def __init__(self, cache: MutMap):
        self._cache = cache
        self.reset()

    def hits(self):
        """Return the cache hit ratio."""
        return float(self._hits) / float(max(self._reads, 1))

    def reset(self):
        """Reset internal stats data."""
        self._reads, self._writes, self._dels, self._hits = 0, 0, 0, 0

    def __getitem__(self, key):
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


class TwoLevelCache(_MutMapMix, MutMap):
    """Two-Level Cache class for CacheTools.

    :param cache: first (smaller, shorter TTL) cache
    :param cache2: second (larger, longer TTL) cache
    :param resilient: whether to ignore cache2 failures
    """

    def __init__(self, cache: MutMap, cache2: MutMap, resilient=False):
        self._resilient = resilient
        self._cache = cache
        self._cache2 = cache2

    def __getitem__(self, key):
        try:
            return self._cache.__getitem__(key)
        except KeyError:
            try:
                val = self._cache2.__getitem__(key)
            except Exception as e:
                log.error(e, exc_info=True)
                if not self._resilient:
                    raise
            self._cache.__setitem__(key, val)
            return val

    def __setitem__(self, key, val):
        try:
            self._cache2.__setitem__(key, val)
        except Exception as e:
            log.error(e, exc_info=True)
            if not self._resilient:
                raise
        return self._cache.__setitem__(key, val)

    def __delitem__(self, key):
        try:
            self._cache2.__delitem__(key)
        except KeyError:
            pass
        except Exception as e:
            log.error(e, exc_info=True)
            if not self._resilient:
                raise
        return self._cache.__delitem__(key)

    def clear(self):
        return self._cache.clear()


def cached(cache, *args, **kwargs):
    """Extended decorator with delete and exists.

    All parameters are forwarded to ``cachetools.cached``.

    :param cache: actual cache.

    If *f(\\*args, \\*\\*kwargs)* is the ``cached`` function, then:

    - ``f.cache_in(*args, **kwargs)`` tells whether the result is cached.
    - ``f.cache_del(*args, **kwargs)`` deletes (invalidates) the cached result.
    """

    def decorate(fun: Callable):

        # use cachetools
        fun = cachetools.cached(cache, *args, **kwargs)(fun)

        # extend
        def cache_in(*args, **kwargs):
            key = fun.cache_key(*args, **kwargs)
            return key in fun.cache

        def cache_del(*args, **kwargs):
            key = fun.cache_key(*args, **kwargs)
            key_in = key in fun.cache
            if key_in:
                del fun.cache[key]
            return key_in

        fun.cache_in = cache_in    # type: ignore
        fun.cache_del = cache_del  # type: ignore

        return fun

    return decorate


# short generator type name
MapGen = Callable[[MutMap, str], MutMap]


def cacheMethods(cache: MutMap, obj: Any, gen: MapGen = PrefixedCache, **funs):
    """Cache some object methods.

    :param cache: cache to use.
    :param obj: object instance to be cached.
    :param gen: generator of PrefixedCache.
    :param funs: name of methods and corresponding prefix

    .. code-block:: python

       cacheMethods(cache, item, PrefixedCache, compute1="c1.", compute2="c2.")
    """
    for fun, prefix in funs.items():
        assert hasattr(obj, fun), f"cannot cache missing method {fun} on {obj}"
        f = getattr(obj, fun)
        while hasattr(f, "__wrapped__"):
            f = f.__wrapped__
        setattr(obj, fun, cached(cache=gen(cache, prefix))(f))


def cacheFunctions(
    cache: MutMap, globs: MutMap[str, Any], gen: MapGen = PrefixedCache, **funs
):
    """Cache some global functions, with a prefix.

    :param cache: cache to use.
    :param globs: global object dictionary.
    :param gen: generator of PrefixedCache.
    :param funs: name of functions and corresponding prefix

    .. code-block:: python

       cacheFunctions(cache, globals(), PrefixedCache, fun1="f1.", fun2="f2.")
    """
    for fun, prefix in funs.items():
        assert fun in globs, "caching functions: {fun} not found"
        f = globs[fun]
        while hasattr(f, "__wrapped__"):
            f = f.__wrapped__
        globs[fun] = cached(cache=gen(cache, prefix))(f)


#
# MEMCACHED
#
class JsonSerde:
    """JSON serialize/deserialize class for MemCached (``pymemcached``).

    .. code-block:: python

       import pymemcached as pmc
       import CacheToolsUtils as ctu
       pmc_cache = pmc.Client(server="localhost", serde=ctu.JsonSerde())
    """

    # keep strings, else json
    def serialize(self, key, value):
        if isinstance(value, str):
            return value.encode("utf-8"), 1
        else:
            return json.dumps(value).encode("utf-8"), 2

    # reverse previous serialization
    def deserialize(self, key, value, flag):
        if flag == 1:
            return value.decode("utf-8")
        elif flag == 2:
            return json.loads(value.decode("utf-8"))
        else:
            raise Exception("Unknown serialization format")


class MemCached(_KeyMutMapMix, MutMap):
    """MemCached-compatible wrapper class for cachetools with key encoding.

    :param cache: actual memcached cache.

    .. code-block:: python

       import pymemcached as pmc
       import CacheToolsUtils as ctu
       cache = ctu.MemCached(pmc.Client(server="localhost", serde=ctu.JsonSerde()))

       @ctu.cached(cache=cache)
       def whatever(...):
    """

    def __init__(self, cache):
        self._cache = cache

    # memcached keys are constrained bytes, we need some encoding…
    # short (250 bytes) ASCII without control chars nor spaces
    # we do not use hashing which might be costly and induce collisions
    def _key(self, key):
        import base64

        return base64.b85encode(str(key).encode("utf-8"))

    def __len__(self):
        return self._cache.stats()[b"curr_items"]

    def stats(self):
        """Return MemCached stats."""
        return self._cache.stats()

    def clear(self):  # pragma: no cover
        """Flush MemCached contents."""
        return self._cache.flush_all()

    def hits(self):
        """Return overall cache hit ratio."""
        stats = self._cache.stats()
        return float(stats[b"get_hits"]) / max(stats[b"cmd_get"], 1)


class PrefixedMemCached(MemCached):
    """MemCached-compatible wrapper class for cachetools with a key prefix.

    :param cache: actual memcached cache.
    :param prefix: post key-encoding prepended prefix.

    .. code-block:: python

       import pymemcached as pmc
       import CacheToolsUtils as ctu
       # add a "app." prefix to keys, after serialization
       cache = ctu.PrefixedMemCached(pmc.Client(server="localhost", serde=ctu.JsonSerde()), "app.")
    """

    def __init__(self, cache, prefix: str = ""):
        super().__init__(cache=cache)
        self._prefix = bytes(prefix, "utf-8")

    def _key(self, key):
        import base64

        return self._prefix + base64.b85encode(str(key).encode("utf-8"))


class StatsMemCached(MemCached):
    """Cache MemCached-compatible class with stats.

    This class is empty and only kept for compatibility.
    """

    pass


#
# REDIS
#


class RedisCache(MutMap):
    """Redis TTL-ed wrapper for cachetools (``redis``).

    :param cache: actual redis cache.
    :param ttl: time-to-live in seconds, used as default expiration (``ex``).

    Keys and values are serialized in *JSON*.

    .. code-block:: python

       import redis
       import CacheToolsUtils as ctu
       # redis with 1 hour expiration
       cache = ctu.RedisCache(redis.Redis(host="localhost"), 3600)
    """

    def __init__(self, cache, ttl=600):
        self._cache = cache
        self._ttl = ttl

    def clear(self):  # pragma: no cover
        """Flush Redis contents."""
        return self._cache.flushdb()

    def _serialize(self, s):
        return json.dumps(s)

    def _deserialize(self, s):
        return json.loads(s)

    def _key(self, key):
        return json.dumps(key)

    def __getitem__(self, index):
        val = self._cache.get(self._key(index))
        if val:
            return self._deserialize(val)
        else:
            raise KeyError()

    def __setitem__(self, index, value):
        return self._cache.set(self._key(index), self._serialize(value), ex=self._ttl)

    def __delitem__(self, index):
        return self._cache.delete(self._key(index))

    def __len__(self):
        return self._cache.dbsize()

    def __iter__(self):
        raise Exception("not implemented yet")

    def info(self, *args, **kwargs):
        """Return redis informations."""
        return self._cache.info(*args, **kwargs)

    def dbsize(self, *args, **kwargs):
        """Return redis database size."""
        return self._cache.dbsize(*args, **kwargs)

    # also forward Redis set/get/delete
    def set(self, index, value, **kwargs):
        """Set cache contents."""
        if "ex" not in kwargs:  # pragma: no cover
            kwargs["ex"] = self._ttl
        return self._cache.set(self._key(index), self._serialize(value), **kwargs)

    def get(self, index, default=None):
        """Get cache contents."""
        return self[index]

    def delete(self, index):
        """Delete cache contents."""
        del self[index]

    # stats
    def hits(self):
        """Return cache hits."""
        stats = self.info(section="stats")
        return float(stats["keyspace_hits"]) / (
            stats["keyspace_hits"] + stats["keyspace_misses"]
        )


class PrefixedRedisCache(RedisCache):
    """Prefixed Redis wrapper class for cachetools.

    :param cache: actual redis cache.
    :param prefix: post key encoding prefix.
    :param ttl: time-to-live in seconds, used as default expiration (``ex``).

    .. code-block:: python

       import redis
       import CacheToolsUtils as ctu
       # redis with "app." prefix and 1 hour expiration
       cache = ctu.PrefixedRedisCache(redis.Redis(host="localhost"), "app.", 3600)
    """

    def __init__(self, cache, prefix: str = "", ttl=600):
        super().__init__(cache, ttl)
        self._prefix = prefix

    def _key(self, key):
        # or self._cache._key(prefix + key)?
        return self._prefix + str(key)


class StatsRedisCache(PrefixedRedisCache):
    """TTL-ed Redis wrapper class for cachetools.

    This class is empty and only kept for compatibility.
    """

    pass
