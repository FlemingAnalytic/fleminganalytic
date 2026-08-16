from multiprocessing import cpu_count



# Socket Path

bind = 'unix:/var/www/fleminganalytic/gunicorn.sock'



# Worker Options
# NOTE: Using 1 worker for chess game sessions stored in memory
# For production with multiple workers, consider using Redis or database for session storage

workers = 1

worker_class = 'uvicorn.workers.UvicornWorker'

# Timeout (increased for file uploads)
timeout = 300

# Logging Options

loglevel = 'debug'

accesslog = '/var/www/fleminganalytic/access_log'

errorlog =  '/var/www/fleminganalytic/error_log'
