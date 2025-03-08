#! /usr/bin/env python

import sys
import socket
import importlib
import random
import threading
import cachetools as ct
import CacheToolsUtils as ctu
import pytest
import logging

logging.basicConfig()
log = logging.getLogger("ctu-test")
# log.setLevel(logging.DEBUG)

SECRET = b"incredible secret key for testing encrypted cache..."

def has_service(host="localhost", port=22) -> bool:
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

def has_package(pkg_name: str) -> bool:
    try:
        importlib.import_module(pkg_name)
        return True
    except ModuleNotFoundError:
        return False

def cached_fun(cache, cached=ct.cached, key=ct.keys.hashkey):
    """return a cached function with basic types."""

    @cached(cache=cache, key=key)
    def fun(i: int, s: str|None, b: bool) -> int:
        return i + (10 * len(s) if s is not None else -20) + (100 if b else 0)

    return fun

# reset cache contents and stats
def reset_cache(cache):
    try:
        cache.clear()
    except:  # fails on redis
        pass
    try:
        if hasattr(cache, "_cache") and hasattr(cache._cache, "reset"):
            cache._cache.reset()
    except:  # fails on redis
        pass
    try:
        if hasattr(cache, "_cache2") and hasattr(cache._cache2, "reset"):
            cache._cache2.reset()
    except:  # fails on redis
        pass

def run_cached_keys(cache):

    for cached in (ct.cached, ctu.cached):
        for keyfun in (ct.keys.hashkey, ct.keys.typedkey, ctu.hash_json_key, ctu.json_key):
            reset_cache(cache)
            fun = cached_fun(cache, cached, key=keyfun)
            x = 0
            for n in range(10):
                for i in range(5):
                    for s in ["a", "bb", "ccc", "", None]:
                        for b in [False, True]:
                            v = fun(i, s, b=b)
                            # log.debug(f"fun{(i, s, b)} = {v} {type(v)}")
                            x += v
            assert x == 30000

def run_cached(cache, key=ct.keys.hashkey):
    """run something on a cached function."""

    for cached in (ct.cached, ctu.cached):
        # reset cache contents and stats
        reset_cache(cache)
        # NOTE we probably trigger a double json encoding in some tests.
        fun = cached_fun(cache, cached, key=key)
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
    # str keys and values
    cache[KEY] = VAL
    # assert KEY in cache
    assert cache[KEY] == VAL
    del cache[KEY]
    # assert KEY not in cache
    try:
        val = cache[KEY]
        pytest.fail("should raise KeyError")
    except Exception as e:
        assert isinstance(e, KeyError)
    # int value
    cache[KEY] = 65536
    # assert KEY in cache
    assert cache[KEY] == 65536
    del cache[KEY]
    # FIXME memcached error
    # assert KEY not in cache

def setgetdel_bytes(cache):
    key, val, cst = KEY.encode("UTF8"), VAL.encode("UTF8"), b"FOO"
    cache.setdefault(key, val)
    assert key in cache
    assert cache.get(key) == val
    assert cache.setdefault(key, cst) == val
    assert cache.pop(key) == val
    assert key not in cache
    assert cache.get(key, cst) == cst
    assert cache.pop(key, cst) == cst
    try:
        cache.pop(key)
        pytest.fail("should raise KeyError")
    except KeyError as e:
        assert True, "KeyError was raised"

def test_key_ct():
    c0 = ct.TTLCache(maxsize=100, ttl=100)
    c1 = ctu.PrefixedCache(c0, "f.")
    c2 = ctu.PrefixedCache(c0, "f.")
    c3 = ctu.PrefixedCache(c0, "g.")
    run_cached(c1)
    run_cached(c2)
    assert len(c0) == 50
    assert "f.(0, 'a', False)" in c0
    assert c1["(3, 'bb', True)"] == 123
    assert "f.(4, None, True)" in c0
    assert c2["(4, 'ccc', True)"] == 134
    run_cached(c3)
    assert len(c0) == 100
    assert c3["(2, '', True)"] == 102
    c0.clear()
    setgetdel(c0)
    setgetdel(c1)
    setgetdel(c2)
    setgetdel(c3)
    for key in c0:
        assert key[0] in ("f", "g") and key[1] == "."
    for key in c3:
        assert key[0] in ("f", "g") and key[1] == "."
    setgetdel_bytes(c0)
    setgetdel_bytes(c1)
    setgetdel_bytes(c2)
    setgetdel_bytes(c3)

