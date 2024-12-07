# CacheToolsUtils Reference

This module provide the following cache wrappers suitable to use with
`cachetools`:

- Some classes provide actual storage or API to actual storage.
  For this purpose a cache is basically a key-value store, aka a dictionary,
  possibly with some constraints on keys (type, size) and values (size,
  serialization).

- Other classes add features on top of these, such as using a prefix so that
  a storage can be shared without collisions or keeping usage and efficiency
  statistics.

Install with `pip install CacheToolsUtils` or any other relevant mean.

## LockedCache

A cache with a lock, that can be shared between threads.
Although there is `lock` option in `cachetools` `cached` decorator, it is at
the function level thus does not work properly if a cache is shared between
functions.

```python
import threading
import cachetools
import CacheToolsUtils as ctu

lcache = ctu.LockedCache(cachetools.TTLCache(...), threading.Lock())
```

## PrefixedCache

Add a key prefix to an underlying cache to avoid key collisions.

```python
ct_base = cachetools.TTLCache(maxsize=1048576, ttl=600)
foo_cache = ctu.PrefixedCache(ct_base, "foo.")
bla_cache = ctu.PrefixedCache(ct_base, "bla.")

@cachetools.cached(cache=foo_cache)
def foo(…):
    return …

@cachetools.cached(cache=bla_cache)
def bla(…):
    return …
```

## StatsCache

Keep stats, cache hit rate shown with `hits()`.

```python
scache = ctu.StatsCache(cache)
```

## TwoLevelCache

Two-level cache, for instance a local in-memory cachetools cache for the first
level, and a larger shared `redis` or `memcached` distributed cache for the
second level.
Whether such setting can bring performance benefits is an open question.

```python
cache = ctu.TwoLevelCache(TTLCache(…), RedisCache(…))
```

There should be some consistency between the two level configurations
so that it makes sense. For instance, having two TTL-ed stores would
suggest that the secondary has a longer TTL than the primary.

There is an additional `resilient` boolean option to the constructor to
ignore errors on the second level cache, switching reliance on the first
cache only if the second one fails. Note that this does not mean that
the system would recover if the second level is back online later, because
there is no provision to manage reconnections and the like at this level.
The second level may manage that on its own, though.

## EncryptedCache

A wrapper to add an hash and encryption layer on bytes key-values.
The design is write only, i.e. the cache contents _cannot_ be extracted
with the _secret_ only:

- keys are _hashed_ to have fixed-size keys, thus cannot be recovered simply.
- values are encrypted depending on the actual key value, thus cannot be
  recovered without the key.

Hashing is based on _SHA3_, encryption uses _Salsa20_.

```python
cache = EncryptedCache(actual_cache, secret=b"super secret stuff you cannot guess", hsize=16)
```

Hash size $s$ can be extended up to _24_, key collision probability is $2^{-4 s}$.

The point of this class is to bring security to cached data on distributed
systems such as Redis.  There is no much point to encrypting in-memory caches.
All of this is very nice, but it costs cycles thus money, do you really want to
pay for them?

When used with `cached`, the key is expected to be simple bytes for encryption.
Consider `ToBytesCache` to trigger byte conversions.
The output is also bytes, which may or may not suit the underlying cache, consider
`BytesCache` if necessary, or using the `raw` option on `RedisCache`.

```python
actual = redis.Redis(…)
red = ctu.RedisCache(actual, raw=True)
enc = ctu.EncryptedCache(red, b"…")
cache = ctu.ToBytesCache(enc)

@cached(cache=PrefixedCache(cache, "foo."))
def foo(what, ever):
    return …
```

## ToBytesCache

Map keys and values to bytes.

## BytesCache

Handle bytes keys and values and map them to strings.

## MemCached

Basic wrapper, possibly with JSON key encoding thanks to the `JsonSerde` class.
Also add a `hits()` method to compute the cache hit ratio with data taken from
the memcached server.

```python
import pymemcache as pmc

mc_base = pmc.Client(server="localhost", serde=ctu.JsonSerde())
cache = ctu.MemCached(mc_base)

@cachetools.cached(cache=cache)
def poc(…):
```

Keep in mind MemCached limitations: key size is limited to 250 bytes strings where
some characters cannot be used, eg spaces, which suggest some encoding
such as base64, further reducing the actual key size; value size is 1 MiB by default.

## PrefixedMemCached

Wrapper with a prefix.
A specific class is needed because of necessary key encoding.

```python
pcache = ctu.PrefixedMemCached(mc_base, prefix="pic.")
```

## RedisCache

TTL'ed Redis wrapper, default ttl is 10 minutes and key/value JSON serialization.
Also adds a `hits()` method to compute the cache hit ratio with data taken
from the Redis server.

```python
import redis

rd_base = redis.Redis(host="localhost")
cache = ctu.RedisCache(rd_base, ttl=60)
```

Redis stores arbitrary bytes. Key and values can be up to 512 MiB.
Keeping keys under 1 KiB seems reasonable.
Option `raw` allows to skip the serialization step, if you know that
keys and values are scalars.

## PrefixedRedisCache

Wrapper with a prefix *and* a ttl.
A specific class is needed because of key encoding and value
serialization and deserialization.

```python
pcache = ctu.PrefixedRedisCache(rd_base, "pac.", ttl=3600)
```

## Functions cacheMethods and cacheFunctions

This utility function create a prefixed cache around methods of an object
or functions in the global scope.
First parameter is the actual cache, second parameter is the object or scope,
`opts` named-parameter allows additional options to `cached`,
and finally a keyword mapping from function names to prefixes.

```python
# add cache to obj.get_data and obj.get_some
ctu.cacheMethods(cache, obj, get_data="1.", get_some="2.")

# add cache to some_func
ctu.cacheFunctions(cache, globals(), opts={"key": ctu.json_key}, some_func="f.")
```

## Decorator cached

This is an extension of `cachetools` `cached` decorator, with two additions:

- `cache_in` tests whether these function parameters are in cache
- `cache_del` removes the cache entry

```python
import CacheToolsUtils as ctu

cache = ...

@ctu.cached(cache=cache)
def acme(what: str, count: int) -> str:
    return ...

print(acme("hello", 3))
assert acme.cache_in("hello", 3)
print(acme("hello", 3))
acme.cache_del("hello", 3)
assert not acme.cache_in("hello", 3)
```
