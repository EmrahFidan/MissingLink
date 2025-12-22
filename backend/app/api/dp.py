"""
Differential Privacy API Endpoints
Faz 2.2: Diferansiyel Gizlilik API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Tuple
import pandas as pd
import os
from datetime import datetime

from app.services.differential_privacy import DifferentialPrivacy

router = APIRouter()

# Upload dizini
UPLOAD_DIR = "uploads"
DP_DIR = os.path.join(UPLOAD_DIR, "differential_privacy")

# DP dizinini oluştur
os.makedirs(DP_DIR, exist_ok=True)


class ApplyDPRequest(BaseModel):
    """DP uygulama isteği"""
    filename: str
    epsilon: float = Field(default=1.0, ge=0.01, le=10.0, description="Privacy budget")
    delta: float = Field(default=1e-5, ge=1e-10, le=0.1, description="Failure probability")
    mechanism: Literal["laplace", "gaussian"] = Field(default="laplace", description="Noise mechanism")
    columns: Optional[List[str]] = Field(default=None, description="Sütunlar (None=tüm numeric)")
    bounds: Optional[Dict[str, Tuple[float, float]]] = Field(default=None, description="Sütun bounds")


class KAnonymityRequest(BaseModel):
    """K-anonymity kontrol isteği"""
    filename: str
    quasi_identifiers: List[str] = Field(description="Quasi-identifier sütunlar")
    k: int = Field(default=5, ge=2, le=100, description="Minimum grup büyüklüğü")


class EpsilonRecommendationRequest(BaseModel):
    """Epsilon önerisi isteği"""
    data_sensitivity: Literal["low", "medium", "high"]
    use_case: Literal["research", "production", "public_release"]


@router.post("/apply-dp")
async def apply_differential_privacy(request: ApplyDPRequest):
    """
    CSV dosyasına differential privacy uygula

    Args:
        request: DP uygulama isteği

    Returns:
        DP uygulanmış dosya bilgileri ve rapor
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, request.filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")

        # CSV'yi oku
        df = pd.read_csv(file_path)

        # DP instance oluştur
        dp = DifferentialPrivacy(epsilon=request.epsilon, delta=request.delta)

        # DP uygula
        df_dp, dp_report = dp.apply_noise_to_dataframe(
            df,
            mechanism=request.mechanism,
            columns=request.columns,
            bounds=request.bounds
        )

        # DP uygulanmış dosyayı kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = os.path.splitext(request.filename)[0]
        dp_filename = f"{base_filename}_dp_eps{request.epsilon}_{timestamp}.csv"
        dp_path = os.path.join(DP_DIR, dp_filename)

        df_dp.to_csv(dp_path, index=False)

        # Dosya boyutu
        file_size_mb = round(os.path.getsize(dp_path) / (1024 * 1024), 2)

        return {
            "status": "success",
            "message": "Differential privacy başarıyla uygulandı",
            "original_file": request.filename,
            "dp_file": dp_filename,
            "dp_path": f"differential_privacy/{dp_filename}",
            "file_size_mb": file_size_mb,
            "dp_report": dp_report,
            "data_info": {
                "total_rows": len(df_dp),
                "total_columns": len(df_dp.columns),
                "columns": df_dp.columns.tolist()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DP uygulaması başarısız: {str(e)}")


@router.post("/check-k-anonymity")
async def check_k_anonymity(request: KAnonymityRequest):
    """
    K-anonymity kontrolü yap

    Args:
        request: K-anonymity kontrol isteği

    Returns:
        K-anonymity raporu
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, request.filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")

        # CSV'yi oku
        df = pd.read_csv(file_path)

        # Quasi-identifier'ları kontrol et
        missing_columns = [col for col in request.quasi_identifiers if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Sütunlar bulunamadı: {missing_columns}"
            )

        # DP instance oluştur
        dp = DifferentialPrivacy()

        # K-anonymity kontrolü
        k_anonymity_report = dp.k_anonymity_check(
            df,
            quasi_identifiers=request.quasi_identifiers,
            k=request.k
        )

        return {
            "status": "success",
            "filename": request.filename,
            "k_anonymity": k_anonymity_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"K-anonymity kontrolü başarısız: {str(e)}")


@router.post("/get-epsilon-recommendation")
async def get_epsilon_recommendation(request: EpsilonRecommendationRequest):
    """
    Kullanım senaryosuna göre epsilon önerisi al

    Args:
        request: Epsilon önerisi isteği

    Returns:
        Epsilon önerisi
    """
    try:
        dp = DifferentialPrivacy()

        recommendation = dp.get_epsilon_recommendation(
            data_sensitivity=request.data_sensitivity,
            use_case=request.use_case
        )

        return {
            "status": "success",
            "recommendation": recommendation
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Öneri alınamadı: {str(e)}")


@router.get("/privacy-levels")
async def get_privacy_levels():
    """
    Gizlilik seviyelerini listele

    Returns:
        Gizlilik seviyeleri ve açıklamaları
    """
    dp = DifferentialPrivacy()

    levels = []
    for level, (min_eps, max_eps, description) in dp.privacy_levels.items():
        levels.append({
            "level": level,
            "epsilon_range": [min_eps, max_eps],
            "description": description
        })

    return {
        "status": "success",
        "privacy_levels": levels
    }


@router.get("/dp-files")
async def list_dp_files():
    """
    DP uygulanmış dosyaları listele

    Returns:
        DP dosya listesi
    """
    try:
        if not os.path.exists(DP_DIR):
            return {"files": []}

        files = []
        for filename in os.listdir(DP_DIR):
            if filename.endswith('.csv'):
                file_path = os.path.join(DP_DIR, filename)
                file_size = os.path.getsize(file_path)

                # Epsilon değerini filename'den çıkar
                epsilon_str = "N/A"
                if "_dp_eps" in filename:
                    try:
                        epsilon_str = filename.split("_dp_eps")[1].split("_")[0]
                    except:
                        pass

                files.append({
                    "filename": filename,
                    "path": f"differential_privacy/{filename}",
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "epsilon": epsilon_str,
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


@router.delete("/dp-files/{filename}")
async def delete_dp_file(filename: str):
    """
    DP dosyasını sil

    Args:
        filename: Silinecek dosya adı

    Returns:
        Silme durumu
    """
    try:
        file_path = os.path.join(DP_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")

        os.remove(file_path)

        return {
            "status": "success",
            "message": f"{filename} başarıyla silindi"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya silinemedi: {str(e)}")


@router.post("/calculate-privacy-loss")
async def calculate_privacy_loss(epsilon: float, num_queries: int):
    """
    Privacy loss hesapla (composition)

    Args:
        epsilon: Base epsilon
        num_queries: Sorgu sayısı

    Returns:
        Privacy loss raporu
    """
    try:
        dp = DifferentialPrivacy(epsilon=epsilon)

        privacy_loss = dp.calculate_privacy_loss(num_queries)

        return {
            "status": "success",
            "privacy_loss": privacy_loss
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hesaplama başarısız: {str(e)}")
