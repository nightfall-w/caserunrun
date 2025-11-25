from __future__ import absolute_import, unicode_literals

import os
from datetime import datetime

import pytz
from celery import Celery, platforms


def app_now():
    tzinfo = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz=tzinfo)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engineproxy.settings')
platforms.C_FORCE_ROOT = True

app = Celery('celery_tasks')

app.config_from_object('celery_tasks.celeryconfig', namespace='CELERY')
app.now = app_now
app.autodiscover_tasks(["celery_tasks"])
app.conf.broker_transport_options = {'visibility_timeout': 3600 * 24}  # 24 小时，单位为秒
