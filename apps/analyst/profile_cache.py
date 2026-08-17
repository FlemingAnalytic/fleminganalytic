"""Cache the dataset profile, which is a pure function of the data.

Profiling 100,000 rows costs about 0.68s: a correlation matrix, a full-frame
duplicate scan, per-column statistics and outlier bounds. Nothing in it
depends on the request, the user or the time - the same frame always produces
the same profile - so recomputing it on every load was pure waste.

It became four times as wasteful when the site moved from one gunicorn worker
to four, because each worker keeps its own session cache and the first request
to reach each of them paid the full cost again. That showed up plainly in the
timings: eight identical pivots returned in 1.15s, 0.06s, 1.19s, then 0.05s
and below, as each worker warmed separately. This cache is on disk, so the
four workers share it and only the first one anywhere pays.

Two keys, because the cheap one is not always available:

  source key    For a file on disk: path, mtime and size. Costs about 0.1ms.
  content hash  For anything derived - a filtered frame, a join, an upload -
                where there is no file to point at. Costs about 80ms on
                100,000 rows, which is still eight times cheaper than
                profiling it.

Invalidation is automatic. The key includes a hash of the profiler's own
source code, so editing DataProfiler invalidates every cached profile without
anyone having to remember to bump a version number. That is the failure this
guards against: a stale cache that silently serves the old shape of an answer
is worse than no cache, and "remember to bump the version" is not a control.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "db", "profile_cache",
)

# Profiles are ~18 KB each. This is a guard against unbounded growth from
# ad-hoc uploads, not a tuned figure.
MAX_ENTRIES = 300

_code_fingerprint: Optional[str] = None
_fingerprint_lock = threading.Lock()


def _profiler_fingerprint(profiler_cls: type) -> str:
    """A hash of the profiler's source, so a code change invalidates the cache."""
    global _code_fingerprint
    if _code_fingerprint is None:
        with _fingerprint_lock:
            if _code_fingerprint is None:
                try:
                    src = inspect.getsource(profiler_cls)
                except (OSError, TypeError):
                    # Can't read the source (frozen, or a C extension). Fall
                    # back to something that at least changes when the class
                    # is replaced, rather than pretending the cache is valid.
                    src = repr(profiler_cls)
                _code_fingerprint = hashlib.sha256(src.encode()).hexdigest()[:12]
    return _code_fingerprint


def file_source_key(path: str) -> Optional[str]:
    """Identity of a file on disk, cheaply. None if it is not there."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    return f"file:{os.path.abspath(path)}:{int(st.st_mtime)}:{st.st_size}"


def content_key(df: pd.DataFrame) -> str:
    """Identity of a frame by its contents, for anything with no file behind it."""
    digest = hashlib.sha256()
    digest.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    # Column names and order change the profile but not the row hashes.
    digest.update("\x00".join(map(str, df.columns)).encode())
    return "content:" + digest.hexdigest()


def _cache_path(key: str, fingerprint: str) -> str:
    name = hashlib.sha256(f"{fingerprint}:{key}".encode()).hexdigest()
    return os.path.join(CACHE_DIR, name + ".json")


def _prune() -> None:
    """Keep the directory bounded. Oldest-accessed go first."""
    try:
        entries = [
            (os.path.getmtime(os.path.join(CACHE_DIR, f)), os.path.join(CACHE_DIR, f))
            for f in os.listdir(CACHE_DIR) if f.endswith(".json")
        ]
    except OSError:
        return
    if len(entries) <= MAX_ENTRIES:
        return
    entries.sort()
    for _, path in entries[:len(entries) - MAX_ENTRIES]:
        try:
            os.remove(path)
        except OSError:
            pass


def profile_df(
    df: pd.DataFrame,
    profiler_cls: type,
    source_key: Optional[str] = None,
    clean: Optional[Callable[[Any], Any]] = None,
) -> Dict[str, Any]:
    """Return the profile for `df`, from disk if it has been computed before.

    `source_key` is an optional cheap identity for the data - use
    file_source_key() when the frame came straight off a file. Without one the
    frame is content-hashed, which is slower but still far cheaper than
    profiling.

    Any failure in the cache falls through to computing the profile. A cache
    is an optimisation; it must never be the reason a request fails.
    """
    fingerprint = _profiler_fingerprint(profiler_cls)

    try:
        key = source_key or content_key(df)
        path = _cache_path(key, fingerprint)
    except Exception as exc:                      # pragma: no cover - defensive
        logger.warning(f"analyst: could not key the profile cache ({exc}); profiling")
        return profiler_cls(df).run_full_profile()

    if os.path.exists(path):
        try:
            with open(path, "r") as fh:
                profile = json.load(fh)
            os.utime(path, None)                  # mark as recently used
            logger.info(f"analyst: profile cache hit for {key[:60]}")
            return profile
        except (OSError, ValueError) as exc:
            logger.warning(f"analyst: unreadable cached profile ({exc}); recomputing")
            try:
                os.remove(path)
            except OSError:
                pass

    started = time.time()
    profile = profiler_cls(df).run_full_profile()
    elapsed = time.time() - started

    # Clean before returning, not just before writing. A hit comes back off
    # disk as plain JSON types; if a miss returned numpy scalars instead, the
    # two paths would hand callers subtly different objects and the difference
    # would only show up once the cache was warm - which is the worst possible
    # time to discover it.
    profile = clean(profile) if clean else profile

    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        # Write to a temp file in the same directory and rename, so a second
        # worker never reads a half-written profile.
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w") as fh:
            json.dump(profile, fh)
        os.replace(tmp, path)
        _prune()
        logger.info(f"analyst: profiled in {elapsed:.2f}s and cached {key[:60]}")
    except (OSError, TypeError, ValueError) as exc:
        logger.warning(f"analyst: could not cache the profile ({exc})")

    return profile


def stats() -> Dict[str, Any]:
    try:
        files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    except OSError:
        return {"entries": 0, "bytes": 0}
    total = 0
    for f in files:
        try:
            total += os.path.getsize(os.path.join(CACHE_DIR, f))
        except OSError:
            pass
    return {"entries": len(files), "bytes": total}
