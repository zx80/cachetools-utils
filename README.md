# CacheToolsUtils

Classes to add key prefix and stats to
[cachetools](https://pypi.org/project/cachetools/) classes and use
[redis](https://redis.io/) and
[memcached](https://memcached.org/) as storage backends,
and other cache-related utils.

![Status](https://github.com/zx80/cachetools-utils/actions/workflows/cachetools-utils.yml/badge.svg?branch=main&style=flat)
![Tests](https://img.shields.io/badge/tests-17%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/CacheToolsUtils)
![Badges](https://img.shields.io/badge/badges-7-informational)
![License](https://img.shields.io/pypi/l/cachetoolsutils?style=flat)

## Module Contents

For our purpose, a cache is a key-value store, aka a dictionary, possibly with
some constraints on keys (type, size) and values (size, serialization).
Thi module provide new caches, wrappers and other utilities suitable to use
with `cachetools`.

### Cache classes

- `RedisCache` allows to see a Redis server as a python cache
  by wrapping a `redis.Redis` instance.
- `MemCached` does the same for a Memcached server.
  The utility class `JsonSerde` is a convenient JSON serializer-deserializer
  class for Memcached.
- `DictCache` a `dict` cache.

### Other wrappers to extend cache capabilities

- `PrefixedCache`, `PrefixedMemCached` and `PrefixedRedisCache` add a prefix to
  distinguish sources on a shared cache.
- `StatsCache`, `StatsMemCached` and `StatsRedisCache` add a `hits()` method
  to report the cache hit rate.
- `LockedCache` use a (thread) lock to control cache accesses.
- `TwoLevelCache` allows to combine two caches.

### Cache utilities

- `cached` decorator: a cachetools replacement which allows to test e if a
  function result is in cache, and to delete such an entry.
- `cacheFunctions` and `cacheMethods`: add caching to functions or methods.

## More

See the
[documentation](https://zx80.github.io/cachetools-utils/),
[sources](https://github.com/zx80/cachetools-utils) and
[issues](https://github.com/zx80/cachetools-utils/issues) on GitHub.

See [packages](https://pypi.org/project/CacheToolsUtils/) on PyPI.

## License

This code is public domain.
