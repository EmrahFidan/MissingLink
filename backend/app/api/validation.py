"""
Validation API Endpoints
Faz 3: Similarity Report ve Utility Score API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import pandas as pd
import os

from app.services.similarity_report import SimilarityReport
from app.services.utility_score import UtilityScore

router = APIRouter()

# Upload dizini
UPLOAD_DIR = "uploads"


class SimilarityRequest(BaseModel):
    """Similarity report isteği"""
    original_file: str
    synthetic_file: str


class ColumnComparisonRequest(BaseModel):
    """Sütun karşılaştırma isteği"""
    original_file: str
    synthetic_file: str
    column: str


class UtilityRequest(BaseModel):
    """Utility score isteği"""
    original_file: str
    synthetic_file: str
    target_column: str
    task_type: Literal["auto", "classification", "regression"] = Field(default="auto")


@router.post("/similarity-report")
async def generate_similarity_report(request: SimilarityRequest):
    """
    Orijinal ve sentetik veri arasında similarity raporu oluştur

    Args:
        request: Similarity report isteği

    Returns:
        Tam similarity raporu
    """
    try:
        # Dosyaları bul
        orig_path = None
        synth_path = None

        # Uploads ve alt dizinlerde ara
        for root, dirs, files in os.walk(UPLOAD_DIR):
            for file in files:
                if file == request.original_file:
                    orig_path = os.path.join(root, file)
                if file == request.synthetic_file:
                    synth_path = os.path.join(root, file)

        if not orig_path:
            raise HTTPException(status_code=404, detail=f"Orijinal dosya bulunamadı: {request.original_file}")

        if not synth_path:
            raise HTTPException(status_code=404, detail=f"Sentetik dosya bulunamadı: {request.synthetic_file}")

        # CSV'leri oku
        df_original = pd.read_csv(orig_path)
        df_synthetic = pd.read_csv(synth_path)

        # Similarity report oluştur
        similarity_service = SimilarityReport()
        report = similarity_service.generate_full_report(df_original, df_synthetic)

        return {
            "status": "success",
            "original_file": request.original_file,
            "synthetic_file": request.synthetic_file,
            "report": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity raporu oluşturulamadı: {str(e)}")


@router.post("/column-comparison")
async def compare_column(request: ColumnComparisonRequest):
    """
    Tek bir sütun için detaylı karşılaştırma

    Args:
        request: Sütun karşılaştırma isteği

    Returns:
        Sütun karşılaştırma raporu
    """
    try:
        # Dosyaları bul
        orig_path = None
        synth_path = None

        for root, dirs, files in os.walk(UPLOAD_DIR):
            for file in files:
                if file == request.original_file:
                    orig_path = os.path.join(root, file)
                if file == request.synthetic_file:
                    synth_path = os.path.join(root, file)

        if not orig_path or not synth_path:
            raise HTTPException(status_code=404, detail="Dosyalar bulunamadı")

        # CSV'leri oku
        df_original = pd.read_csv(orig_path)
        df_synthetic = pd.read_csv(synth_path)

        # Sütun karşılaştırması
        similarity_service = SimilarityReport()
        comparison = similarity_service.generate_column_comparison(
            df_original,
            df_synthetic,
            request.column
        )

        return {
            "status": "success",
            "comparison": comparison
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sütun karşılaştırması başarısız: {str(e)}")


@router.post("/utility-score")
async def calculate_utility_score(request: UtilityRequest):
    """
    ML modelleri ile utility score hesapla

    Args:
        request: Utility score isteği

    Returns:
        Utility assessment raporu
    """
    try:
        # Dosyaları bul
        orig_path = None
        synth_path = None

        for root, dirs, files in os.walk(UPLOAD_DIR):
            for file in files:
                if file == request.original_file:
                    orig_path = os.path.join(root, file)
                if file == request.synthetic_file:
                    synth_path = os.path.join(root, file)

        if not orig_path:
            raise HTTPException(status_code=404, detail=f"Orijinal dosya bulunamadı: {request.original_file}")

        if not synth_path:
            raise HTTPException(status_code=404, detail=f"Sentetik dosya bulunamadı: {request.synthetic_file}")

        # CSV'leri oku
        df_original = pd.read_csv(orig_path)
        df_synthetic = pd.read_csv(synth_path)

        # Utility score hesapla
        utility_service = UtilityScore()
        report = utility_service.assess_utility(
            df_original,
            df_synthetic,
            target_column=request.target_column,
            task_type=request.task_type
        )

        return {
            "status": "success",
            "original_file": request.original_file,
            "synthetic_file": request.synthetic_file,
            "target_column": request.target_column,
            "report": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Utility score hesaplaması başarısız: {str(e)}")


@router.get("/synthetic-files")
async def list_synthetic_files():
    """
    Sentetik dosyaları listele (CTGAN, DP, anonymized)

    Returns:
        Sentetik dosya listesi
    """
    try:
        synthetic_files = []

        # CTGAN outputs
        ctgan_dir = os.path.join(UPLOAD_DIR, "outputs")
        if os.path.exists(ctgan_dir):
            for filename in os.listdir(ctgan_dir):
                if filename.endswith('.csv'):
                    synthetic_files.append({
                        "filename": filename,
                        "type": "ctgan",
                        "path": f"outputs/{filename}"
                    })

        # DP outputs
        dp_dir = os.path.join(UPLOAD_DIR, "differential_privacy")
        if os.path.exists(dp_dir):
            for filename in os.listdir(dp_dir):
                if filename.endswith('.csv'):
                    synthetic_files.append({
                        "filename": filename,
                        "type": "differential_privacy",
                        "path": f"differential_privacy/{filename}"
                    })

        # Anonymized outputs
        anon_dir = os.path.join(UPLOAD_DIR, "anonymized")
        if os.path.exists(anon_dir):
            for filename in os.listdir(anon_dir):
                if filename.endswith('.csv'):
                    synthetic_files.append({
                        "filename": filename,
                        "type": "anonymized",
                        "path": f"anonymized/{filename}"
                    })

        return {
            "status": "success",
            "files": synthetic_files,
            "total": len(synthetic_files)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya listesi alınamadı: {str(e)}")
