"""
CTGAN Celery Tasks
Faz 4.1: Asenkron CTGAN İşlemleri
"""

from celery import Task
from app.celery_config import celery_app
from app.services.ctgan_trainer import CTGANTrainer
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any

UPLOAD_DIR = "uploads"
OUTPUT_DIR = os.path.join(UPLOAD_DIR, "outputs")
MODEL_DIR = "models"


class CTGANTask(Task):
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
    base=CTGANTask,
    name='app.tasks.ctgan_tasks.train_ctgan_async',
    track_started=True
)
def train_ctgan_async(
    self,
    filename: str,
    epochs: int = 300,
    batch_size: int = 500,
    generator_dim: tuple = (256, 256),
    discriminator_dim: tuple = (256, 256)
) -> Dict[str, Any]:
    """
    Asenkron CTGAN model eğitimi

    Args:
        filename: CSV dosya adı
        epochs: Epoch sayısı
        batch_size: Batch size
        generator_dim: Generator dimension
        discriminator_dim: Discriminator dimension

    Returns:
        Training result dictionary
    """
    import threading
    import time

    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': epochs, 'status': 'Veri yükleniyor...'}
        )

        # Load data
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

        df = pd.read_csv(file_path)

        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': epochs, 'status': 'Model oluşturuluyor...'}
        )

        # Create trainer
        trainer = CTGANTrainer(df)

        # Progress simulation thread
        training_complete = threading.Event()
        current_epoch = {'value': 10}

        def simulate_progress():
            """Simulate training progress"""
            while not training_complete.is_set():
                time.sleep(2)  # Update every 2 seconds
                if current_epoch['value'] < epochs - 10:
                    # Increment progress (simulate epoch completion)
                    increment = max(1, int(epochs * 0.03))  # ~3% per update
                    current_epoch['value'] = min(current_epoch['value'] + increment, epochs - 10)

                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': current_epoch['value'],
                            'total': epochs,
                            'status': f'Model eğitiliyor... Epoch {current_epoch["value"]}/{epochs}'
                        }
                    )

        # Start progress simulation
        progress_thread = threading.Thread(target=simulate_progress, daemon=True)
        progress_thread.start()

        # Train model
        result = trainer.train_model(
            epochs=epochs,
            batch_size=batch_size,
            generator_dim=generator_dim,
            discriminator_dim=discriminator_dim
        )

        # Stop progress simulation
        training_complete.set()
        progress_thread.join(timeout=1)

        self.update_state(
            state='PROGRESS',
            meta={'current': epochs, 'total': epochs, 'status': 'Model kaydediliyor...'}
        )

        # Save model
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_id = f"model_{timestamp}"
        model_path = os.path.join(MODEL_DIR, f"{model_id}.pkl")

        save_result = trainer.save_model(model_path)

        return {
            "status": "completed",
            "task_id": self.request.id,
            "model_id": model_id,
            "model_path": model_path,
            "training_stats": result,
            "save_result": save_result
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise


@celery_app.task(
    bind=True,
    base=CTGANTask,
    name='app.tasks.ctgan_tasks.generate_synthetic_data_async',
    track_started=True
)
def generate_synthetic_data_async(
    self,
    model_id: str,
    num_rows: int = 1000,
    batch_size: int = None,
    evaluate: bool = True
) -> Dict[str, Any]:
    """
    Asenkron sentetik veri üretimi

    Args:
        model_id: Model ID
        num_rows: Üretilecek satır sayısı
        batch_size: Batch size (None ise otomatik)
        evaluate: Değerlendirme yapılsın mı

    Returns:
        Generation result dictionary
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': num_rows, 'status': 'Model yükleniyor...'}
        )

        # Load model
        model_path = os.path.join(MODEL_DIR, f"{model_id}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model bulunamadı: {model_id}")

        # Load trainer with model
        trainer = CTGANTrainer.load_model(model_path)

        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': num_rows, 'status': 'Veri üretiliyor...'}
        )

        # Generate data
        synthetic_data = trainer.generate_synthetic_data(
            num_rows=num_rows,
            batch_size=batch_size
        )

        self.update_state(
            state='PROGRESS',
            meta={'current': num_rows, 'total': num_rows, 'status': 'Veri kaydediliyor...'}
        )

        # Save synthetic data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"synthetic_{model_id}_{timestamp}.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        synthetic_data.to_csv(output_path, index=False)

        # Evaluate if requested
        evaluation = None
        if evaluate:
            self.update_state(
                state='PROGRESS',
                meta={'current': num_rows, 'total': num_rows, 'status': 'Değerlendiriliyor...'}
            )
            evaluation = trainer.evaluate_synthetic_data(synthetic_data)

        file_size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 2)

        return {
            "status": "completed",
            "task_id": self.request.id,
            "model_id": model_id,
            "filename": output_filename,
            "output_path": f"outputs/{output_filename}",
            "rows_generated": len(synthetic_data),
            "columns": len(synthetic_data.columns),
            "file_size_mb": file_size_mb,
            "evaluation": evaluation
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise


@celery_app.task(
    bind=True,
    base=CTGANTask,
    name='app.tasks.ctgan_tasks.train_and_generate_async',
    track_started=True
)
def train_and_generate_async(
    self,
    filename: str,
    num_rows: int = 1000,
    epochs: int = 300,
    batch_size: int = 500
) -> Dict[str, Any]:
    """
    Eğit ve üret (tam pipeline)

    Args:
        filename: CSV dosya adı
        num_rows: Üretilecek satır sayısı
        epochs: Epoch sayısı
        batch_size: Batch size

    Returns:
        Complete pipeline result
    """
    try:
        # Train
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'training', 'progress': 0, 'status': 'Model eğitiliyor...'}
        )

        train_result = train_ctgan_async.apply(
            args=[filename, epochs, batch_size]
        ).get()

        if train_result['status'] != 'completed':
            raise Exception("Model eğitimi başarısız")

        # Generate
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'generation', 'progress': 50, 'status': 'Veri üretiliyor...'}
        )

        model_id = train_result['model_id']
        gen_result = generate_synthetic_data_async.apply(
            args=[model_id, num_rows]
        ).get()

        return {
            "status": "completed",
            "task_id": self.request.id,
            "training": train_result,
            "generation": gen_result
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Hata: {str(e)}'}
        )
        raise
