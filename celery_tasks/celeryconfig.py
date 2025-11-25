from datetime import timedelta
from urllib.parse import quote

from kombu import Queue, Exchange

from engineproxy.settings import REDIS_SERVER, REDIS_USERNAME, REDIS_PORT, REDIS_PASSWORD, TIME_ZONE

# CELERY STUFF
broker_url = 'redis://{}:{}@{}:{}/5'.format(REDIS_USERNAME, quote(REDIS_PASSWORD), REDIS_SERVER, REDIS_PORT)
broker_heartbeat = 0
# result_backend = 'redis://%s:%s/4' % (REDIS_SERVER, REDIS_PORT)
timezone = TIME_ZONE
task_time_limit = 60 * 30
accept_content = ['pickle', 'json']
task_serializer = 'pickle'
result_serializer = 'pickle'
task_default_exchange = 'default'
imports = (
    "celery_tasks.tasks"
)

enable_utc = False

task_queues = (
    Queue(
        "pytest_case_job_executor",
        Exchange("pytest_case_job_executor"),
        routing_key="pytest_case_job_executor"),
    Queue(
        "pytest_case_task_executor",
        Exchange("pytest_case_task_executor"),
        routing_key="pytest_case_task_executor"),
    Queue(
        "testng_case_task_executor",
        Exchange("testng_case_task_executor"),
        routing_key="testng_case_task_executor"),
    Queue(
        "testng_case_job_executor",
        Exchange("testng_case_job_executor"),
        routing_key="testng_case_job_executor"),
    Queue(
        "minitest_case_job_executor",
        Exchange("minitest_case_job_executor"),
        routing_key="minitest_case_job_executor"),
    Queue(
        "sonic_case_task_executor",
        Exchange("sonic_case_task_executor"),
        routing_key="sonic_case_task_executor"),
)
# Queue的路由
task_routes = {
    'pytest_case_job_executor': {"queue": "pytest_case_job_executor",
                                 "routing_key": "pytest_case_job_executor"},
    'pytest_case_task_executor': {"queue": "pytest_case_task_executor",
                                  "routing_key": "pytest_case_task_executor"},
    'testng_case_job_executor': {"queue": "testng_case_job_executor",
                                 "routing_key": "testng_case_job_executor"},
    'testng_case_task_executor': {"queue": "testng_case_task_executor",
                                  "routing_key": "testng_case_task_executor"},
    'minitest_case_job_executor': {"queue": "minitest_case_job_executor",
                                   "routing_key": "minitest_case_job_executor"},
    'engine_sonic.handler.*': {"queue": "sonic_case_task_executor",
                               "routing_key": "sonic_case_task_executor"}
}

CELERY_BEAT_SCHEDULE = {
    'update_sonic_run_result': {
        'task': 'engine_sonic.handler.update_sonic_run_result',
        'schedule': timedelta(seconds=60)
    },
    'sync_sonic_case_modify': {
        'task': 'engine_sonic.handler.sync_sonic_case_modify',
        'schedule': timedelta(seconds=180)
    },
}
