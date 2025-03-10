# CacheToolsUtils

Stackable cache classes for sharing, encryption, statistics _and more_
on top of [cachetools](https://pypi.org/project/cachetools/),
[redis](https://redis.io/) and [memcached](https://memcached.org/).

![Status](https://github.com/zx80/cachetools-utils/actions/workflows/ctu.yml/badge.svg?branch=main&style=flat)
![Tests](https://img.shields.io/badge/tests-25%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Issues](https://img.shields.io/github/issues/zx80/cachetools-utils?style=flat)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/CacheToolsUtils)
![Badges](https://img.shields.io/badge/badges-8-informational)
![License](https://img.shields.io/pypi/l/cachetoolsutils?style=flat)

## Module Contents

For our purpose, a cache is a key-value store, aka a dictionary, possibly with
some constraints on keys (type, size) and values (size, serialization).
This module provides new caches, wrappers and other utilities suitable to use
with `cachetools`. Example:

```python
import redis
import CacheToolsUtils as ctu
import config

redis_storage = redis.Redis(**config.REDIS_SERVER)
storage = ctu.RedisCache(redis_storage, raw=True, ttl=120)
crypto = ctu.EncryptedCache(storage, config.CACHE_KEY)
cache = ctu.ToBytesCache(crypto)

@ctu.cached(ctu.AutoPrefixedCache(cache), key=ctu.json_key)
def repeat(s: str, n: int) -> str:
    return s * n

@ctu.cached(ctu.AutoPrefixedCache(cache), key=ctu.json_key)
def banged(s: str, n: int) -> str:
    return repeat(s, n) + "!"

@ctu.cached(ctu.AutoPrefixedCache(cache), key=ctu.json_key)
def question(s: str, n: int) -> str:
    return repeat(s, n) + "?"

print(banged("aa", 3))    # add 2 cache entries
print(question("aa", 3))  # add 1 entry, 1 hit
print(repeat("aa", 3))    # cache hit!
print(banged("aa", 3))    # cache hit!

assert cache.hits() > 0
```

### Cache classes

- `RedisCache` allows to see a Redis server as a python cache
  by wrapping a `redis.Redis` instance.
- `MemCached` does the same for a Memcached server.
  The utility class `JsonSerde` is a convenient JSON serializer-deserializer
  class for Memcached.
- `DictCache` a very simple `dict` cache.

### Wrappers to extend cache capabilities

- `PrefixedCache`, `PrefixedMemCached` and `PrefixedRedisCache` add a prefix to
  distinguish sources on a shared cache.
- `AutoPrefixedCache` add a counter-based prefix.
- `StatsCache`, `MemCached` and `RedisCache` add a `hits` method
  to report the cache hit rate, `stats` to report statistics and
  `reset` to reset statistics.
- `LockedCache` use a (thread) lock to control cache accesses.
- `TwoLevelCache` allows to combine two caches.
- `DebugCache` to trace cache calls using `logging`.
- `EncryptedCache` a cache with key hashing and value encryption.
- `ToBytesCache` map keys and values to bytes.
- `BytesCache` map bytes keys and values to strings.

### Cache utilities

- `cached` decorator: a cachetools replacement which allows to test if a
  function result is in cache, and to delete such an entry.
- `cacheFunctions` and `cacheMethods`: add caching to functions or methods.
- `json_key`, `hash_json_key`, `full_hash_key`: convenient JSON-based cache key
  serialization functions for `cached`.

## License

This code is [Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

All software has bug, this is software, hence… Beware that you may lose your
hairs or your friends because of it. If you like it, feel free to send a
postcard to the author.

## More

See the
[documentation](https://zx80.github.io/cachetools-utils/),
[sources](https://github.com/zx80/cachetools-utils) and
[issues](https://github.com/zx80/cachetools-utils/issues) on GitHub.

See [packages](https://pypi.org/project/CacheToolsUtils/) on PyPI.
