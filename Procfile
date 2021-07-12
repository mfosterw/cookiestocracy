release: python manage.py migrate
web: newrelic-admin run-program gunicorn config.wsgi:application
worker: newrelic-admin run-program celery worker --app=config.celery_app --loglevel=info
beat: newrelic-admin run-program celery beat --app=config.celery_app --loglevel=info