def test_stats_ct():
    c0 = ct.TTLCache(maxsize=100, ttl=100)
    cache = ctu.StatsCache(c0)
    run_cached(cache, key=ctu.json_key)
    assert len(cache) == 50
    # NOTE keys are jsonified in run_cached
    assert cache['[4,"a",true]'] == 114
    assert cache['[0,null,false]'] == -20
    assert cache.hits() > 0.8
    assert isinstance(cache.stats(), dict)
    cache.clear()
    setgetdel(c0)
    setgetdel(cache)

def test_caches():
    n = 0
    for Cache in (ct.LRUCache, ct.FIFOCache, ct.LFUCache, ct.RRCache):
        n += 1
        cache = Cache(maxsize=1024)
        run_cached_keys(cache)
    assert n == 4

@pytest.mark.skipif(
    not has_service(port=11211) or not has_package("Crypto"),
    reason="requires memcached service and Crypto module",
)
def test_memcached():
    import pymemcache as pmc

    mc = pmc.Client(server="localhost", serde=ctu.JsonSerde())
    mcc = ctu.MemCached(mc)
    ec = ctu.EncryptedCache(mcc, SECRET)
    cache = ctu.ToBytesCache(ec)
    run_cached(cache)
    assert len(cache) >= 50
    assert ec[b'[1,"a",true]'] == b"111"
    assert ec[b'[3,null,false]'] == b"-17"
    assert isinstance(cache.stats(), dict)

@pytest.mark.skipif(
    not has_service(port=11211),
    reason="no local memcached service available for testing",
)
def test_key_memcached():
    import pymemcache as pmc

    c0 = pmc.Client(server="localhost", serde=ctu.JsonSerde())
    c1 = ctu.PrefixedMemCached(c0, "CacheToolsUtils.")
    run_cached(c1, key=ctu.json_key)
    assert len(c1) >= 50
    assert c1['[1,"a",true]'] == 111
    assert c1['[3,null,false]'] == -17

@pytest.mark.skipif(
    not has_service(port=11211),
    reason="no local memcached service available for testing",
)
def test_stats_memcached():
    import pymemcache as pmc

    c0 = pmc.Client(server="localhost", serde=ctu.JsonSerde(), key_prefix=b"ctu.")
    c1 = ctu.MemCached(c0)
    run_cached(c1, key=ctu.json_key)
    assert len(c1) >= 50
    assert c1['[1,"a",true]'] == 111
    assert c1['[3,null,false]'] == -17
    assert c1.hits() > 0.0
    assert isinstance(c1.stats(), dict)
    setgetdel(c0)
    setgetdel(c1)

@pytest.mark.skipif(
    not has_service(port=6379) or not has_package("Crypto"),
    reason="requires redis service and Crypto module"
)
def test_redis():
    import redis
    import threading

    c0 = redis.Redis(host="localhost")
    c0.flushdb()

    c1 = ctu.RedisCache(c0, raw=True)
    c2 = ctu.EncryptedCache(c1, SECRET, hsize=20, csize=4)
    c3 = ctu.ToBytesCache(c2)
    c4 = ctu.DebugCache(c3, log)
    cache = ctu.LockedCache(c4, threading.RLock())
    run_cached(cache)
    assert len(cache) >= 50
    assert cache[(1, 'a', True)] == 111
    assert cache[(3, None, False)] == -17
    setgetdel(cache)
    try:
        cache.__iter__()
        pytest.fail("not supported")
    except Exception as e:
        assert "not implemented yet" in str(e)

@pytest.mark.skipif(
    not has_service(port=6379), reason="no local redis service available for testing"
)
def test_key_redis():
    import redis

    c0 = redis.Redis(host="localhost")
    c1 = ctu.PrefixedRedisCache(c0, "CacheToolsUtils.")
    run_cached(c1)
    assert len(c1) >= 50
    assert c1["(1, 'a', True)"] == 111
    assert c1["(3, None, False)"] == -17
    setgetdel(c1)
    c1.set("Hello", "World!")
    assert c1["Hello"] == c1.get("Hello")
    c1.delete("Hello")
    assert "Hello" not in c1

@pytest.mark.skipif(
    not has_service(port=6379), reason="no local redis service available for testing"
)
def test_stats_redis():
    import redis

    c0 = redis.Redis(host="localhost")
    c1 = ctu.StatsRedisCache(c0)
    run_cached(c1, key=ctu.json_key)
    assert len(c1) >= 50
    assert c1['[1,"a",true]'] == 111
    assert c1['[3,null,false]'] == -17
    assert c1.hits() > 0.0
    assert isinstance(c1.stats(), dict)
    setgetdel(c1)

