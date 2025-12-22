#!/bin/bash
# Celery Worker Başlatma Script'i
# Faz 4.1: Asenkron İşleme

# CTGAN worker'ını başlat (GPU kullanımı için ayrı worker)
echo "Starting CTGAN worker..."
celery -A app.celery_config:celery_app worker \
    --queue=ctgan \
    --concurrency=1 \
    --loglevel=info \
    --hostname=ctgan_worker@%h \
    --logfile=logs/celery_ctgan.log \
    --pidfile=run/celery_ctgan.pid \
    --detach

# Processing worker'ını başlat (genel işlemler)
echo "Starting Processing worker..."
celery -A app.celery_config:celery_app worker \
    --queue=processing \
    --concurrency=4 \
    --loglevel=info \
    --hostname=processing_worker@%h \
    --logfile=logs/celery_processing.log \
    --pidfile=run/celery_processing.pid \
    --detach

echo "All workers started successfully!"
echo "Check logs at logs/celery_*.log"
