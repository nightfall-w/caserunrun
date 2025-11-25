#!/bin/bash
sleep 2s
nohup celery --app=celery_tasks flower >>/data/logs/all.log 2>&1 &
sleep 3s
nohup celery --app=celery_tasks worker -P prefork --loglevel=DEBUG --concurrency=4 --queues=pytest_case_job_executor,pytest_case_task_executor -n pytest-runner@%h >>/data/logs/all.log 2>&1 &
nohup celery --app=celery_tasks worker -P prefork --loglevel=DEBUG --concurrency=2 --queues=testng_case_job_executor,testng_case_task_executor -n testng-runner@%h >>/data/logs/all.log 2>&1 &
nohup celery --app=celery_tasks worker -P prefork --loglevel=DEBUG --concurrency=10 --queues=minitest_case_job_executor -n minitest-runner@%h >>/data/logs/all.log 2>&1 &
nohup celery --app=celery_tasks worker -P prefork --loglevel=info --concurrency=4 --queues=sonic_case_task_executor -n sonic-runner@%h >/var/logs/celerylog/sonic.log 2>&1 &
sleep 2s
nohup celery -A celery_tasks beat -l info >>/data/logs/all.log 2>&1 &
sleep 2s
nohup gunicorn engineproxy.wsgi:application --workers 8 --bind 0.0.0.0:8000 >>/data/logs/all.log 2>&1 &
sleep 3s
tail -f /data/logs/all.log -n 300
