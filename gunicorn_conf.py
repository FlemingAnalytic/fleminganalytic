from multiprocessing import cpu_count



# Socket Path

bind = 'unix:/var/www/fleminganalytic/gunicorn.sock'



# Worker Options
#
# One worker, because three module-level dicts hold state that a second
# process would not share. Raising this without dealing with them first does
# not fail loudly - it fails intermittently, which is worse, since a request
# either lands on the process holding the state or it does not.
#
#   chessapi.py:103           game_sessions   a game in progress. Nothing is
#                                             written to disk, so a second
#                                             worker loses games mid-move.
#   apps/stjohn/router.py:33  sessions        login tokens. A second worker
#                                             logs people out at random.
#   apps/analyst/router.py    sessions        RESOLVED - now a cache. It
#                                             rebuilds itself from disk on a
#                                             miss and replays any derived
#                                             columns, so it is already safe
#                                             for more than one worker.
#
# The remaining two need a shared store. db/stjohn.db already exists and
# SQLite is sufficient for both - no new infrastructure. Until then, every
# request to every application on this domain queues behind this process.
workers = 1

worker_class = 'uvicorn.workers.UvicornWorker'

# Timeout (increased for file uploads)
timeout = 300

# Logging Options

loglevel = 'debug'

accesslog = '/var/www/fleminganalytic/access_log'

errorlog =  '/var/www/fleminganalytic/error_log'
