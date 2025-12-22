"""
Processing Celery Tasks
Faz 4.1: Data Processing Asenkron İşlemleri
"""

from celery import Task
from app.celery_config import celery_app
from app.services.data_profiler import DataProfiler
from app.services.data_cleaner import DataCleaner
from app.services.pii_detector import PIIDetector
from app.services.differential_privacy import DifferentialPrivacy
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

UPLOAD_DIR = "uploads"
OUTPUT_DIR = os.path.join(UPLOAD_DIR, "outputs")


class ProcessingTask(Task):
    """Base task with error handling"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        print(f"Task {task_id} failed: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
            "task_id": task_id
        }


@celery_app.task(
    bind=True,
    base=ProcessingTask,
    name='app.tasks.processing_tasks.profile_data_async',
    track_started=True
)
def profile_data_async(
    self,
    filename: str
) -> Dict[str, Any]:
    """
    Asenkron veri profilleme

    Args:
        filename: CSV dosya adı

    Returns:
        Profiling result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Veri yükleniyor...'}
        )

        # Load data
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        df = pd.read_csv(file_path)

        self.update_state(
            state='PROGRESS',
            meta={'status': 'Veri analiz ediliyor...'}
        )

        # Profile data
        profiler = DataProfiler(df)
        profile = profiler.get_full_profile()

        return {
            "status": "completed",
            "task_id": self.request.id,
            "filename": filename,
            "profile": profile
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise


@celery_app.task(
    bind=True,
    base=ProcessingTask,
    name='app.tasks.processing_tasks.clean_data_async',
    track_started=True
)
def clean_data_async(
    self,
    filename: str,
    handle_missing: str = "drop",
    remove_duplicates: bool = True,
    handle_outliers: bool = False
) -> Dict[str, Any]:
    """
    Asenkron veri temizleme

    Args:
        filename: CSV dosya adı
        handle_missing: Missing value stratejisi
        remove_duplicates: Duplicate'leri kaldır
        handle_outliers: Outlier'ları işle

    Returns:
        Cleaning result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Veri yükleniyor...'}
        )

        # Load data
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        df = pd.read_csv(file_path)
        original_shape = df.shape

        self.update_state(
            state='PROGRESS',
            meta={'status': 'Veri temizleniyor...'}
        )

        # Clean data
        cleaner = DataCleaner(df)
        cleaned_df = cleaner.clean_data(
            handle_missing=handle_missing,
            remove_duplicates=remove_duplicates,
            handle_outliers=handle_outliers
        )
        report = cleaner.get_cleaning_report()

        # Save cleaned data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"cleaned_{filename.rsplit('.', 1)[0]}_{timestamp}.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        cleaned_df.to_csv(output_path, index=False)

        return {
            "status": "completed",
            "task_id": self.request.id,
            "original_filename": filename,
            "output_filename": output_filename,
            "output_path": f"outputs/{output_filename}",
            "original_shape": original_shape,
            "cleaned_shape": cleaned_df.shape,
            "report": report
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise


@celery_app.task(
    bind=True,
    base=ProcessingTask,
    name='app.tasks.processing_tasks.detect_pii_async',
    track_started=True
)
def detect_pii_async(
    self,
    filename: str,
    columns: Optional[List[str]] = None,
    consistent: bool = True
) -> Dict[str, Any]:
    """
    Asenkron PII detection

    Args:
        filename: CSV dosya adı
        columns: Kontrol edilecek kolonlar
        consistent: Tutarlı anonymization

    Returns:
        PII detection result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Veri yükleniyor...'}
        )

        # Load data
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        df = pd.read_csv(file_path)

        self.update_state(
            state='PROGRESS',
            meta={'status': 'PII analiz ediliyor...'}
        )

        # Detect PII
        detector = PIIDetector()
        results = detector.detect_pii_in_dataframe(df, columns)

        return {
            "status": "completed",
            "task_id": self.request.id,
            "filename": filename,
            "pii_results": results
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise


@celery_app.task(
    bind=True,
    base=ProcessingTask,
    name='app.tasks.processing_tasks.anonymize_data_async',
    track_started=True
)
def anonymize_data_async(
    self,
    filename: str,
    columns: Optional[List[str]] = None,
    consistent: bool = True
) -> Dict[str, Any]:
    """
    Asenkron data anonymization

    Args:
        filename: CSV dosya adı
        columns: Anonymize edilecek kolonlar
        consistent: Tutarlı anonymization

    Returns:
        Anonymization result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Veri yükleniyor...'}
        )

        # Load data
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        df = pd.read_csv(file_path)

        self.update_state(
            state='PROGRESS',
            meta={'status': 'Veri anonymize ediliyor...'}
        )

        # Anonymize data
        detector = PIIDetector()
        anonymized_df, stats = detector.anonymize_dataframe(df, columns, consistent)

        # Save anonymized data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"anonymized_{filename.rsplit('.', 1)[0]}_{timestamp}.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        anonymized_df.to_csv(output_path, index=False)

        return {
            "status": "completed",
            "task_id": self.request.id,
            "original_filename": filename,
            "output_filename": output_filename,
            "output_path": f"outputs/{output_filename}",
            "anonymization_stats": stats
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise


@celery_app.task(
    bind=True,
    base=ProcessingTask,
    name='app.tasks.processing_tasks.apply_dp_async',
    track_started=True
)
def apply_dp_async(
    self,
    filename: str,
    epsilon: float = 1.0,
    mechanism: str = "laplace",
    columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Asenkron differential privacy application

    Args:
        filename: CSV dosya adı
        epsilon: Privacy budget
        mechanism: Noise mechanism (laplace/gaussian)
        columns: İşlenecek kolonlar

    Returns:
        DP application result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Veri yükleniyor...'}
        )

        # Load data
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        df = pd.read_csv(file_path)

        self.update_state(
            state='PROGRESS',
            meta={'status': 'Differential privacy uygulanıyor...'}
        )

        # Apply DP
        dp = DifferentialPrivacy(epsilon)
        dp_df, stats = dp.apply_noise_to_dataframe(df, mechanism, columns)

        # Save DP data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"dp_{filename.rsplit('.', 1)[0]}_{timestamp}.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        dp_df.to_csv(output_path, index=False)

        return {
            "status": "completed",
            "task_id": self.request.id,
            "original_filename": filename,
            "output_filename": output_filename,
            "output_path": f"outputs/{output_filename}",
            "epsilon": epsilon,
            "mechanism": mechanism,
            "dp_stats": stats
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise
