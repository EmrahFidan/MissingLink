"""CSV Dosya Yükleme Endpoint"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import pandas as pd
import os
from pathlib import Path
import shutil
from datetime import datetime

router = APIRouter()

# Yükleme dizini
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maksimum dosya boyutu (MB cinsinden)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload/csv", status_code=status.HTTP_201_CREATED)
async def upload_csv(file: UploadFile = File(...)):
    """
    CSV dosyası yükleme endpoint'i

    Args:
        file: Yüklenecek CSV dosyası

    Returns:
        JSON response with file info and basic statistics

    Raises:
        HTTPException: Dosya formatı veya boyut hatası
    """

    # Dosya formatı kontrolü
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece CSV dosyaları kabul edilir"
        )

    # Dosya boyutu kontrolü
    contents = await file.read()
    file_size = len(contents)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Dosya boyutu {MAX_FILE_SIZE_MB}MB'ı aşamaz"
        )

    # Benzersiz dosya adı oluştur
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = Path(file.filename).stem
    file_extension = Path(file.filename).suffix
    unique_filename = f"{original_filename}_{timestamp}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        # Dosyayı kaydet
        await file.seek(0)  # Dosya okuma pozisyonunu başa al
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Pandas ile dosyayı oku ve analiz et
        df = pd.read_csv(file_path)

        # Temel istatistikler
        stats = {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "upload_path": str(file_path),
            "timestamp": timestamp,
            "data_info": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
                "missing_values": df.isnull().sum().to_dict(),
            },
            "column_types": df.dtypes.astype(str).to_dict(),
            "sample_data": df.head(5).to_dict(orient="records")
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Dosya başarıyla yüklendi ve analiz edildi",
                "data": stats
            }
        )

    except pd.errors.EmptyDataError:
        # Dosyayı sil
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV dosyası boş"
        )

    except pd.errors.ParserError as e:
        # Dosyayı sil
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV dosyası parse edilemedi: {str(e)}"
        )

    except Exception as e:
        # Dosyayı sil
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dosya yüklenirken hata oluştu: {str(e)}"
        )

    finally:
        await file.close()


@router.get("/uploads", status_code=status.HTTP_200_OK)
async def list_uploads():
    """
    Yüklenmiş CSV dosyalarını listele

    Returns:
        Liste of uploaded files with metadata
    """
    try:
        files = []
        for file_path in UPLOAD_DIR.glob("*.csv"):
            file_stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            })

        return JSONResponse(
            content={
                "total_files": len(files),
                "files": sorted(files, key=lambda x: x["created_at"], reverse=True)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dosyalar listelenirken hata oluştu: {str(e)}"
        )


@router.delete("/uploads/{filename}", status_code=status.HTTP_200_OK)
async def delete_upload(filename: str):
    """
    Yüklenmiş CSV dosyasını sil

    Args:
        filename: Silinecek dosya adı

    Returns:
        Success message

    Raises:
        HTTPException: Dosya bulunamadı veya silinemedi
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dosya bulunamadı"
        )

    if not file_path.suffix == ".csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece CSV dosyaları silinebilir"
        )

    try:
        file_path.unlink()
        return JSONResponse(
            content={
                "message": f"{filename} başarıyla silindi"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dosya silinirken hata oluştu: {str(e)}"
        )
