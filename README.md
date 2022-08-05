# cachetools-utils

Classes to add key prefix and stats to
[cachetools](https://pypi.org/project/cachetools/) classes and use
[redis](https://redis.io/) and
[memcached](https://memcached.org/) as storage backends,
and other cache-related utils.

![Tests](https://img.shields.io/badge/tests-14%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/CacheToolsUtils)
![Badges](https://img.shields.io/badge/badges-6-informational)
![License](https://img.shields.io/pypi/l/cachetoolsutils?style=flat)

## Thoughts about Caching

Caching is a key component of any significant Web or REST backend so as to avoid
performance issues when accessing the storage tier, in term of latency,
throughput and resource usage.

- **Shared Cache**

  A convenient setup is to have *one* shared cache storage tier at the
  application level, which is accessed through wrappers to avoid collisions
  between cache functions, basically by prepending keys with some prefix.

  Depending on the access pattern, it may or may not be useful to put
  a multiple-level caching strategy in place, with a local in-process cache
  and a higher-level inter-process and inter-host cache such as Redis
  or MemCached.

  When using a global shared cache, it should be clear that the cache may
  hold sensitive data and its manipulation may allow to change the behavior
  of the application, including working around security by tampering with
  the application authentication and authorization guards.

- **Latency**

  In order to reduce latency, as most time should be spent in network accesses,
  reducing the number of trips is a key strategy. This suggests combining
  data transfers where possible through higher-level interfaces and queries,
  both at the HTTP level and at the database level.

  Denormalizing the relational data model may help. Having an
  application-oriented view of the model (eg JSON objects rather than
  attributes and tables) can help performance, at the price of losing some of
  the consistency warranties provided by a database.  The best of both word may
  be achieved, to some extent, by storing JSON data into a database such as
  [Postgres](https://postgresql.org/).

  Invalidating data from the cache requires a detailed knowledge of internal
  cache operations and are not very easy to manage at the application level,
  so devops should want to avoid this path if possible, possibly by relying
  on a time-based cache expiration aka TTL (time-to-live).

- **Throughput**

  **Write** operations need to be sent to storage.
  Depending on transaction requirements, i.e. whether some rare data loss is
  admissible, various strategies can be applied, such as updating in parallel
  the cache and the final storage. Yet again, this strategy requires a deep
  knowledge of the underlying cache implementation, thus is best avoided most
  of the time.

  **Read** operations can be cached, at the price of possibly having
  inconsistent data shown to users.
  LFU/LRU cache strategies mean that inconsistent data can be kept in cache
  for indefinite time, which is annoying. A TLL expiration on top of that
  makes such discrepancies bounded in time, so that after some time the data
  shown are eventually up to date.

Basically the application should aim at maximizing throughput for the available
resources whilst keeping the latency under control, eg 90% of queries under
some limit.

## Module Documentation

This module provide the following cache wrappers suitable to use with
`cachetools`:

- Some classes provide actual storage or API to actual storage.
  For this purpose a cache is basically a key-value store, aka a dictionary,
  possibly with some constraints on keys (type, size) and values (size,
  serialization).

- Other classes add features on top of these, such as using a prefix so that
  a storage can be shared without collisions or keeping usage and efficiency
  statistics.

### PrefixedCache

Add a key prefix to an underlying cache to avoid key collisions.

```Python
import cachetools
import CacheToolsUtils as ctu

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

### StatsCache

Keep stats, cache hit rate shown with `hits()`.

```Python
scache = ctu.StatsCache(cache)
```

### TwoLevelCache

Two-level cache, for instance a local in-memory cachetools cache for the first
level, and a larger shared `redis` or `memcached` distributed cache for the
second level.
Whether such setting can bring performance benefits is an open question.

```Python
cache = ctu.TwoLevelCache(TTLCache(…), RedisCache(…))
```

There should be some consistency between the two level configurations
so that it makes sense. For instance, having two TTL-ed stores would
suggest that the secondary has a longer TTL than the primary.

### MemCached

Basic wrapper, possibly with JSON key encoding thanks to the `JsonSerde` class.
Also add a `hits()` method to compute the cache hit ratio with data taken from
the memcached server.

```Python
import pymemcache as pmc

mc_base = pmc.Client(server="localhost", serde=ctu.JsonSerde())
cache = ctu.MemCached(mc_base)

@cachetools.cached(cache=cache)
def poc(…):
```

Keep in mind MemCached limitations: key size is limited to 250 bytes strings where
some characters cannot be used, eg spaces, which suggest some encoding
such as base64, further reducing the actual key size; value size is 1 MiB by default.

### PrefixedMemCached

Wrapper with a prefix.
A specific class is needed because of necessary key encoding.

```Python
pcache = ctu.PrefixedMemCached(mc_base, prefix="pic.")
```

### RedisCache

TTL'ed Redis wrapper, default ttl is 10 minutes.
Also adds a `hits()` method to compute the cache hit ratio with data taken
from the Redis server.

```Python
import redis

rd_base = redis.Redis(host="localhost")
cache = ctu.RedisCache(rd_base, ttl=60)
```

Redis stores arbitrary bytes. Key and values can be up to 512 MiB.
Keeping keys under 1 KiB seems reasonable.

### PrefixedRedisCache

Wrapper with a prefix *and* a ttl.
A specific class is needed because of key encoding and value
serialization and deserialization.

```Python
pcache = ctu.PrefixedRedisCache(rd_base, "pac.", ttl=3600)
```

### cacheMethods and cacheFunctions

This utility function create a prefixed cache around methods of an object
or functions in the global scope.
First parameter is the actual cache, second parameter is the object or scope,
and finally a keyword mapping from function names to prefixes.

```Python
# add cache to obj.get_data and obj.get_some
ctu.cacheMethods(cache, obj, get_data="1.", get_some="2.")

# add cache to some_func
ctu.cacheFunctions(cache, globals(), some_func="f.")
```


## Install

Install with `pip`:

```Shell
pip install CacheToolsUtils
```

See above for example usage.


## License

This code is public domain.


## Versions

### 4.2 on 2022-08-05

Fix minor typo in a badge.

### 4.1 on 2022-08-05

Code reformating.
Improved documentation.
Improved checks.
Improved Makefile.

### 4.0 on 2022-03-13

Remove `StatsRedisCache` and `StatsMemCached` by moving the `hits()` method
to `RedisCache` and `MemCached`, respectively.
The two classes still exist for upward compatibility, but are deprecated.
Improve test coverage, now only 4 not-covered lines.
Improve documentation.

### 3.0 on 2022-03-06

Use simpler `kwargs` approach for caching methods and functions.
Add a `gen` parameter for caching methods and functions.
Improve documentation.

### 2.0 on 2022-02-24

Add `cacheMethods` and `cacheFunctions`.
Improve documentation.
100% coverage test.

### 1.1.0 on 2022-01-30

Improve documentation.
Add `TwoLevelCache`.
Add 100% coverage test.

### 1.0.0 on 2022-01-29

Add `set`, `get` and `delete` forwarding to `RedisCache`, so that redis
classes can be stacked.

### 0.9.0 on 2022-01-29

Initial version extracted from another project.


## TODO

- add a `close`?
- rename `hits`  `hit_rate`?
- add other efficiency statistics?