@pytest.mark.skipif(
    not has_service(port=6379), reason="no local redis service available for testing"
)
def test_stacked_redis():
    import redis

    c0 = redis.Redis(host="localhost")
    c1 = ctu.RedisCache(c0)
    c2 = ctu.StatsRedisCache(c1)
    c3 = ctu.PrefixedRedisCache(c2, "CacheToolsUtilsTests.")
    run_cached(c3)
    assert len(c3) >= 50
    assert c2.hits() > 0.0
    assert isinstance(c2.stats(), dict)
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
    assert isinstance(c1s.stats(), dict)
    assert c0s.hits() > 0.8
    assert isinstance(c0s.stats(), dict)
    assert c2.hits() > 0.0
    assert isinstance(c2.stats(), dict)
    c2.clear()
    setgetdel(c0)
    setgetdel(c1)
    setgetdel(c0s)
    setgetdel(c1s)
    setgetdel(c2)

def test_two_level_ok():
    # front cache is too small, always fallback
    c0 = ct.LRUCache(200)
    c1 = ct.LFUCache(100)
    c0s = ctu.StatsCache(c0)
    c1s = ctu.StatsCache(c1)
    c2 = ctu.TwoLevelCache(c1s, c0s)
    run_cached(c2)
    assert len(c1s) == 50
    assert len(c0s) == 50
    assert c0s._reads == 50
    # assert c0s._writes == 50
    assert c0s._writes == 0
    assert c1s._reads == 500
    assert c1s.hits() == 0.9
    assert isinstance(c1s.stats(), dict)
    assert c0s.hits() == 1.0
    assert isinstance(c0s.stats(), dict)
    assert c2.hits() > 0.0
    assert isinstance(c2.stats(), dict)
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

def test_twolevel_bad_stats():
    c0 = ctu.DictCache()
    c1 = ctu.DictCache()
    c2 = ctu.TwoLevelCache(c0, c1)
    assert isinstance(c2.stats(), dict)
    assert c2.hits() is None


class Stuff:
    """Test class with cacheable methods."""

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return f"Object {self._name}"

    def sum_n2(self, n: int):
        if n < 1:
            return 0
        else:
            return n * n + self.sum_n2(n - 1)

    def sum_n1(self, n: int):
        if n < 0:
            return 0
        else:
            return n + self.sum_n1(n - 1)


def test_methods():
    s = Stuff("test_methods")
    c = ct.TTLCache(1024, ttl=60)
    cs = ctu.StatsCache(c)
    ctu.cacheMethods(cs, s, opts={"key": ctu.json_key}, sum_n1="1.", sum_n2="2.")
    n2 = s.sum_n2(128)
    n1 = s.sum_n1(128)
    for i in range(1, 128):
        n = s.sum_n2(i) + s.sum_n1(i)
        n = s.sum_n2(i) + s.sum_n1(i)
    assert len(c) == 259
    assert cs.hits() > 0.6
    assert isinstance(cs.stats(), dict)
    ctu.cacheMethods(cs, s, sum_n1="x.")
    try:
        ctu.cacheMethods(cs, s, no_such_method="?.")
        pytest.fail("exception must be raised")
    except Exception as e:
        assert "missing method" in str(e)

def sum_n2(n: int):
    return n * n + sum_n2(n - 1) if n >= 1 else 0

def test_functions():
    c = ct.TTLCache(1024, ttl=60.0)
    cs = ctu.StatsCache(c)
    ctu.cacheFunctions(cs, globals(), sum_n2="2.")
    ctu.cacheFunctions(cs, globals(), sum_n2="2.")
    assert hasattr(sum_n2, "__wrapped__")
    n2 = sum_n2(128)
    for i in range(1, 128):
        n = sum_n2(i) + sum_n2(i) + sum_n2(i)
    assert len(c) == 129
    assert cs.hits() > 0.7
    assert isinstance(cs.stats(), dict)

