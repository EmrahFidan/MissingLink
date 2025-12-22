"""
Async CTGAN API Endpoints
Faz 4.1: Celery ile Asenkron İşlemler
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from celery.result import AsyncResult
from app.celery_config import celery_app
from app.tasks.ctgan_tasks import (
    train_ctgan_async,
    generate_synthetic_data_async,
    train_and_generate_async
)

router = APIRouter()


class TrainRequest(BaseModel):
    """Training request model"""
    filename: str = Field(..., description="CSV dosya adı")
    epochs: int = Field(300, ge=10, le=1000, description="Epoch sayısı")
    batch_size: int = Field(500, ge=100, le=2000, description="Batch size")
    generator_dim: tuple = Field((256, 256), description="Generator dimensions")
    discriminator_dim: tuple = Field((256, 256), description="Discriminator dimensions")


class GenerateRequest(BaseModel):
    """Generation request model"""
    model_id: str = Field(..., description="Model ID")
    num_rows: int = Field(1000, ge=1, le=100000, description="Üretilecek satır sayısı")
    batch_size: Optional[int] = Field(None, description="Batch size (opsiyonel)")
    evaluate: bool = Field(True, description="Değerlendirme yapılsın mı")


class PipelineRequest(BaseModel):
    """Complete pipeline request model"""
    filename: str = Field(..., description="CSV dosya adı")
    num_rows: int = Field(1000, ge=1, le=100000, description="Üretilecek satır sayısı")
    epochs: int = Field(300, ge=10, le=1000, description="Epoch sayısı")
    batch_size: int = Field(500, ge=100, le=2000, description="Batch size")


@router.post("/async/train")
async def start_async_training(request: TrainRequest) -> Dict[str, Any]:
    """
    Asenkron model eğitimini başlat

    Returns:
        task_id ve status bilgisi
    """
    try:
        # Start async task
        task = train_ctgan_async.apply_async(
            kwargs={
                'filename': request.filename,
                'epochs': request.epochs,
                'batch_size': request.batch_size,
                'generator_dim': request.generator_dim,
                'discriminator_dim': request.discriminator_dim
            }
        )

        return {
            "status": "started",
            "task_id": task.id,
            "message": "Model eğitimi başlatıldı",
            "check_status_url": f"/api/v1/async/task/{task.id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task başlatılamadı: {str(e)}")


@router.post("/async/generate")
async def start_async_generation(request: GenerateRequest) -> Dict[str, Any]:
    """
    Asenkron veri üretimini başlat

    Returns:
        task_id ve status bilgisi
    """
    try:
        # Start async task
        task = generate_synthetic_data_async.apply_async(
            kwargs={
                'model_id': request.model_id,
                'num_rows': request.num_rows,
                'batch_size': request.batch_size,
                'evaluate': request.evaluate
            }
        )

        return {
            "status": "started",
            "task_id": task.id,
            "message": "Veri üretimi başlatıldı",
            "check_status_url": f"/api/v1/async/task/{task.id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task başlatılamadı: {str(e)}")


@router.post("/async/pipeline")
async def start_async_pipeline(request: PipelineRequest) -> Dict[str, Any]:
    """
    Tam pipeline'ı (eğit + üret) asenkron başlat

    Returns:
        task_id ve status bilgisi
    """
    try:
        # Start async task
        task = train_and_generate_async.apply_async(
            kwargs={
                'filename': request.filename,
                'num_rows': request.num_rows,
                'epochs': request.epochs,
                'batch_size': request.batch_size
            }
        )

        return {
            "status": "started",
            "task_id": task.id,
            "message": "Pipeline başlatıldı (eğitim + üretim)",
            "check_status_url": f"/api/v1/async/task/{task.id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task başlatılamadı: {str(e)}")


@router.get("/async/task/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Task durumunu kontrol et

    Args:
        task_id: Celery task ID

    Returns:
        Task durumu ve ilerleme bilgisi
    """
    try:
        task = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "state": task.state,
            "ready": task.ready(),
            "successful": task.successful() if task.ready() else None
        }

        # Add progress info if available
        if task.state == 'PROGRESS':
            response["progress"] = task.info

        # Add result if completed
        elif task.state == 'SUCCESS':
            response["result"] = task.result

        # Add error if failed
        elif task.state == 'FAILURE':
            response["error"] = str(task.info)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task durumu alınamadı: {str(e)}")


@router.get("/async/result/{task_id}")
async def get_task_result(task_id: str) -> Dict[str, Any]:
    """
    Task sonucunu al (tamamlanmış task'lar için)

    Args:
        task_id: Celery task ID

    Returns:
        Task sonucu
    """
    try:
        task = AsyncResult(task_id, app=celery_app)

        if not task.ready():
            raise HTTPException(
                status_code=400,
                detail=f"Task henüz tamamlanmadı. Durum: {task.state}"
            )

        if task.failed():
            raise HTTPException(
                status_code=500,
                detail=f"Task başarısız oldu: {str(task.info)}"
            )

        return {
            "task_id": task_id,
            "status": "completed",
            "result": task.result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task sonucu alınamadı: {str(e)}")


@router.delete("/async/task/{task_id}")
async def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Çalışan task'ı iptal et

    Args:
        task_id: Celery task ID

    Returns:
        İptal durumu
    """
    try:
        task = AsyncResult(task_id, app=celery_app)

        if task.ready():
            return {
                "task_id": task_id,
                "message": "Task zaten tamamlanmış",
                "state": task.state
            }

        task.revoke(terminate=True)

        return {
            "task_id": task_id,
            "message": "Task iptal edildi",
            "status": "cancelled"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task iptal edilemedi: {str(e)}")


@router.get("/async/tasks")
async def list_active_tasks() -> Dict[str, Any]:
    """
    Aktif task'ları listele

    Returns:
        Aktif task listesi
    """
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()

        return {
            "active": active or {},
            "scheduled": scheduled or {},
            "reserved": reserved or {}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task listesi alınamadı: {str(e)}")
