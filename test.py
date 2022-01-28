#! /usr/bin/env python

import cachetools as ct
import CacheToolsUtils as ctu
import socket
import pytest

def has_service(host="localhost", port=22):
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
    @ct.cached(cache=cache)
    def fun(i: int, s: str) -> int:
        return i + (len(s) if s else 0)
    return fun

def run_cached(cache):
    fun = cached_fun(cache)
    x = 0
    for n in range(10):
        for i in range(5):
            for s in ["a", "b", "c", None]:
                x += int(fun(i, s))  # FIXME typing
    return x

def test_key_ct():
    c0 = ct.TTLCache(maxsize=100, ttl=100)
    cache = ctu.PrefixedCache(c0, "f.")
    x = run_cached(ctu.PrefixedCache(cache, "f."))
    assert x == 550
    assert len(cache) == 20
    assert "f.(0, 'a')" in cache
    assert "f.(4, None)" in cache

def test_stats_ct():
    c0 = ct.TTLCache(maxsize=100, ttl=100)
    cache = ctu.StatsCache(c0)
    x = run_cached(cache)
    # assert x == 550  # FIXME
    assert len(cache) == 20
    assert cache[(4, "a")] == 5
    assert cache[(0, None)] == 0
    assert cache.hits() > 0.7

@pytest.mark.skipif(not has_service(port=11211), reason="no local memcached service available for testing")
def test_key_memcached():
    import pymemcache as pmc
    c0 = pmc.Client(server="localhost")
    cache = ctu.PrefixedMemCached(c0, "CacheToolsUtils.")
    x = run_cached(cache)
    # assert x == 550
    assert len(cache) >= 20
    assert int(cache["(0, 'a')"]) == 1  # FIXME typing
    # assert cache["(3, None)"] == 3  # FIXME typing

@pytest.mark.skipif(not has_service(port=11211), reason="no local memcached service available for testing")
def test_stats_memcached():
    import pymemcache as pmc
    pass

@pytest.mark.skipif(not has_service(port=6379), reason="no local redis service available for testing")
def test_key_redis():
    import redis
    pass

@pytest.mark.skipif(not has_service(port=6379), reason="no local redis service available for testing")
def test_stats_redis():
    import redis
    pass