def test_corners():
    # _MutMapMix coverage
    c = ctu.DictCache()
    cs = ctu.StatsCache(c)
    run_cached(cs)
    assert len(cs) > 0
    cs["foo-bla-khan"] = 1
    assert "foo-bla-khan" in cs
    del cs["foo-bla-khan"]
    assert "foo-bla-khan" not in cs
    # raise JsonSerde flag error
    try:
        js = ctu.JsonSerde()
        js.deserialize("foo", "bla", 42)
        pytest.fail("exception must be raised")
    except Exception as e:
        assert "Unknown serialization format" in str(e)


class BrokenCache():
    """All Error Cache, for testing purposes."""

    def __setitem__(self, key, val):
        raise Exception("oops!")

    def __getitem__(self, key):
        raise Exception("oops!")

    def __delitem__(self, key):
        raise Exception("oops!")

def test_resilience():
    d = ctu.DictCache()
    b = BrokenCache()

    # no resilience (default)
    c = ctu.TwoLevelCache(d, b, False)
    try:
        c["foo"] = "bla"
        pytest.fail("must raise an exception")
    except Exception:
        assert True, "expecting exception"
    try:
        c["foo"]
        pytest.fail("must raise an exception")
    except Exception:
        assert True, "expecting exception"
    try:
        del c["foo"]
        pytest.fail("must raise an exception")
    except Exception:
        assert True, "expecting exception"

    # activate resilience
    c._resilient = True
    c["foo"] = "bla"
    assert c["foo"] == "bla"
    del c["foo"]

def test_locked():
    import threading
    c = ctu.LockedCache(ctu.DictCache(), threading.Lock())
    c["hello"] = "world!"
    assert "hello" in c
    assert c["hello"] == "world!"
    del c["hello"]
    assert "hello" not in c
    # just for coverage
    try:
        c.hits() == 0.0
    except:
        pass
    try:
        c.reset()
    except:
        pass

def test_cached():
    cache = ctu.StatsCache(ctu.DictCache())
    @ctu.cached(cache)
    def cached(s: str, i: int):
        return s[i]
    assert not cached.cache_in("hello", 4)
    assert cached("hello", 4) == "o"
    cached("hello", 4)
    assert cached.cache_in("hello", 4)
    assert cache.hits() == 0.5
    assert isinstance(cache.stats(), dict)
    cached.cache_del("hello", 4)
    assert not cached.cache_in("hello", 4)

def test_debug():
    log = logging.getLogger("debug-test")
    log.setLevel(logging.DEBUG)
    cache = ctu.DebugCache(ctu.StatsCache(ctu.DictCache()), log, "test_debug")
    run_cached(cache)
    cache["Hello"] = "World!"
    assert "Hello" in cache
    assert len(cache) > 0
    assert cache.hits() > 0.0
    assert isinstance(cache.stats(), dict)
    has_hello = False
    for k in iter(cache):
        if k == "Hello":
            has_hello = True
    assert has_hello
    del cache["Hello"]
    assert "Hello" not in cache

def test_cache_key():
    assert ctu.json_key(1, "hi") == '[1,"hi"]'
    assert str(ctu.hash_json_key(1, "hi")) == '[1,"hi"]'
    assert ctu.json_key(1, hi="hello") == '{"*":[1],"**":{"hi":"hello"}}'
    assert ctu.json_key(hi="bj") == '{"**":{"hi":"bj"}}'
    assert ctu.full_hash_key("Hello World!") == "j#jQnvD$Vrm{P2s(T`v8"

@pytest.mark.skipif(not has_package("Crypto"), reason="module Crypto is required")
def test_encrypted_cache():
    # available ciphers
    CIPHERS = [ "Salsa20", "AES-128-CBC", "ChaCha20" ]

    loops = 0
    for cipher in CIPHERS:
        # bytes
        actual = ctu.DictCache()
        cache = ctu.EncryptedCache(actual, SECRET, csize=1, cipher=cipher)
        cache[b"Hello"] = b"World!"
        assert b"Hello" in cache
        assert cache[b"Hello"] == b"World!"
        # bad checksum
        assert len(actual) == 1
        k = list(actual.keys())[0]
        actual[k] = bytes([(actual[k][0] + 42) % 256]) + actual[k][1:]
        try:
            _ = cache[b"Hello"]
            pytest.fail("must raise an exception")
        except KeyError as ke:
            assert "invalid encrypted value" in str(ke)
        del cache[b"Hello"]
        assert b"Hello" not in cache
        # strings
        scache = ctu.ToBytesCache(cache)
        scache["Hello"] = "World!"
        assert "Hello" in scache
        assert scache["Hello"] == "World!"
        del scache["Hello"]
        # bytes again
        bcache = ctu.BytesCache(scache)
        bcache[b"Hello"] = b"World!"
        assert b"Hello" in bcache
        assert bcache[b"Hello"] == b"World!"
        del bcache[b"Hello"]
        assert b"Hello" not in bcache
        loops += 1
    # check that we looped as expected
    assert loops == len(CIPHERS)
    # just for coverage
    try:
        ctu._Cipher("foo")
        pytest.fail("must raise an exception")
    except Exception as e:
        assert "unexpected" in str(e)

