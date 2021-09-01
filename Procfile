web: PYTHONUNBUFFERED=true gunicorn --access-logfile=- --error-logfile=- --log-level=info --workers 3 seriesly.wsgi:application
worker: PYTHONUNBUFFERED=true celery -A seriesly worker -Q celery,update_show -l DEBUG --without-gossip --without-mingle --without-heartbeat
scheduler: PYTHONUNBUFFERED=true celery -A seriesly beat -l DEBUG
