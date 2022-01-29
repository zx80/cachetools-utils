# cachetools-utils

Classes to add key prefix and stats to
[cachetools](https://pypi.org/project/cachetools/) classes and use
[redis](https://redis.io/) and
[memcached](https://memcached.org/) as storage backends.

## Usage

Install with `pip`:

```Shell
pip install CacheToolsUtils
```

See below.

## Documentation

This module provide the following cache wrappers suitable to use
with `cachetools`:

### PrefixedCache

Add a key prefix.

```Python
import CacheToolsUtils as ctu

base = cachetools.TTLCache(ttl=600)
foo_cache = ctu.PrefixedCache(base, "foo.")
bla_cache = ctu.PrefixedCache(base, "bla.")

@cachetools.cached(cache=foo_cache)
def foo(…):
    return …

@cachetools.cached(cache=bla_cache)
def bla(…):
    return …
```

### StatsCache

Keep stats, cache hit rate shown with `hits()`.

### MemCached

Basic wrapper with JSON key encoding.

```Python
import pymemcache as pmc

mcbase = pmc.Client(server="localhost", serde=ctu.JsonSerde())
cache = ctu.MemCached(mcbase)

@cachetools.cached(cache=cache)
def poc(…):
```

### PrefixedMemCached

Wrapper with a prefix.

```Python
pcache = ctu.PrefixedMemCached(mcbase, prefix="pic.")
```

### StatsMemCached

Wrapper with stats actually taken from the MemCached server.

### RedisCache

TTL'ed Redis wrapper, default ttl is 10 minutes.

```Python
import redis

rd_base = redis.Redis(host="localhost")
cache = ctu.RedisCache(rd_base, ttl=60)
```

### PrefixedRedisCache

Wrapper with a prefix and a ttl.

### StatsRedisCache

Wrapper with stats (call `hits()`) and a ttl.

## License

This code is public domain.

## Versions

### 1.0.0 on 2022-01-29

Add `set`, `get` and `delete` forwarding to `RedisCache`, so that redis
classes can be stacked.

### 0.9.0 on 2022-01-29

Initial version extracted from another project.


## TODO

- improve documentation
- add a `close`?
