"""MissingLink FastAPI Ana Uygulama"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

# API router'ları import et
from app.api import upload, analysis, ctgan, pii, dp

# FastAPI uygulaması oluştur
app = FastAPI(
    title=os.getenv("APP_NAME", "MissingLink"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Deep Learning tabanlı sentetik veri üretim motoru",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS ayarları
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router'larını ekle
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(ctgan.router, prefix="/api/v1", tags=["CTGAN"])
app.include_router(pii.router, prefix="/api/v1", tags=["PII"])
app.include_router(dp.router, prefix="/api/v1", tags=["Differential Privacy"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    return JSONResponse(
        content={
            "status": "healthy",
            "app": os.getenv("APP_NAME", "MissingLink"),
            "version": os.getenv("APP_VERSION", "1.0.0")
        }
    )

@app.get("/")
async def root():
    """Ana endpoint"""
    return {
        "message": "MissingLink API - Sentetik Veri Üretim Motoru",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug
    )
