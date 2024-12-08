"""
CacheTools Utilities. This code is public domain.
"""

from typing import Any, Callable, MutableMapping
import abc

import base64
import hashlib
import cachetools
import json

from importlib.metadata import version as pkg_version
__version__ = pkg_version("CacheToolsUtils")

import logging
log = logging.getLogger(__name__)


#
# UTILS: Abstract Classes and Mixins
#

_NO_DEFAULT = object()


class _MutMapMix:
    """Convenient MutableMapping Mixin, forward to _cache."""

    # FIXME coverage reports this as missing with Python 3.14
    _cache: MutableMapping  # pragma: no cover

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

    @abc.abstractmethod
    def _key(self, key: Any) -> Any:  # pragma: no cover
        return None

    def __contains__(self, key: Any):
        return self._cache.__contains__(self._key(key))

    def __getitem__(self, key: Any):
        return self._cache.__getitem__(self._key(key))

    def __setitem__(self, key: Any, val: Any):
        return self._cache.__setitem__(self._key(key), val)

    def __delitem__(self, key: Any):
        return self._cache.__delitem__(self._key(key))


class _StatsMix:
    """Convenient Mixin to forward stats methods to _cache."""

    def hits(self) -> float|None:
        return self._cache.hits()  # type: ignore

    def stats(self) -> dict[str, Any]:
        return self._cache.stats()  # type: ignore

    def reset(self):
        return self._cache.reset()  # type: ignore


class _RedisMix:  # pragma: no cover
    """Convenient mixin to forward redis methods."""

    # NOTE declaring _cache would conflict with _MutMapMix
    # probably there is a clever way to do that, let us not bother

    def set(self, *args, **kwargs):
        return self._cache.set(*args, **kwargs)  # type: ignore

    def get(self, *args, **kwargs):
        return self._cache.get(*args, **kwargs)  # type: ignore

    def delete(self, *args, **kwargs):
        return self._cache.delete(*args, **kwargs)  # type: ignore

    def info(self, *args, **kwargs):
        return self._cache.info(*args, **kwargs)  # type: ignore

    def dbsize(self, *args, **kwargs):
        return self._cache.dbsize(*args, **kwargs)  # type: ignore


#
# CACHETOOLS EXTENSIONS
#

class DebugCache(_StatsMix, MutableMapping):
    """Debug class.

    :param cache: actual cache
    :param log: logging instance
    :param name: name of instance for output
    """

    def __init__(self, cache: MutableMapping, log: logging.Logger, name="cache"):
        self._cache = cache
        self._log = log
        self._name = name
        self._log.info(f"DebugCache {name}: init")

    def _debug(self, msg):
        self._log.debug(f"DebugCache {self._name}: {msg}")

    def __contains__(self, key):
        self._debug(f"in {key}")
        return self._cache.__contains__(key)

    def __getitem__(self, key):
        self._debug(f"get {key}")
        return self._cache.__getitem__(key)

    def __setitem__(self, key, val):
        self._debug(f"set {key} {val}")
        return self._cache.__setitem__(key, val)

    def __delitem__(self, key):
        self._debug(f"del {key}")
        return self._cache.__delitem__(key)

    def __len__(self):
        self._debug("len")
        return self._cache.__len__()

    def __iter__(self):
        self._debug("iter")
        return self._cache.__iter__()

    def clear(self):
        self._debug("clear")
        return self._cache.clear()

    def reset(self):  # pragma: no cover
        self._debug("reset")
        return self._cache.reset()  # type: ignore


class DictCache(_MutMapMix, MutableMapping):
    """Cache class based on dict."""

    def __init__(self):
        self._cache = dict()

    def clear(self):
        self._cache.clear()


class LockedCache(_MutMapMix, _StatsMix, _RedisMix, MutableMapping):
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

    def __init__(self, cache: MutableMapping, lock):
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


