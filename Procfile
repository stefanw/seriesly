web: PYTHONUNBUFFERED=true gunicorn --access-logfile=- --error-logfile=- --log-level=info --workers 3 -k gevent --worker-connections 100 --config gunicorn_config.py seriesly.wsgi:application
worker: PYTHONUNBUFFERED=true celery worker -A seriesly -l DEBUG --without-gossip --without-mingle --without-heartbeat
scheduler: PYTHONUNBUFFERED=true celery beat -A seriesly -l DEBUG
