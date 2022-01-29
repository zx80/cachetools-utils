#! /usr/bin/env python

from typing import Optional
import cachetools as ct
import CacheToolsUtils as ctu
import socket
import pytest
import logging

logging.basicConfig()
log = logging.getLogger()
# log.setLevel(logging.DEBUG)

def has_service(host="localhost", port=22):
    """check whether a network TCP/IP service is available."""
    try:
        tcp_ip = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_ip.settimeout(1)
        res = tcp_ip.connect_ex((host, port))
        return res == 0
    except Exception as e:
        log.info(f"connection to {(host, port)} failed: {e}")
        return False
    finally:
        tcp_ip.close()

def cached_fun(cache):
    """return a cached function with basic types."""
    @ct.cached(cache=cache)
    def fun(i: int, s: Optional[str], b: bool) -> int:
        return i + (10*len(s) if s is not None else -20) + (100 if b else 0)
    return fun

def run_cached(cache):
    """run something on a cached function."""
    fun = cached_fun(cache)
    x = 0
    for n in range(10):
        for i in range(5):
            for s in ["a", "bb", "ccc", "", None]:
                for b in [False, True]:
                    v = fun(i, s, b)
                    # log.debug(f"fun{(i, s, b)} = {v} {type(v)}")
                    x += v
    assert x == 30000

def test_key_ct():
    c0 = ct.TTLCache(maxsize=100, ttl=100)
    c1 = ctu.PrefixedCache(c0, "f.")
    c2 = ctu.PrefixedCache(c0, "f.")
    c3 = ctu.PrefixedCache(c0, "g.")
    run_cached(c1)
    run_cached(c2)
    assert len(c0) == 50
    assert "f.(0, 'a', False)" in c0
    assert c1[(3, "bb", True)] == 123
    assert "f.(4, None, True)" in c0
    assert c2[(4, "ccc", True)] == 134
    run_cached(c3)
    assert len(c0) == 100
    assert c3[(2, "", True)] == 102

def test_stats_ct():
    c0 = ct.TTLCache(maxsize=100, ttl=100)
    cache = ctu.StatsCache(c0)
    run_cached(cache)
    assert len(cache) == 50
    assert cache[(4, "a", True)] == 114
    assert cache[(0, None, False)] == -20
    assert cache.hits() > 0.8

@pytest.mark.skipif(not has_service(port=11211), reason="no local memcached service available for testing")
def test_memcached():
    import pymemcache as pmc
    c0 = pmc.Client(server="localhost", serde=ctu.JsonSerde())
    c1 = ctu.MemCached(c0)
    run_cached(c1)
    assert len(c1) >= 50
    assert c1["(1, 'a', True)"] == 111
    assert c1["(3, None, False)"] == -17

@pytest.mark.skipif(not has_service(port=11211), reason="no local memcached service available for testing")
def test_key_memcached():
    import pymemcache as pmc
    c0 = pmc.Client(server="localhost", serde=ctu.JsonSerde())
    c1 = ctu.PrefixedMemCached(c0, "CacheToolsUtils.")
    run_cached(c1)
    assert len(c1) >= 50
    assert c1["(1, 'a', True)"] == 111
    assert c1["(3, None, False)"] == -17

@pytest.mark.skipif(not has_service(port=11211), reason="no local memcached service available for testing")
def test_stats_memcached():
    import pymemcache as pmc
    c0 = pmc.Client(server="localhost", serde=ctu.JsonSerde(), key_prefix=b"ctu.")
    c1 = ctu.StatsMemCached(c0)
    run_cached(c1)
    assert len(c1) >= 50
    assert c1["(1, 'a', True)"] == 111
    assert c1["(3, None, False)"] == -17
    assert c1.hits() > 0.0

@pytest.mark.skipif(not has_service(port=6379), reason="no local redis service available for testing")
def test_redis():
    import redis
    c0 = redis.Redis(host="localhost")
    c1 = ctu.RedisCache(c0)
    run_cached(c1)
    assert len(c1) >= 50
    assert c1[(1, 'a', True)] == 111
    assert c1[(3, None, False)] == -17

@pytest.mark.skipif(not has_service(port=6379), reason="no local redis service available for testing")
def test_key_redis():
    import redis
    c0 = redis.Redis(host="localhost")
    c1 = ctu.PrefixedRedisCache(c0, "CacheToolsUtils.")
    run_cached(c1)
    assert len(c1) >= 50
    assert c1[(1, 'a', True)] == 111
    assert c1[(3, None, False)] == -17

@pytest.mark.skipif(not has_service(port=6379), reason="no local redis service available for testing")
def test_stats_redis():
    import redis
    c0 = redis.Redis(host="localhost")
    c1 = ctu.StatsRedisCache(c0)
    run_cached(c1)
    assert len(c1) >= 50
    assert c1[(1, 'a', True)] == 111
    assert c1[(3, None, False)] == -17
    assert c1.hits() > 0.0