class PrefixedCache(_KeyMutMapMix, _StatsMix, MutableMapping):
    """Cache class to add a key prefix.

    :param cache: actual cache.
    :param prefix: prefix to prepend to keys.
    """

    def __init__(self, cache: MutableMapping, prefix: str|bytes = ""):
        self._prefix = prefix
        self._cache = cache
        # dynamic cast
        self._cast: Callable[[Any], str]|Callable[[Any], bytes]
        if isinstance(prefix, str):
            self._cast = lambda v: str(v)
        else:  # pragma: no cover
            self._cast = lambda v: bytes(v)

    def _key(self, key: Any) -> Any:
        return self._prefix + self._cast(key)  # type: ignore


class StatsCache(_MutMapMix, MutableMapping):
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

    def __init__(self, cache: MutableMapping):
        self._cache = cache
        self.reset()

    def hits(self) -> float:
        """Return the cache hit ratio."""
        return float(self._hits) / max(self._reads, 1)

    def reset(self):
        """Reset internal stats data."""
        self._reads, self._writes, self._dels, self._hits = 0, 0, 0, 0

    def stats(self) -> dict[str, Any]:
        """Return available stats data as dict."""
        return {
            "type": 1,
            "reads": self._reads,
            "writes": self._writes,
            "dels": self._dels,
            "hits": self.hits(),
            "size": self._cache.__len__()
        }

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


class TwoLevelCache(_MutMapMix, MutableMapping):
    """Two-Level Cache class for CacheTools.

    :param cache: first (smaller, shorter TTL) cache
    :param cache2: second (larger, longer TTL) cache
    :param resilient: whether to ignore cache2 failures
    """

    def __init__(self, cache: MutableMapping, cache2: MutableMapping, resilient=False):
        self._resilient = resilient
        self._cache = cache
        self._cache2 = cache2

    def __getitem__(self, key):
        try:
            return self._cache.__getitem__(key)
        except KeyError as ke:
            try:
                val = self._cache2.__getitem__(key)
            except KeyError:
                raise ke  # initial error
            except Exception as e:
                if self._resilient:  # pragma: no cover
                    log.debug(e, exc_info=True)
                    raise ke
                else:
                    raise
            # put cache2 value into cache
            self._cache.__setitem__(key, val)
            return val

    def __setitem__(self, key, val):
        try:
            self._cache2.__setitem__(key, val)
        except Exception as e:
            if self._resilient:
                log.debug(e, exc_info=True)
            else:
                raise
        return self._cache.__setitem__(key, val)

    def __delitem__(self, key):
        try:
            self._cache2.__delitem__(key)
        except KeyError:
            pass
        except Exception as e:
            if self._resilient:
                log.debug(e, exc_info=True)
            else:
                raise
        return self._cache.__delitem__(key)

    def clear(self):
        # NOTE not passed on cache2…
        return self._cache.clear()

    def stats(self) -> dict[str, Any]:
        data = {"type": 2}
        try:
            data["cache1"] = self._cache.stats()  # type: ignore
        except Exception:
            data["cache1"] = {}  # type: ignore
        try:
            data["cache2"] = self._cache2.stats()  # type: ignore
        except Exception:
            data["cache2"] = {}  # type: ignore
        return data

    def hits(self) -> float|None:
        data = self.stats()
        c1, c2 = data["cache1"], data["cache2"]
        if (c1 and "type" in c1 and c1["type"] == 1 and
            c2 and "type" in c2 and c2["type"] == 1):
            return float(c1["hits"] + c2["hits"]) / max(c1["reads"] + c2["reads"], 1)
        # else
        return None

    def reset(self):  # pragma: no cover
        self._cache.reset()  # type: ignore
        self._cache2.reset()  # type: ignore


