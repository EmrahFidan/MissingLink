@echo off
REM Celery Worker Başlatma Script'i (Windows)
REM Faz 4.1: Asenkron İşleme

echo Creating directories...
if not exist logs mkdir logs
if not exist run mkdir run

echo Starting CTGAN worker...
start "CTGAN Worker" celery -A app.celery_config:celery_app worker --queue=ctgan --concurrency=1 --loglevel=info --hostname=ctgan_worker@%%h --logfile=logs/celery_ctgan.log

echo Starting Processing worker...
start "Processing Worker" celery -A app.celery_config:celery_app worker --queue=processing --concurrency=4 --loglevel=info --hostname=processing_worker@%%h --logfile=logs/celery_processing.log

echo All workers started successfully!
echo Check logs at logs\celery_*.log
pause
