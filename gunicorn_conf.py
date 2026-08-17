from multiprocessing import cpu_count



# Socket Path

bind = 'unix:/var/www/fleminganalytic/gunicorn.sock'



# Worker Options
#
# This was `workers = 1` for a long time, because three module-level dicts
# held state a second process would not share. Raising it before fixing them
# would not have failed loudly - it would have failed intermittently, which is
# worse, since a request either lands on the process holding the state or it
# does not. All three are now resolved:
#
#   apps/analyst/router.py      the dataset session is a cache. It rebuilds
#                               itself from disk on a miss and replays any
#                               derived columns.
#   chessapi/chessapi.py        games are in SQLite, stored as their move list
#                               and replayed on load, so repetition and the
#                               fifty-move rule survive the round trip.
#   apps/stjohn/router.py       login tokens are in SQLite. A restart no
#                               longer signs everybody out.
#
# Both of the latter use apps/session_store.py, which versions each row and
# refuses a stale write rather than silently losing one of two simultaneous
# updates.
#
# Four, not the conventional (2 x cores) + 1. This is a 4-core box shared with
# several other sites, and at ~60 requests/hour the point of more workers here
# is that one slow pivot or chess search no longer blocks every other
# application on the domain - not raw throughput. Oversubscribing a shared
# machine to chase throughput nobody is asking for would just move the
# contention somewhere less visible.
workers = 4

worker_class = 'uvicorn.workers.UvicornWorker'

# Import the application once in the master and fork, rather than importing it
# in each worker. It loads 1,091 PGN games and the pandas/analyst stack at
# import; without this, four workers pay that cost four times in memory and in
# startup. Safe only because no module now holds mutable per-request state -
# which is exactly what the work above was for.
preload_app = True

# Timeout (increased for file uploads)
timeout = 300

# Logging Options

loglevel = 'debug'

accesslog = '/var/www/fleminganalytic/access_log'

errorlog =  '/var/www/fleminganalytic/error_log'