#
# Encrypted Cache
#
class EncryptedCache(_KeyMutMapMix, _StatsMix, MutableMapping):
    """Encrypted Bytes Key-Value Cache.

    :param secret: bytes of secret, at least 16 bytes.
    :param hsize: size of hashed key, default is *16*.
    :param csize: value checksum size, default is *0*.

    The key is *not* encrypted but simply hashed, thus they are
    fixed size with a very low collision probability.

    By design, the clear-text key is needed to recover the value,
    as each value is encrypted with its own key and nonce.

    Algorithms:
    - SHA3: hash/key/nonce derivation and checksum.
    - Salsa20: value encryption.
    """

    def __init__(self, cache: MutableMapping, secret: bytes, hsize: int = 16, csize: int = 0):
        self._cache = cache
        assert len(secret) >= 16
        self._secret = secret
        assert 8 <= hsize <= 32
        self._hsize = hsize
        assert 0 <= csize <= 32
        self._csize = csize
        from Crypto.Cipher import Salsa20
        self._cipher = Salsa20

    def _keydev(self, key) -> tuple[bytes, bytes, bytes]:
        """Compute hash, key and nonce from initial key."""
        hkey = hashlib.sha3_512(key + self._secret).digest()
        # NOTE hash and nonce may overlap, which is not an issue
        return (hkey[:self._hsize], hkey[32:], hkey[24:32])

    def _key(self, key):
        return self._keydev(key)[0]

    def __setitem__(self, key, val):
        hkey, vkey, vnonce = self._keydev(key)
        xval = self._cipher.new(key=vkey, nonce=vnonce).encrypt(val)
        if self._csize:
            cs = hashlib.sha3_256(val).digest()[:self._csize]
            xval = cs + xval
        self._cache[hkey] = xval

    def __getitem__(self, key):
        hkey, vkey, vnonce = self._keydev(key)
        xval = self._cache[hkey]
        if self._csize:  # split cs from encrypted value
            cs, xval = xval[:self._csize], xval[self._csize:]
        else:
            cs = None
        val = self._cipher.new(key=vkey, nonce=vnonce).decrypt(xval)
        if self._csize and cs != hashlib.sha3_256(val).digest()[:self._csize]:
            raise KeyError(f"invalid encrypted value for key {key}")
        return val


class BytesCache(_KeyMutMapMix, _StatsMix, MutableMapping):
    """Map bytes to strings."""

    def __init__(self, cache):
        self._cache = cache

    def _key(self, key):
        # assert isinstance(key, bytes)
        return base64.b85encode(key).decode("ASCII")

    def __setitem__(self, key, val):
        self._cache.__setitem__(self._key(key), self._key(val))

    def __getitem__(self, key):
        val = self._cache.__getitem__(self._key(key))
        # assert isinstance(val, str)
        return base64.b85decode(val)


class ToBytesCache(_KeyMutMapMix, _StatsMix, MutableMapping):
    """Map (JSON-serializable) cache keys and values to bytes."""

    def __init__(self, cache):
        self._cache = cache

    def _key(self, key):
        return json.dumps(key, sort_keys=True, separators=(",", ":")).encode("UTF-8")

    def __setitem__(self, key, val):
        self._cache.__setitem__(self._key(key), self._key(val))

    def __getitem__(self, key):
        return json.loads(self._cache.__getitem__(self._key(key)).decode("UTF-8"))


#
# CACHED DECORATOR AND HELPERS
#
def cached(cache, *args, **kwargs):
    """Extended decorator with delete and exists.

    All parameters are forwarded to ``cachetools.cached``.

    :param cache: actual cache.

    If *f(\\*args, \\*\\*kwargs)* is the ``cached`` function, then:

    - ``f.cache_in(*args, **kwargs)`` tells whether the result is cached.
    - ``f.cache_del(*args, **kwargs)`` deletes (invalidates) the cached result.
    """

    def decorate(fun: Callable):

        # use cachetools "cached" decorator
        fun = cachetools.cached(cache, *args, **kwargs)(fun)

        # extend it with two functions
        def cache_in(*args, **kwargs) -> bool:
            """Tell whether key is already in cache."""
            key = fun.cache_key(*args, **kwargs)  # type: ignore
            return key in fun.cache  # type: ignore

        def cache_del(*args, **kwargs):
            """Delete key from cache, return if it was there."""
            key = fun.cache_key(*args, **kwargs)  # type: ignore
            key_in = key in fun.cache  # type: ignore
            if key_in:
                del fun.cache[key]  # type: ignore
            return key_in

        fun.cache_in = cache_in    # type: ignore
        fun.cache_del = cache_del  # type: ignore

        return fun

    return decorate


