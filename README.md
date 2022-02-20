# cachetools-utils

Classes to add key prefix and stats to
[cachetools](https://pypi.org/project/cachetools/) classes and use
[redis](https://redis.io/) and
[memcached](https://memcached.org/) as storage backends,
and other utils.


## Install

Install with `pip`:

```Shell
pip install CacheToolsUtils
```

See below for example usage.


## Documentation

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
scache = StatsCache(cache)
```

### TwoLevelCache

Two-level cache, for instance a local in-memory cachetools cache for the first
level, and a larger shared `redis` or `memcached` distributed cache for the
second level.
Whether such setting can bring performance benefits is an open question.

```Python
cache = TwoLevelCache(TTLCache(…), RedisCache(…))
```

There should be some consistency between the two level configurations
so that it make sense. For instance, having two TTL-ed stores would
suggest that the secondary has a longer TTL than the primary.

### MemCached

Basic wrapper, possibly with JSON key encoding.

```Python
import pymemcache as pmc

mc_base = pmc.Client(server="localhost", serde=ctu.JsonSerde())
cache = ctu.MemCached(mc_base)

@cachetools.cached(cache=cache)
def poc(…):
```

### PrefixedMemCached

Wrapper with a prefix.

```Python
pcache = ctu.PrefixedMemCached(mc_base, prefix="pic.")
```

### StatsMemCached

Wrapper with stats actually taken from the MemCached server.

```Python
scache = ctu.StatsMemCached(pcache)
```

### RedisCache

TTL'ed Redis wrapper, default ttl is 10 minutes.

```Python
import redis

rd_base = redis.Redis(host="localhost")
cache = ctu.RedisCache(rd_base, ttl=60)
```

### PrefixedRedisCache

Wrapper with a prefix *and* a ttl.

```Python
pcache = ctu.PrefixedRedisCache(rd_base, "pac.", ttl=3600)
```

### StatsRedisCache

Wrapper with stats (call `hits()`) *and* a ttl.
Stats are actually taken from the Redis server.

```Python
scache = ctu.StatsRedisCache(pcache)
```

### cacheMethods and cacheFunctions

This utility function create a prefixed cache around methods of an object
or functions in the global scope.
First parameter is the actual cache, second parameter is the object or scope,
third parameter is a dictionary mapping method names to prefixes.

```Python
ctu.cacheMethods(cache, obj, {"get_data": "1.", "get_some": "2."})
ctu.cacheFunctions(cache, globals(), {"some_func": "f."})
```


## License

This code is public domain.


## Versions

### 2.0 in Future

Add `cacheMethods` and `cacheFunctions`.
Improve documentation.

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

- improve documentation further.
- add a `close`?
- add my thoughts about caching: TTL!
- rename `hits`  `hit_rate`.
- add some other efficiency statistics?
