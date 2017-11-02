from psycogreen.gevent import patch_psycopg

def post_fork(server, worker):
    """
    https://github.com/jneight/django-db-geventpool
    """
    patch_psycopg()
    worker.log.info("Made Psycopg2 Green")

