# Thoughts about Caching

Caching is a key component of any significant Web or REST backend so as to avoid
performance issues when accessing the storage tier, in term of latency,
throughput and resource usage.

## Cache Hierarchy

In a modern web or mobile application, caching may take place at multiple
levels to hide the fundamental sluggishness of network and database/disk
accesses to permanent, reliable and transactional storage, mostly due to
latency:

- at the web application level, `SWR` and `redux` are libraries designed
  to hide the latency of accessing remote data, eg by providing _stale_
  data while waiting for updates, or keeping a local state.
- at the web browser level, honoring HTTP `Cache-Control` headers helps
  the application avoiding actual HTTP request.
- at the HTTP server/proxy level, response may be cached with specific
  modules, such as `mod_cache` for Apache; If the web server handles
  authentication it may also use caches to avoid data traffic.
- at the server application level, say a Python Flask back-end in Python,
  CacheTools and CacheToolsUtils can help maintain efficient data accesses,
  possibly using multilevel in-memory distributed caches such as Redis or
  Memcached.
- at the application architectural level, services such as elasticache
  can hide data accesses and indexing, in effect replicating the entire
  underlying database.
- within the database itself, accesses to raw data are cached in shared
  memory, both at the OS and database level.
- at the the hardware level, storage can benefit from different levels of
  caches.

## Shared Cache

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

Although a cache may allow to improve performance, an important side effect is
that it reduces the query load on the actual database backend.

## Latency

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
Note that the extended `cached` decorator provided with this module includes a
the convenient `cached_del` method to help implement cache invalidation at
the application level.

## Throughput

**Write** operations need to be sent to storage.
Depending on transaction requirements, i.e. whether some rare data loss is
admissible, various strategies can be applied, such as updating in parallel
the cache and the final storage. Yet again, this strategy requires a deep
knowledge of the underlying cache implementation, thus is best avoided most
of the time.

**Read** operations can be cached, at the price of possibly having
inconsistent data shown to users.
LRU/LFU/ARC cache strategies mean that inconsistent data can be kept in cache
for indefinite time, which is annoying. A TLL expiration on top of that
makes such discrepancies bounded in time, so that after some time the data
shown are eventually up to date.

Basically the application should aim at maximizing throughput for the available
resources whilst keeping the latency under control, eg 90% of queries under
some limit.
