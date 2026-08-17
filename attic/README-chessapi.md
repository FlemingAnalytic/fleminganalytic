# attic/chessapi.py.dead-duplicate

This was `/var/www/fleminganalytic/chessapi.py`, a 1,354-line copy of the chess
API sitting beside the `chessapi/` package.

**It was never the code that ran.** Python resolves a package before a module
of the same name, so `from chessapi import router` in main.py always loaded
`chessapi/__init__.py` -> `chessapi/chessapi.py`. The top-level file was dead
the moment the package was created, and it had already drifted: the live copy
gained `ai_from_square` / `ai_to_square` for the move-flash animation, which
this one never had.

It was actively misleading. The comment in `gunicorn_conf.py` that named the
blockers for raising the worker count cited "chessapi.py:103" - a line in this
dead file. Anyone following that pointer would have edited code that does
nothing and concluded the fix did not work.

Moved here 2026-08-17 rather than deleted, in case the drift ran the other way
somewhere unnoticed. Safe to delete once nobody has missed it.
