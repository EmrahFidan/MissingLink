"""Veri Analiz ve Temizleme Endpoint'leri"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
from pathlib import Path

from app.services.data_profiler import DataProfiler
from app.services.data_cleaner import DataCleaner

router = APIRouter()

# Yükleme dizini
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))


class CleaningRequest(BaseModel):
    """Veri temizleme isteği modeli"""
    filename: str
    missing_strategy: Optional[str] = "auto"
    remove_outliers: Optional[bool] = False
    outlier_method: Optional[str] = "iqr"
    outlier_threshold: Optional[float] = 1.5
    normalize: Optional[bool] = False
    normalize_method: Optional[str] = "minmax"
    encode_categorical: Optional[bool] = False
    encoding_method: Optional[str] = "label"


@router.get("/analyze/{filename}", status_code=status.HTTP_200_OK)
async def analyze_file(filename: str):
    """
    Dosya için detaylı veri profiling

    Args:
        filename: Analiz edilecek dosya adı

    Returns:
        Detaylı veri profili
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dosya bulunamadı: {filename}"
        )

    if not file_path.suffix == ".csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece CSV dosyaları analiz edilebilir"
        )

    try:
        profiler = DataProfiler(str(file_path))
        profile = profiler.get_full_profile()

        return JSONResponse(
            content={
                "message": "Veri analizi başarıyla tamamlandı",
                "filename": filename,
                "profile": profile
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analiz sırasında hata oluştu: {str(e)}"
        )


@router.post("/clean", status_code=status.HTTP_200_OK)
async def clean_data(request: CleaningRequest):
    """
    Veriyi temizle ve ön işle

    Args:
        request: Temizleme parametreleri

    Returns:
        Temizlenmiş veri özeti ve indirme linki
    """
    file_path = UPLOAD_DIR / request.filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dosya bulunamadı: {request.filename}"
        )

    try:
        cleaner = DataCleaner(str(file_path))

        # Eksik değerleri işle
        if request.missing_strategy:
            cleaner.handle_missing_values(strategy=request.missing_strategy)

        # Outlier'ları kaldır
        if request.remove_outliers:
            cleaner.remove_outliers(
                method=request.outlier_method,
                threshold=request.outlier_threshold
            )

        # Normalizasyon
        if request.normalize:
            cleaner.normalize_columns(method=request.normalize_method)

        # Kategorik encoding
        if request.encode_categorical:
            cleaner.encode_categorical(method=request.encoding_method)

        # Temizlenmiş veriyi kaydet
        cleaned_filename = f"cleaned_{request.filename}"
        cleaned_path = UPLOAD_DIR / cleaned_filename
        cleaner.save_cleaned_data(str(cleaned_path))

        # Özet bilgileri al
        summary = cleaner.get_cleaning_summary()

        return JSONResponse(
            content={
                "message": "Veri temizleme başarıyla tamamlandı",
                "original_file": request.filename,
                "cleaned_file": cleaned_filename,
                "summary": summary,
                "download_url": f"/api/v1/download/{cleaned_filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Temizleme sırasında hata oluştu: {str(e)}"
        )


@router.get("/download/{filename}", status_code=status.HTTP_200_OK)
async def download_file(filename: str):
    """
    Dosya indirme endpoint'i

    Args:
        filename: İndirilecek dosya adı

    Returns:
        CSV dosyası
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dosya bulunamadı: {filename}"
        )

    return FileResponse(
        path=str(file_path),
        media_type="text/csv",
        filename=filename
    )


@router.get("/column-analysis/{filename}/{column}", status_code=status.HTTP_200_OK)
async def analyze_column(filename: str, column: str):
    """
    Tek bir sütun için detaylı analiz

    Args:
        filename: Dosya adı
        column: Sütun adı

    Returns:
        Sütun analizi
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dosya bulunamadı: {filename}"
        )

    try:
        profiler = DataProfiler(str(file_path))

        if column not in profiler.df.columns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sütun bulunamadı: {column}"
            )

        column_types = profiler.get_column_types()
        col_type = column_types[column]

        analysis = {
            "column": column,
            "type": col_type,
            "null_count": int(profiler.df[column].isnull().sum()),
            "null_percentage": round(profiler.df[column].isnull().sum() / len(profiler.df) * 100, 2)
        }

        if col_type in ["integer", "float"]:
            analysis.update(profiler.analyze_numeric_column(column))
        elif col_type in ["categorical", "text", "boolean"]:
            analysis.update(profiler.analyze_categorical_column(column))

        return JSONResponse(
            content={
                "message": "Sütun analizi başarıyla tamamlandı",
                "filename": filename,
                "analysis": analysis
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analiz sırasında hata oluştu: {str(e)}"
        )
