"""
Async PII API Endpoints
Asenkron PII İşlemleri
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from celery.result import AsyncResult
from app.celery_config import celery_app
from app.tasks.pii_tasks import detect_pii_async, anonymize_data_async

router = APIRouter()


class PIIDetectionRequest(BaseModel):
    """PII detection request model"""
    filename: str = Field(..., description="CSV dosya adı")
    preview_only: bool = Field(True, description="Sadece önizleme mi?")


class PIIAnonymizationRequest(BaseModel):
    """PII anonymization request model"""
    filename: str = Field(..., description="CSV dosya adı")
    columns: Optional[List[str]] = Field(None, description="Anonimleştirilecek sütunlar")
    consistent: bool = Field(True, description="Tutarlı replacement")
    locale: str = Field("tr_TR", description="Faker locale")


@router.post("/async/detect-pii")
async def start_async_pii_detection(request: PIIDetectionRequest) -> Dict[str, Any]:
    """
    Asenkron PII tespitini başlat

    Returns:
        task_id ve status bilgisi
    """
    try:
        # Start async task
        task = detect_pii_async.apply_async(
            kwargs={
                'filename': request.filename,
                'preview_only': request.preview_only
            }
        )

        return {
            "status": "started",
            "task_id": task.id,
            "message": "PII tespiti başlatıldı",
            "check_status_url": f"/api/v1/async/task/{task.id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task başlatılamadı: {str(e)}")


@router.post("/async/anonymize")
async def start_async_anonymization(request: PIIAnonymizationRequest) -> Dict[str, Any]:
    """
    Asenkron anonimleştirmeyi başlat

    Returns:
        task_id ve status bilgisi
    """
    try:
        # Start async task
        task = anonymize_data_async.apply_async(
            kwargs={
                'filename': request.filename,
                'columns': request.columns,
                'consistent': request.consistent,
                'locale': request.locale
            }
        )

        return {
            "status": "started",
            "task_id": task.id,
            "message": "Anonimleştirme başlatıldı",
            "check_status_url": f"/api/v1/async/task/{task.id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task başlatılamadı: {str(e)}")