def test_autoprefix_cache():
    cache = ctu.DictCache()

    @ctu.cached(cache=ctu.AutoPrefixedCache(cache))
    def p1(i: int):
        return i + 1

    @ctu.cached(cache=ctu.AutoPrefixedCache(cache))
    def m1(i: int):
        return i - 1

    assert len(cache) == 0
    assert p1(0) == 1 and p1(41) == 42 and p1(2) == 3 and p1(0) == 1
    assert len(cache) == 3
    assert m1(1) == 0 and m1(43) == 42 and m1(2) == 1 and m1(43) == 42
    assert len(cache) == 6
    assert p1(0) == 1 and p1(41) == 42 and p1(2) == 3 and p1(0) == 1
    assert m1(1) == 0 and m1(43) == 42 and m1(2) == 1 and m1(43) == 42
    assert len(cache) == 6
    assert all("." in k for k in cache._cache.keys())
    prefixes = set(k.split(".", 1)[0] for k in cache._cache.keys())
    assert len(prefixes) == 2
    params = set(k.split(".", 1)[1] for k in cache._cache.keys())
    assert len(params) == 5  # 0, 41, 2, 1, 43
    values = set(cache._cache.values())
    assert len(values) == 4  # 1, 42, 3, 0

    try:
        cache = ctu.AutoPrefixedCache(cache, method="bad-method")
        pytest.fail("must raise an exception")
    except Exception as e:
        assert "method: bad-method" in str(e)

def run_thread(cache, nthreads):

    # direct tests
    cache.clear()
    cache.reset()
    assert len(cache) == 0

    @ctu.cached(cache=ctu.AutoPrefixedCache(cache))
    def repeat(s: str, n: int) -> str:
        return s * n

    @ctu.cached(cache=ctu.AutoPrefixedCache(cache))
    def banged(s: str, n: int) -> str:
        return repeat(s, n) + "!"

    assert banged("a", 3) == "aaa!"  # +2 entries
    assert repeat("a", 3) == "aaa"   # hit
    assert banged("a", 3) == "aaa!"  # hit
    assert cache.hits() == 0.5

    # threaded tests
    cache.clear()
    cache.reset()
    assert len(cache) == 0

    barrier = threading.Barrier(nthreads, timeout=2)

    LS, LI = ["a", "b", "c", "d"], list(range(4))

    def run():
        name = threading.current_thread().name
        log.debug(f"thread start: {name}")
        ls, li = LS.copy(), LI.copy()
        random.shuffle(ls)
        random.shuffle(li)
        barrier.wait()
        for s in ls:
            for n in li:
                barrier.wait()
                assert banged(s, n) == s * n + "!"
        barrier.wait()
        log.debug(f"thread end: {name}")

    threads = [ threading.Thread(target=run, name=f"thread {i}") for i in range(nthreads) ]
    list(map(lambda t: t.start(), threads))
    list(map(lambda t: t.join(), threads))

    # log.info(f"nthreads={nthreads} stats={cache.stats()}")

    assert len(cache) == 32
    # 16 * 2 gets-no-hit + 16 * (nthreads - 1) get-with-hit
    hits = (nthreads - 1) / (nthreads + 1)
    # NOTE hit ratio is not deterministic
    assert 0.75 * hits < cache.hits() <= hits

def test_threads():
    cache = ctu.LockedCache(ctu.StatsCache(ctu.DictCache()), threading.RLock())
    run_thread(cache, 4)
    del cache

def test_nogil():
    try:
        if sys._is_gil_enabled():
            pytest.skip("gil is enabled")
    except AttributeError as e:
        assert "_is_gil_enabled" in str(e)
        pytest.skip("nogil not supported")

    assert not sys._is_gil_enabled()

    cache = ctu.LockedCache(ctu.StatsCache(ctu.DictCache()), threading.Lock())
    run_thread(cache, 4)
    del cache

    assert not sys._is_gil_enabled()
