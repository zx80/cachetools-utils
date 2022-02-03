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

KEY, VAL = "hello-world!", "Hello World…"

def setgetdel(cache):
    # str value
    cache[KEY] = VAL
    assert cache[KEY] == VAL
    del cache[KEY]
    try:
       val = cache[KEY]
       assert False, "should raise KeyError"
    except Exception as e:
       assert isinstance(e, KeyError)
    # int value
    cache[KEY] = 65536
    assert cache[KEY] == 65536
    del cache[KEY]
    # assert KEY not in cache

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
    c0.clear()
    setgetdel(c0)
    setgetdel(c1)
    setgetdel(c2)
    setgetdel(c3)
    for key in c0:
        assert key[0] in ("f", "g") and key[1] == "."
    for key in c3:
        assert key[0] in ("f", "g") and key[1] == "."

def test_stats_ct():
    c0 = ct.TTLCache(maxsize=100, ttl=100)
    cache = ctu.StatsCache(c0)
    run_cached(cache)
    assert len(cache) == 50
    assert cache[(4, "a", True)] == 114
    assert cache[(0, None, False)] == -20
    assert cache.hits() > 0.8
    cache.clear()
    setgetdel(c0)
    setgetdel(cache)

@pytest.mark.skipif(not has_service(port=11211), reason="no local memcached service available for testing")
def test_memcached():
    import pymemcache as pmc
    c0 = pmc.Client(server="localhost", serde=ctu.JsonSerde())
    c1 = ctu.MemCached(c0)
    run_cached(c1)
    assert len(c1) >= 50
    assert c1["(1, 'a', True)"] == 111
    assert c1["(3, None, False)"] == -17
    assert isinstance(c1.stats(), dict)

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
    setgetdel(c0)
    setgetdel(c1)

@pytest.mark.skipif(not has_service(port=6379), reason="no local redis service available for testing")
def test_redis():
    import redis
    c0 = redis.Redis(host="localhost")
    c1 = ctu.RedisCache(c0)
    run_cached(c1)
    assert len(c1) >= 50
    assert c1[(1, 'a', True)] == 111
    assert c1[(3, None, False)] == -17
    setgetdel(c1)
    try:
        c1.__iter__()
        assert False, "should raise an Exception"
    except Exception as e:
        assert "not implemented yet" in str(e)

@pytest.mark.skipif(not has_service(port=6379), reason="no local redis service available for testing")
def test_key_redis():
    import redis
    c0 = redis.Redis(host="localhost")
    c1 = ctu.PrefixedRedisCache(c0, "CacheToolsUtils.")
    run_cached(c1)
    assert len(c1) >= 50
    assert c1[(1, 'a', True)] == 111
    assert c1[(3, None, False)] == -17
    setgetdel(c1)

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
    setgetdel(c1)

@pytest.mark.skipif(not has_service(port=6379), reason="no local redis service available for testing")
def test_stacked_redis():
    import redis
    c0 = redis.Redis(host="localhost")
    c1 = ctu.RedisCache(c0)
    c2 = ctu.StatsRedisCache(c1)
    c3 = ctu.PrefixedRedisCache(c2, "CacheToolsUtilsTests.")
    run_cached(c3)
    assert len(c3) >= 50
    assert c2.hits() > 0.0
    setgetdel(c1)
    setgetdel(c2)
    setgetdel(c3)

def test_two_level_small():
    # front cache is too small, always fallback
    c0 = ct.TTLCache(100, ttl=60)
    c1 = ct.LFUCache(10)
    c0s = ctu.StatsCache(c0)
    c1s = ctu.StatsCache(c1)
    c2 = ctu.TwoLevelCache(c1s, c0s)
    run_cached(c2)
    assert len(c1s) == 10
    assert len(c0s) == 50
    assert c0s._reads == c1s._reads
    assert c1s.hits() == 0.0
    assert c0s.hits() > 0.8
    c2.clear()
    setgetdel(c0)
    setgetdel(c1)
    setgetdel(c0s)
    setgetdel(c1s)
    setgetdel(c2)

def test_two_level_ok():
    # front cache is too small, always fallback
    c0 = ct.LRUCache(200)
    c1 = ct.MRUCache(100)
    c0s = ctu.StatsCache(c0)
    c1s = ctu.StatsCache(c1)
    c2 = ctu.TwoLevelCache(c1s, c0s)
    run_cached(c2)
    assert len(c1s) == 50
    assert len(c0s) == 50
    assert c0s._reads == 50
    assert c0s._writes == 50
    assert c1s._reads == 500
    assert c1s.hits() == 0.9
    assert c0s.hits() == 0.0
    c2.clear()
    setgetdel(c0)
    setgetdel(c1)
    setgetdel(c0s)
    setgetdel(c1s)
    setgetdel(c2)
    # trigger a level-2 miss
    c2[KEY] = VAL
    del c0s[KEY]
    del c2[KEY]


class Stuff:

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return f"Object {self._name}"

    def sum_n2(self, n: int):
        if n < 1:
            return 0
        else:
            return n*n + self.sum_n2(n-1)

    def sum_n1(self, n: int):
        if n < 0:
            return 0
        else:
            return n + self.sum_n1(n-1)

def test_methods():
    s = Stuff("test_methods")
    c = ct.TTLCache(1024, ttl=60)
    cs = ctu.StatsCache(c)
    ctu.cacheMethods(cs, s, {"sum_n1": "1.", "sum_n2": "2."})
    n2 = s.sum_n2(128)
    n1 = s.sum_n1(128)
    for i in range(1, 128):
        n = s.sum_n2(i) + s.sum_n1(i)
        n = s.sum_n2(i) + s.sum_n1(i)
    assert len(c) == 259
    assert cs.hits() > 0.6
    ctu.cacheMethods(cs, s, {"sum_n1": "x."})
    try:
        ctu.cacheMethods(cs, s, {"no-such-method": "?."})
        assert False, "exception must be raised"
    except Exception as e:
        assert "missing method" in str(e)
