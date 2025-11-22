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

- switch documentation to MkDocs.
- switch docstrings to markdown.
- use SPDX licensing format.
- update GitHub CI versions.
- fix tests wrt to LFU behavior change.

## 10.4 on 2025-03-08

- collect tests (contains) stats.
- add _PyPy 3.11_, _Python 3.13t_ and _Python 3.14t_ to GitHub CI.
- improve documentation.

As of 2025-03-07 freethreaded is a pain because `cryptography` does not install,
thus only partial testing is enabled.
The dependency comes from `pycryptodome` _and_ `types-redis`.

## 10.3 on 2025-03-05

- add `AutoPrefixedCache`.
- update doc action versions.

## 10.2 on 2024-12-24

- allow to change the cipher within _Salsa20_, _AES-128-CBC_ and _ChaCha20_.

## 10.1 on 2024-12-08

- add optional integrity check to `EncryptedCache`.
- code cleanup.
- reorder memcached serialization formats.

## 10.0 on 2024-12-07

- add `full_hash_key` function.
- add `EncryptedCache`, `ToBytesCache` and `BytesCache`.

## 9.3 on 2024-12-06

- add `opts` to provide additional parameters to cached when wrapping methods and functions.

## 9.2 on 2024-11-29

- simpler and more compact json cache key function.

## 9.1 on 2024-11-28

- improve documentation.
- add experimental `json_key` and `hash_json_key` cache key functions.

## 9.0 on 2024-10-27

- add `stats` method to return a convenient `dict` of statistics.
- improve type declarations.
- add some tests.
- test with (future) Python 3.14.
- fix doc typo.

## 8.6 on 2024-08-03

- add license section to README.
- add `ruff` pass.
- add _Pypy 3.10_ and _Python 3.13_ to CI.

## 8.5 on 2024-02-03

- add missing MutableMapping inheritance.
- update GitHub action versions.
- drop type alias.

## 8.4 on 2024-01-20

- improved documentation.
- improved type declarations with `pyright`, added to CI.

## 8.3 on 2023-11-12

- fix `TwoLevelCache` verbosity.
- add `DebugCache` for helping debug.
- sort keys on JSON dumps.
- upgrade GitHub actions.
- test with Python *3.12*.
- improved documentation.

## 8.2 on 2023-08-27

- add more method forwarding to `LockedCache`, for `Redis`.
- fix `pymemcache` package name in documentation.

## 8.1 on 2023-08-27

- use extended `cached` for `cacheMethods` and `cacheFunctions`.

## 8.0 on 2023-08-26

- add `LockedCache` class for shared cache and threading.
- add `DictCache` class for dict-based cache.
- add resiliency option to `TwoLevelCache`.
- add extended `cached` decorator with `in` and `del` support.
- use base85 instead of base64 for MemCached keys.
- improved documentation following diátaxis advices.
- hide some private internals.

## 7.0 on 2023-06-17

- switch to `pyproject.toml`.
- require Python *3.10+* for easier typing.

## 6.0 on 2023-03-19

- improved documentation for `github.io`.
- add a `pyproject.toml` (stupid) file.

## 5.1 on 2022-11-12

- test with Python *3.12*.

## 5.0 on 2022-09-11

- add `pymarkdown` check.
- add GitHub CI configuration.
- add a badge.

## 4.3 on 2022-09-07

- fix missing key filtering for `Redis`'s `get`, `set` and `delete`.
- also forward `in` in Mixin.

## 4.2 on 2022-08-05

- fix minor typo in a badge.

## 4.1 on 2022-08-05

- code reformating.
- improved documentation.
- improved checks.
- improved Makefile.

## 4.0 on 2022-03-13

- remove `StatsRedisCache` and `StatsMemCached` by moving the `hits()` method
  to `RedisCache` and `MemCached`, respectively.
- the two classes still exist for upward compatibility, but are deprecated.
- improve test coverage, now only 4 not-covered lines.
- improve documentation.

## 3.0 on 2022-03-06

- use simpler `kwargs` approach for caching methods and functions.
- add a `gen` parameter for caching methods and functions.
- improve documentation.

## 2.0 on 2022-02-24

- add `cacheMethods` and `cacheFunctions`.
- improve documentation.
- 100% coverage test.

## 1.1.0 on 2022-01-30

- improve documentation.
- add `TwoLevelCache`.
- add 100% coverage test.

## 1.0.0 on 2022-01-29

- add `set`, `get` and `delete` forwarding to `RedisCache`, so that redis
  classes can be stacked.

## 0.9.0 on 2022-01-29

- initial version extracted from another project.
