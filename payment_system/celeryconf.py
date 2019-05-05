import os
from celery import Celery
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_system.settings')

app = Celery('payment-system-worker')
CELERY_TIMEZONE = 'Europe/Moscow'

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

