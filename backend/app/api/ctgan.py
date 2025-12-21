"""CTGAN Model Eğitimi ve Sentetik Veri Üretimi Endpoint'leri"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import os
from pathlib import Path
import pandas as pd

from app.services.ctgan_trainer import CTGANTrainer

router = APIRouter()

# Dizinler
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
MODEL_DIR = Path("./models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Global model cache (production'da Redis kullanılmalı)
model_cache = {}


class TrainRequest(BaseModel):
    """Model eğitimi isteği"""
    filename: str
    epochs: int = Field(default=300, ge=10, le=1000, description="Eğitim epoch sayısı")
    batch_size: int = Field(default=500, ge=100, le=2000, description="Batch boyutu")
    generator_dim: tuple[int, int] = Field(default=(256, 256), description="Generator boyutları")
    discriminator_dim: tuple[int, int] = Field(default=(256, 256), description="Discriminator boyutları")


class GenerateRequest(BaseModel):
    """Sentetik veri üretimi isteği"""
    model_id: str
    num_rows: int = Field(default=1000, ge=1, le=100000, description="Üretilecek satır sayısı")
    batch_size: Optional[int] = Field(default=None, description="Batch boyutu")
    evaluate: bool = Field(default=True, description="Kalite değerlendirmesi yap")


@router.post("/train", status_code=status.HTTP_202_ACCEPTED)
async def train_model(request: TrainRequest, background_tasks: BackgroundTasks):
    """
    CTGAN modelini eğit

    Args:
        request: Eğitim parametreleri
        background_tasks: Arka plan görevleri

    Returns:
        Eğitim başlatma bilgileri
    """
    file_path = UPLOAD_DIR / request.filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dosya bulunamadı: {request.filename}"
        )

    # Model ID oluştur (dosya adı + timestamp)
    model_id = f"{Path(request.filename).stem}_model"

    try:
        # Trainer oluştur
        trainer = CTGANTrainer(str(file_path))

        # Modeli eğit
        training_stats = trainer.train_model(
            epochs=request.epochs,
            batch_size=request.batch_size,
            generator_dim=request.generator_dim,
            discriminator_dim=request.discriminator_dim,
            verbose=False
        )

        # Modeli kaydet
        model_path = MODEL_DIR / model_id
        save_info = trainer.save_model(str(model_path))

        # Cache'e ekle
        model_cache[model_id] = trainer

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Model başarıyla eğitildi",
                "model_id": model_id,
                "training_stats": training_stats,
                "save_info": save_info
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model eğitimi sırasında hata: {str(e)}"
        )


@router.post("/generate", status_code=status.HTTP_200_OK)
async def generate_synthetic_data(request: GenerateRequest):
    """
    Sentetik veri üret

    Args:
        request: Üretim parametreleri

    Returns:
        Üretilen veri bilgileri ve indirme linki
    """
    # Model cache'den al veya yükle
    if request.model_id not in model_cache:
        model_path = MODEL_DIR / request.model_id

        if not model_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model bulunamadı: {request.model_id}"
            )

        try:
            trainer = CTGANTrainer(str(UPLOAD_DIR / "dummy.csv"))  # Dummy path
            trainer.load_model(str(model_path))
            model_cache[request.model_id] = trainer
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model yükleme hatası: {str(e)}"
            )

    trainer = model_cache[request.model_id]

    try:
        # Sentetik veri üret
        synthetic_data = trainer.generate_synthetic_data(
            num_rows=request.num_rows,
            batch_size=request.batch_size
        )

        # Dosya adı
        output_filename = f"synthetic_{request.model_id}_{request.num_rows}rows.csv"
        output_path = UPLOAD_DIR / output_filename

        # Kaydet
        synthetic_data.to_csv(output_path, index=False)

        response_data = {
            "message": "Sentetik veri başarıyla üretildi",
            "filename": output_filename,
            "rows_generated": len(synthetic_data),
            "columns": len(synthetic_data.columns),
            "column_names": synthetic_data.columns.tolist(),
            "download_url": f"/api/v1/download/{output_filename}"
        }

        # Kalite değerlendirmesi
        if request.evaluate and hasattr(trainer, 'df') and trainer.df is not None:
            try:
                evaluation = trainer.evaluate_synthetic_data(synthetic_data)
                response_data["evaluation"] = evaluation
            except Exception as e:
                response_data["evaluation_error"] = str(e)

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentetik veri üretimi hatası: {str(e)}"
        )


@router.get("/models", status_code=status.HTTP_200_OK)
async def list_models():
    """
    Kaydedilmiş modelleri listele

    Returns:
        Model listesi
    """
    try:
        models = []

        for model_dir in MODEL_DIR.iterdir():
            if model_dir.is_dir():
                stats_file = model_dir / "training_stats.json"

                model_info = {
                    "model_id": model_dir.name,
                    "model_path": str(model_dir),
                    "is_cached": model_dir.name in model_cache
                }

                if stats_file.exists():
                    import json
                    with open(stats_file, 'r') as f:
                        model_info["training_stats"] = json.load(f)

                models.append(model_info)

        return JSONResponse(
            content={
                "total_models": len(models),
                "models": sorted(models, key=lambda x: x.get("training_stats", {}).get("trained_at", ""), reverse=True)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model listeleme hatası: {str(e)}"
        )


@router.get("/models/{model_id}", status_code=status.HTTP_200_OK)
async def get_model_info(model_id: str):
    """
    Belirli bir modelin bilgilerini getir

    Args:
        model_id: Model ID

    Returns:
        Model bilgileri
    """
    model_path = MODEL_DIR / model_id

    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model bulunamadı: {model_id}"
        )

    try:
        import json

        stats_file = model_path / "training_stats.json"
        metadata_file = model_path / "metadata.json"

        info = {
            "model_id": model_id,
            "model_path": str(model_path),
            "is_cached": model_id in model_cache
        }

        if stats_file.exists():
            with open(stats_file, 'r') as f:
                info["training_stats"] = json.load(f)

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                info["metadata"] = json.load(f)

        return JSONResponse(content=info)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model bilgisi alma hatası: {str(e)}"
        )


@router.delete("/models/{model_id}", status_code=status.HTTP_200_OK)
async def delete_model(model_id: str):
    """
    Modeli sil

    Args:
        model_id: Model ID

    Returns:
        Silme bilgileri
    """
    model_path = MODEL_DIR / model_id

    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model bulunamadı: {model_id}"
        )

    try:
        # Cache'den kaldır
        if model_id in model_cache:
            del model_cache[model_id]

        # Dizini sil
        import shutil
        shutil.rmtree(model_path)

        return JSONResponse(
            content={
                "message": f"Model başarıyla silindi: {model_id}",
                "model_id": model_id
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model silme hatası: {str(e)}"
        )
