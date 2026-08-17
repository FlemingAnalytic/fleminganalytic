"""A session store that survives a restart and is safe across worker processes.

Why this exists
---------------
Every application on this domain shared a single gunicorn worker, because
several of them kept their sessions in a module-global dict. A dict lives in
one process's memory, so a second worker would have its own copy: a chess game
started on worker A would 404 on worker B, and a logged-in user would be
logged out at random depending on which process caught the request. Nothing
would fail loudly - it would just be intermittently wrong, which is worse.

`workers = 1` was the workaround. This module is the fix.

Concurrency: optimistic, not locked
-----------------------------------
The obvious implementation - hold a SQLite write transaction from load to save
- is wrong here, and it is worth saying why so nobody "simplifies" it back.
SQLite locks the whole database for writes, not the row. The chess AI search
takes seconds, so holding a write transaction across it would block writes for
every session of every application on the domain. That trades one bottleneck
for another.

So each row carries a version. `checkout()` reads without a transaction, hands
you the data to modify for as long as you like, then writes back only if the
version is still what it was. If another request modified the same session in
the meantime the write is refused and `SessionConflict` is raised. Writes stay
sub-millisecond, unrelated sessions never contend, and a genuine double-submit
on one session is reported rather than silently losing a move.

Values must be JSON-serialisable. Anything richer is the caller's job to
encode - see the chess board, which is stored as its move list and replayed,
so that threefold-repetition detection survives the round trip. A FEN string
alone would have lost it.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "sessions.db")

_local = threading.local()
_init_lock = threading.Lock()
_initialised = False


class SessionConflict(RuntimeError):
    """Another request modified this session while we were working on it."""


def _connect() -> sqlite3.Connection:
    """One connection per thread. SQLite connections are not thread-safe, and
    FastAPI runs sync endpoints in a threadpool, so a shared one would be a
    latent crash rather than a visible error."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10.0, isolation_level=None)
        # WAL is what makes multiple worker processes viable: readers do not
        # block the writer and the writer does not block readers.
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=10000")
        conn.row_factory = sqlite3.Row
        _local.conn = conn
        _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    global _initialised
    with _init_lock:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                store    TEXT NOT NULL,
                key      TEXT NOT NULL,
                data     TEXT NOT NULL,
                version  INTEGER NOT NULL DEFAULT 1,
                created  REAL NOT NULL,
                updated  REAL NOT NULL,
                expires  REAL NOT NULL,
                PRIMARY KEY (store, key)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires)")
        _initialised = True


class SessionStore:
    """A named, expiring, cross-process dict of JSON-serialisable values."""

    def __init__(self, name: str, ttl_seconds: float):
        self.name = name
        self.ttl = float(ttl_seconds)

    # ---- reads ---------------------------------------------------------

    def load(self, key: str) -> Optional[Tuple[Dict[str, Any], int]]:
        """Return (data, version), or None if absent or expired."""
        row = _connect().execute(
            "SELECT data, version, expires FROM sessions WHERE store = ? AND key = ?",
            (self.name, key),
        ).fetchone()
        if row is None:
            return None
        if row["expires"] <= time.time():
            self.delete(key)
            return None
        return json.loads(row["data"]), row["version"]

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        found = self.load(key)
        return found[0] if found else None

    def __contains__(self, key: str) -> bool:
        return self.load(key) is not None

    def items(self) -> List[Tuple[str, Dict[str, Any]]]:
        rows = _connect().execute(
            "SELECT key, data FROM sessions WHERE store = ? AND expires > ? ORDER BY updated DESC",
            (self.name, time.time()),
        ).fetchall()
        return [(r["key"], json.loads(r["data"])) for r in rows]

    def count(self) -> int:
        return _connect().execute(
            "SELECT COUNT(*) AS n FROM sessions WHERE store = ? AND expires > ?",
            (self.name, time.time()),
        ).fetchone()["n"]

    # ---- writes --------------------------------------------------------

    def create(self, key: str, data: Dict[str, Any]) -> None:
        now = time.time()
        _connect().execute(
            "INSERT OR REPLACE INTO sessions (store, key, data, version, created, updated, expires)"
            " VALUES (?, ?, ?, 1, ?, ?, ?)",
            (self.name, key, json.dumps(data), now, now, now + self.ttl),
        )

    def save(self, key: str, data: Dict[str, Any], expected_version: Optional[int] = None) -> bool:
        """Write back. With expected_version, refuse if it has moved on.
        Returns True if the write landed."""
        now = time.time()
        if expected_version is None:
            cur = _connect().execute(
                "UPDATE sessions SET data = ?, version = version + 1, updated = ?, expires = ?"
                " WHERE store = ? AND key = ?",
                (json.dumps(data), now, now + self.ttl, self.name, key),
            )
        else:
            cur = _connect().execute(
                "UPDATE sessions SET data = ?, version = version + 1, updated = ?, expires = ?"
                " WHERE store = ? AND key = ? AND version = ?",
                (json.dumps(data), now, now + self.ttl, self.name, key, expected_version),
            )
        return cur.rowcount > 0

    def touch(self, key: str) -> None:
        """Extend the expiry without reading or rewriting the payload."""
        now = time.time()
        _connect().execute(
            "UPDATE sessions SET updated = ?, expires = ? WHERE store = ? AND key = ?",
            (now, now + self.ttl, self.name, key),
        )

    def delete(self, key: str) -> bool:
        cur = _connect().execute(
            "DELETE FROM sessions WHERE store = ? AND key = ?", (self.name, key)
        )
        return cur.rowcount > 0

    def purge_expired(self) -> int:
        cur = _connect().execute(
            "DELETE FROM sessions WHERE store = ? AND expires <= ?", (self.name, time.time())
        )
        return cur.rowcount

    # ---- the one people should reach for -------------------------------

    @contextmanager
    def checkout(self, key: str) -> Iterator[Dict[str, Any]]:
        """Load a session, let the caller mutate it, write it back on a clean exit.

        Raises KeyError if it is gone or expired, and SessionConflict if
        somebody else wrote to it while we were working. Leaving the block via
        an exception writes nothing, so a failed request cannot half-save.
        """
        found = self.load(key)
        if found is None:
            raise KeyError(key)
        data, version = found
        yield data
        if not self.save(key, data, expected_version=version):
            raise SessionConflict(
                f"session {key!r} in store {self.name!r} was modified by another request"
            )


def purge_all_expired() -> int:
    """Sweep every store at once. Cheap enough to call on a timer."""
    return _connect().execute(
        "DELETE FROM sessions WHERE expires <= ?", (time.time(),)
    ).rowcount


def stats() -> Dict[str, int]:
    rows = _connect().execute(
        "SELECT store, COUNT(*) AS n FROM sessions WHERE expires > ? GROUP BY store",
        (time.time(),),
    ).fetchall()
    return {r["store"]: r["n"] for r in rows}
