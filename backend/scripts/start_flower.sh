#!/bin/bash
# Flower Monitoring Dashboard Başlatma Script'i
# Faz 4.1: Celery Task Monitoring

echo "Starting Flower monitoring dashboard..."
celery -A app.celery_config:celery_app flower \
    --port=5555 \
    --loglevel=info \
    --url_prefix=flower \
    --persistent=True \
    --db=flower_db

echo "Flower dashboard started at http://localhost:5555"