# short generator type name
MapGen = Callable[[MutableMapping, str], MutableMapping]


def cacheMethods(
    cache: MutableMapping,
    obj: Any,
    gen: MapGen = PrefixedCache,
    opts: dict[str, Any] = {},
    **funs
):
    """Cache some object methods.

    :param cache: cache to use.
    :param obj: object instance to be cached.
    :param gen: generator of PrefixedCache.
    :param opts: additional parameters when calling `cached`.
    :param funs: name of methods and corresponding prefix

    .. code-block:: python

       cacheMethods(cache, item, PrefixedCache, compute1="c1.", compute2="c2.")
    """
    for fun, prefix in funs.items():
        assert hasattr(obj, fun), f"cannot cache missing method {fun} on {obj}"
        f = getattr(obj, fun)
        while hasattr(f, "__wrapped__"):
            f = f.__wrapped__
        setattr(obj, fun, cached(cache=gen(cache, prefix), **opts)(f))


def cacheFunctions(
    cache: MutableMapping,
    globs: MutableMapping[str, Any],
    gen: MapGen = PrefixedCache,
    opts: dict[str, Any] = {},
    **funs
):
    """Cache some global functions, with a prefix.

    :param cache: cache to use.
    :param globs: global object dictionary.
    :param gen: generator of PrefixedCache.
    :param opts: additional parameters when calling `cached`.
    :param funs: name of functions and corresponding prefix

    .. code-block:: python

       cacheFunctions(cache, globals(), PrefixedCache, fun1="f1.", fun2="f2.")
    """
    for fun, prefix in funs.items():
        assert fun in globs, "caching functions: {fun} not found"
        f = globs[fun]
        while hasattr(f, "__wrapped__"):
            f = f.__wrapped__
        globs[fun] = cached(cache=gen(cache, prefix), **opts)(f)


# JSON-based key function
# NOTE obviously this only works if parameters are json-serializable…
def json_key(*args, **kwargs) -> str:
    """JSON serialization of arguments."""
    val: Any
    if kwargs:  # object
        if args:
            val = {"*": args, "**": kwargs}
        else:
            val = {"**": kwargs}
    else:  # array
        val = args
    return json.dumps(val, sort_keys=True, separators=(",", ":"))


# Hmmm… is this useful?
class _HashJsonKey:
    """A cache key with a persistant hash value."""

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._key = json_key(*args, **kwargs)
        self._hashed = self._key.__hash__()

    def __hash__(self):
        return self._hashed

    def __str__(self):
        return self._key


def hash_json_key(*args, **kwargs):
    return _HashJsonKey(*args, **kwargs)


def full_hash_key(*args, **kwargs) -> str:
    """Reduce arguments to a single 128-bits hash."""
    skey = json_key(*args, **kwargs)
    hkey = hashlib.sha3_256(skey.encode("UTF-8")).digest()[:16]
    return base64.b85encode(hkey).decode("ASCII")


#
# MEMCACHED
#
class JsonSerde:
    """JSON serialize/deserialize class for MemCached (``pymemcache``).

    .. code-block:: python

       import pymemcache as pmc
       import CacheToolsUtils as ctu
       pmc_cache = pmc.Client(server="localhost", serde=ctu.JsonSerde())
    """

    # keep strings, else json
    def serialize(self, key, value):
        if isinstance(value, bytes):
            return value, 1
        elif isinstance(value, str):
            return value.encode("utf-8"), 2
        else:
            return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"), 3

    # reverse previous serialization
    def deserialize(self, key, value, flag):
        if flag == 1:
            return value
        elif flag == 2:
            return value.decode("utf-8")
        elif flag == 3:
            return json.loads(value.decode("utf-8"))
        else:
            raise Exception("Unknown serialization format")


