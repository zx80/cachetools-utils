# Versions

[Documentation](https://zx80.github.io/cachetools-utils/),
[sources](https://github.com/zx80/cachetools-utils) and
[issues](https://github.com/zx80/cachetools-utils/issues)
are hosted on [GitHub](https://github.com).
Install [package](https://pypi.org/project/CacheToolsUtils/) from
[PyPI](https://pypi.org/).

## TODO or NOT…

- write a tutorial!
- write recipes!
- add a `close`?
- rename `hits` as `hit_rate`?
- add other efficiency statistics?
- add ability to reconnect if an external cache fails?
  this could be for redis or memcached?
  Maybe the existing client can do that with appropriate options?
- `cached`: add `contains` and `delete` parameters to change names?
- I cannot say that all this is clear wrt `str` vs `bytes` vs whatever…
- think again the encryption design to allow persistant ciphers?
  this would require to change the `iv` at least?

## ? on ?

Add _PyPy 3.11_, _Python 3.13t_ and _Python 3.14t_ to GitHub CI.

As of 2025-03-07 freethreaded is a pain because `cryptography` does not install, thus only partial testing is enabled.
The dependency comes from `pycryptodome` _and_ `types-redis`.

## 10.3 on 2025-03-05

Add `AutoPrefixedCache`.
Update doc action versions.

## 10.2 on 2024-12-24

Allow to change the cipher within _Salsa20_, _AES-128-CBC_ and _ChaCha20_.

## 10.1 on 2024-12-08

Add optional integrity check to `EncryptedCache`.
Code cleanup.
Reorder memcached serialization formats.

## 10.0 on 2024-12-07

Add `full_hash_key` function.
Add `EncryptedCache`, `ToBytesCache` and `BytesCache`.

## 9.3 on 2024-12-06

Add `opts` to provide additional parameters to cached when wrapping methods
and functions.

## 9.2 on 2024-11-29

Simpler and more compact json cache key function.

## 9.1 on 2024-11-28

Improve documentation.
Add experimental `json_key` and `hash_json_key` cache key functions.

## 9.0 on 2024-10-27

Add `stats` method to return a convenient `dict` of statistics.
Improve type declarations.
Add some tests.
Test with (future) Python 3.14.
Fix doc typo.

## 8.6 on 2024-08-03

Add license section to README.
Add `ruff` pass.
Add _Pypy 3.10_ and _Python 3.13_ to CI.

## 8.5 on 2024-02-03

Add missing MutableMapping inheritance.
Update GitHub action versions.
Drop type alias.

## 8.4 on 2024-01-20

Improved documentation.
Improved type declarations with `pyright`, added to CI.

## 8.3 on 2023-11-12

Fix `TwoLevelCache` verbosity.
Add `DebugCache` for helping debug.
Sort keys on JSON dumps.
Upgrade GitHub actions.
Test with Python *3.12*.
Improved documentation.

## 8.2 on 2023-08-27

Add more method forwarding to `LockedCache`, for `Redis`.
Fix `pymemcache` package name in documentation.

## 8.1 on 2023-08-27

Use extended `cached` for `cacheMethods` and `cacheFunctions`.

## 8.0 on 2023-08-26

Add `LockedCache` class for shared cache and threading.
Add `DictCache` class for dict-based cache.
Add resiliency option to `TwoLevelCache`.
Add extended `cached` decorator with `in` and `del` support.
Use base85 instead of base64 for MemCached keys.
Improved documentation following diátaxis advices.
Hide some private internals.

## 7.0 on 2023-06-17

Switch to `pyproject.toml`.
Require Python *3.10+* for easier typing.

## 6.0 on 2023-03-19

Improved documentation for `github.io`.
Add a `pyproject.toml` (stupid) file.

## 5.1 on 2022-11-12

Test with Python *3.12*.

## 5.0 on 2022-09-11

Add `pymarkdown` check.
Add GitHub CI configuration.
Add a badge.

## 4.3 on 2022-09-07

Fix missing key filtering for `Redis`'s `get`, `set` and `delete`.
Also forward `in` in Mixin.

## 4.2 on 2022-08-05

Fix minor typo in a badge.

## 4.1 on 2022-08-05

Code reformating.
Improved documentation.
Improved checks.
Improved Makefile.

## 4.0 on 2022-03-13

Remove `StatsRedisCache` and `StatsMemCached` by moving the `hits()` method
to `RedisCache` and `MemCached`, respectively.
The two classes still exist for upward compatibility, but are deprecated.
Improve test coverage, now only 4 not-covered lines.
Improve documentation.

## 3.0 on 2022-03-06

Use simpler `kwargs` approach for caching methods and functions.
Add a `gen` parameter for caching methods and functions.
Improve documentation.

## 2.0 on 2022-02-24

Add `cacheMethods` and `cacheFunctions`.
Improve documentation.
100% coverage test.

## 1.1.0 on 2022-01-30

Improve documentation.
Add `TwoLevelCache`.
Add 100% coverage test.

## 1.0.0 on 2022-01-29

Add `set`, `get` and `delete` forwarding to `RedisCache`, so that redis
classes can be stacked.

## 0.9.0 on 2022-01-29

Initial version extracted from another project.
