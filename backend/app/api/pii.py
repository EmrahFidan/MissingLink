"""
PII Detection and Anonymization API Endpoints
Faz 2.1: PII Tespiti ve Maskeleme API
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
import os
from datetime import datetime

from app.services.pii_detector import PIIDetector

router = APIRouter()

# Upload dizini
UPLOAD_DIR = "uploads"
ANONYMIZED_DIR = os.path.join(UPLOAD_DIR, "anonymized")

# Anonymized dizinini oluştur
os.makedirs(ANONYMIZED_DIR, exist_ok=True)


class PIIDetectionRequest(BaseModel):
    """PII tespit isteği"""
    filename: str
    preview_only: bool = Field(default=True, description="Sadece önizleme mi?")


class PIIAnonymizationRequest(BaseModel):
    """PII anonimleştirme isteği"""
    filename: str
    columns: Optional[List[str]] = Field(default=None, description="Anonimleştirilecek sütunlar")
    consistent: bool = Field(default=True, description="Tutarlı replacement")
    locale: str = Field(default="tr_TR", description="Faker locale")


@router.post("/detect-pii")
async def detect_pii(request: PIIDetectionRequest):
    """
    CSV dosyasındaki PII'ları tespit et

    Args:
        request: PII tespit isteği

    Returns:
        PII tespit raporu ve önizleme
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, request.filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")

        # CSV'yi oku
        df = pd.read_csv(file_path)

        # PII detector oluştur
        detector = PIIDetector(locale="tr_TR")

        # PII tespit et
        pii_report = detector.detect_pii_in_dataframe(df)

        # Önizleme oluştur
        preview = None
        if request.preview_only:
            preview = detector.get_anonymization_preview(df, num_samples=5)

        return {
            "status": "success",
            "filename": request.filename,
            "pii_report": pii_report,
            "preview": preview,
            "total_rows": len(df),
            "total_columns": len(df.columns)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PII tespiti başarısız: {str(e)}")


@router.post("/anonymize")
async def anonymize_data(request: PIIAnonymizationRequest):
    """
    CSV dosyasındaki PII'ları anonimleştir

    Args:
        request: Anonimleştirme isteği

    Returns:
        Anonimleştirilmiş dosya bilgileri
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, request.filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")

        # CSV'yi oku
        df = pd.read_csv(file_path)

        # PII detector oluştur
        detector = PIIDetector(locale=request.locale)

        # Anonimleştir
        df_anonymized, report = detector.anonymize_dataframe(
            df,
            columns=request.columns,
            consistent=request.consistent
        )

        # Anonimleştirilmiş dosyayı kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = os.path.splitext(request.filename)[0]
        anonymized_filename = f"{base_filename}_anonymized_{timestamp}.csv"
        anonymized_path = os.path.join(ANONYMIZED_DIR, anonymized_filename)

        df_anonymized.to_csv(anonymized_path, index=False)

        # Dosya boyutu
        file_size_mb = round(os.path.getsize(anonymized_path) / (1024 * 1024), 2)

        return {
            "status": "success",
            "message": "Veri başarıyla anonimleştirildi",
            "original_file": request.filename,
            "anonymized_file": anonymized_filename,
            "anonymized_path": f"anonymized/{anonymized_filename}",
            "file_size_mb": file_size_mb,
            "anonymization_report": report,
            "data_info": {
                "total_rows": len(df_anonymized),
                "total_columns": len(df_anonymized.columns),
                "columns": df_anonymized.columns.tolist()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anonimleştirme başarısız: {str(e)}")


@router.get("/anonymized-files")
async def list_anonymized_files():
    """
    Anonimleştirilmiş dosyaları listele

    Returns:
        Anonimleştirilmiş dosya listesi
    """
    try:
        if not os.path.exists(ANONYMIZED_DIR):
            return {"files": []}

        files = []
        for filename in os.listdir(ANONYMIZED_DIR):
            if filename.endswith('.csv'):
                file_path = os.path.join(ANONYMIZED_DIR, filename)
                file_size = os.path.getsize(file_path)

                files.append({
                    "filename": filename,
                    "path": f"anonymized/{filename}",
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(
                        os.path.getctime(file_path)
                    ).isoformat()
                })

        # Tarihe göre sırala (en yeni en üstte)
        files.sort(key=lambda x: x["created_at"], reverse=True)

        return {
            "files": files,
            "total": len(files)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya listesi alınamadı: {str(e)}")


@router.delete("/anonymized-files/{filename}")
async def delete_anonymized_file(filename: str):
    """
    Anonimleştirilmiş dosyayı sil

    Args:
        filename: Silinecek dosya adı

    Returns:
        Silme durumu
    """
    try:
        file_path = os.path.join(ANONYMIZED_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")

        os.remove(file_path)

        return {
            "status": "success",
            "message": f"{filename} başarıyla silindi"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya silinemedi: {str(e)}")


@router.post("/analyze-text")
async def analyze_text(text: str):
    """
    Metin içindeki PII'ları tespit et

    Args:
        text: Analiz edilecek metin

    Returns:
        Tespit edilen PII'lar
    """
    try:
        detector = PIIDetector(locale="tr_TR")
        pii_list = detector.detect_pii_in_text(text, language="tr")

        return {
            "status": "success",
            "text": text,
            "pii_found": len(pii_list),
            "pii_entities": pii_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metin analizi başarısız: {str(e)}")