class MemCached(_KeyMutMapMix, MutableMapping):
    """MemCached-compatible wrapper class for cachetools with key encoding.

    :param cache: actual memcached cache.

    .. code-block:: python

       import pymemcache as pmc
       import CacheToolsUtils as ctu
       cache = ctu.MemCached(pmc.Client(server="localhost", serde=ctu.JsonSerde()))

       @ctu.cached(cache=cache)
       def whatever(...):
    """

    def __init__(self, cache):
        # import pymemcache as pmc
        # assert isinstance(cache, pmc.Client)
        self._cache = cache

    # memcached keys are constrained bytes, we need some encoding…
    # short (250 bytes) ASCII without control chars nor spaces
    # we do not use hashing which might be costly or induce collisions
    def _key(self, key):
        return base64.b85encode(str(key).encode("utf-8"))

    def __len__(self):
        return self._cache.stats()[b"curr_items"]  # type: ignore

    def stats(self) -> dict[str, Any]:
        """Return MemCached stats."""
        return self._cache.stats()  # type: ignore

    def clear(self):  # pragma: no cover
        """Flush MemCached contents."""
        return self._cache.flush_all()  # type: ignore

    def hits(self) -> float:
        """Return overall cache hit ratio."""
        stats = self._cache.stats()  # type: ignore
        return float(stats[b"get_hits"]) / max(stats[b"cmd_get"], 1)


class PrefixedMemCached(MemCached):
    """MemCached-compatible wrapper class for cachetools with a key prefix.

    :param cache: actual memcached cache.
    :param prefix: post key-encoding prepended prefix.

    .. code-block:: python

       import pymemcache as pmc
       import CacheToolsUtils as ctu
       # add a "app." prefix to keys, after serialization
       cache = ctu.PrefixedMemCached(pmc.Client(server="localhost", serde=ctu.JsonSerde()), "app.")
    """

    def __init__(self, cache, prefix: str = ""):
        super().__init__(cache=cache)
        self._prefix = bytes(prefix, "utf-8")

    def _key(self, key):
        return self._prefix + base64.b85encode(str(key).encode("utf-8"))


#
# REDIS
#
class RedisCache(MutableMapping):
    """Redis TTL-ed wrapper for cachetools (``redis``).

    :param cache: actual redis cache.
    :param ttl: time-to-live in seconds, used as default expiration (``ex``), default is 600.
    :param raw: whether to serialize keys and values, default is *False*.

    Keys and values are serialized in *JSON*.

    .. code-block:: python

       import redis
       import CacheToolsUtils as ctu
       # redis with 1 hour expiration
       cache = ctu.RedisCache(redis.Redis(host="localhost"), 3600)
    """

    def __init__(self, cache, ttl=600, raw=False):
        # import redis
        # assert isinstance(cache, redis.Redis)
        self._cache = cache
        self._ttl = ttl
        self._raw = raw

    def clear(self):  # pragma: no cover
        """Flush Redis contents."""
        return self._cache.flushdb()

    def _serialize(self, s):
        return s if self._raw else json.dumps(s, sort_keys=True, separators=(",", ":"))

    def _deserialize(self, s):
        return s if self._raw else json.loads(s)

    def _key(self, key):
        return key if self._raw else json.dumps(key, sort_keys=True, separators=(",", ":"))

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

    def stats(self) -> dict[str, Any]:
        return self.info(section="stats")

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
    def hits(self) -> float:
        """Return cache hits."""
        stats = self.stats()
        return float(stats["keyspace_hits"]) / (
            stats["keyspace_hits"] + stats["keyspace_misses"]
        )


class PrefixedRedisCache(RedisCache):
    """Prefixed Redis wrapper class for cachetools.

    :param cache: actual redis cache.
    :param prefix: post key encoding prefix, default is empty.
    :param ttl: time-to-live in seconds, used as default expiration (``ex``), default is 600.

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


# FIXME should it be removed?
class StatsRedisCache(PrefixedRedisCache):
    """TTL-ed Redis wrapper class for cachetools.

    This class is nearly empty.
    """

    def flushdb(self):
        self._cache.clear()

    pass
