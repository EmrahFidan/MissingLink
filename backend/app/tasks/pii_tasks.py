"""
PII Detection Celery Tasks
Asenkron PII İşlemleri
"""

from celery import Task
from app.celery_config import celery_app
from app.services.pii_detector import PIIDetector
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

UPLOAD_DIR = "uploads"
ANONYMIZED_DIR = os.path.join(UPLOAD_DIR, "anonymized")


class PIITask(Task):
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
    base=PIITask,
    name='app.tasks.pii_tasks.detect_pii_async',
    track_started=True
)
def detect_pii_async(
    self,
    filename: str,
    preview_only: bool = True
) -> Dict[str, Any]:
    """
    Asenkron PII tespiti

    Args:
        filename: CSV dosya adı
        preview_only: Sadece önizleme mi?

    Returns:
        PII detection result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Dosya yükleniyor...'}
        )

        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        # Load data
        df = pd.read_csv(file_path)
        total_columns = len(df.columns)

        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'PII tespiti başlıyor...'}
        )

        # Create detector
        detector = PIIDetector(locale="tr_TR")

        # Detect PII with progress updates
        self.update_state(
            state='PROGRESS',
            meta={'current': 40, 'total': 100, 'status': f'{total_columns} sütun analiz ediliyor...'}
        )

        pii_report = detector.detect_pii_in_dataframe(df)

        self.update_state(
            state='PROGRESS',
            meta={'current': 70, 'total': 100, 'status': 'Önizleme oluşturuluyor...'}
        )

        # Create preview if requested
        preview = None
        if preview_only:
            preview = detector.get_anonymization_preview(df, num_samples=5)

        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Tamamlanıyor...'}
        )

        return {
            "status": "completed",
            "task_id": self.request.id,
            "filename": filename,
            "pii_report": pii_report,
            "preview": preview,
            "total_rows": len(df),
            "total_columns": len(df.columns)
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise


@celery_app.task(
    bind=True,
    base=PIITask,
    name='app.tasks.pii_tasks.anonymize_data_async',
    track_started=True
)
def anonymize_data_async(
    self,
    filename: str,
    columns: Optional[List[str]] = None,
    consistent: bool = True,
    locale: str = "tr_TR"
) -> Dict[str, Any]:
    """
    Asenkron veri anonimleştirme

    Args:
        filename: CSV dosya adı
        columns: Anonimleştirilecek sütunlar
        consistent: Tutarlı replacement
        locale: Faker locale

    Returns:
        Anonymization result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Dosya yükleniyor...'}
        )

        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        # Load data
        df = pd.read_csv(file_path)
        total_rows = len(df)

        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Anonimleştirme başlıyor...'}
        )

        # Create detector
        detector = PIIDetector(locale=locale)

        self.update_state(
            state='PROGRESS',
            meta={'current': 40, 'total': 100, 'status': f'{total_rows} satır işleniyor...'}
        )

        # Anonymize data
        df_anonymized, report = detector.anonymize_dataframe(
            df,
            columns=columns,
            consistent=consistent
        )

        self.update_state(
            state='PROGRESS',
            meta={'current': 70, 'total': 100, 'status': 'Dosya kaydediliyor...'}
        )

        # Save anonymized file
        os.makedirs(ANONYMIZED_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = os.path.splitext(filename)[0]
        anonymized_filename = f"{base_filename}_anonymized_{timestamp}.csv"
        anonymized_path = os.path.join(ANONYMIZED_DIR, anonymized_filename)

        df_anonymized.to_csv(anonymized_path, index=False)

        file_size_mb = round(os.path.getsize(anonymized_path) / (1024 * 1024), 2)

        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Tamamlandı!'}
        )

        return {
            "status": "completed",
            "task_id": self.request.id,
            "message": "Veri başarıyla anonimleştirildi",
            "original_file": filename,
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
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise
