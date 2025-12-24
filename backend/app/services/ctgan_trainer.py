"""CTGAN Model Eğitimi ve Sentetik Veri Üretimi Servisi"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path
import pickle
import json
from datetime import datetime

from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata


class CTGANTrainer:
    """CTGAN modelini eğiten ve sentetik veri üreten servis"""

    def __init__(self, file_path: str):
        """
        Args:
            file_path: Eğitim için kullanılacak CSV dosyasının yolu
        """
        self.file_path = Path(file_path)
        self.df = pd.read_csv(file_path)
        self.metadata = None
        self.synthesizer = None
        self.training_stats = {}

    def prepare_metadata(self) -> SingleTableMetadata:
        """
        Veri seti için metadata oluştur (PII detection kapalı)

        Returns:
            SDV SingleTableMetadata objesi
        """
        # Manuel metadata oluştur (PII detection olmadan)
        metadata = SingleTableMetadata()

        # Her kolonu manuel ekle - PII olarak işaretlenmeyecek
        for column in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[column]):
                metadata.add_column(column, sdtype='numerical')
            elif pd.api.types.is_datetime64_any_dtype(self.df[column]):
                metadata.add_column(column, sdtype='datetime')
            elif pd.api.types.is_bool_dtype(self.df[column]):
                metadata.add_column(column, sdtype='boolean')
            else:
                metadata.add_column(column, sdtype='categorical')

        self.metadata = metadata
        return metadata

    def train_model(
        self,
        epochs: int = 300,
        batch_size: int = 500,
        generator_dim: tuple = (256, 256),
        discriminator_dim: tuple = (256, 256),
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        CTGAN modelini eğit

        Args:
            epochs: Eğitim epoch sayısı
            batch_size: Batch boyutu
            generator_dim: Generator katman boyutları
            discriminator_dim: Discriminator katman boyutları
            verbose: Detaylı log

        Returns:
            Eğitim istatistikleri
        """
        start_time = datetime.now()

        # Metadata hazırla
        if self.metadata is None:
            self.prepare_metadata()

        # CTGAN synthesizer oluştur
        self.synthesizer = CTGANSynthesizer(
            metadata=self.metadata,
            epochs=epochs,
            batch_size=batch_size,
            generator_dim=generator_dim,
            discriminator_dim=discriminator_dim,
            verbose=verbose
        )

        # Modeli eğit
        try:
            self.synthesizer.fit(self.df)

            end_time = datetime.now()
            training_duration = (end_time - start_time).total_seconds()

            # Eğitim istatistikleri
            self.training_stats = {
                "status": "success",
                "training_duration_seconds": round(training_duration, 2),
                "training_duration_minutes": round(training_duration / 60, 2),
                "epochs": epochs,
                "batch_size": batch_size,
                "generator_dim": list(generator_dim),
                "discriminator_dim": list(discriminator_dim),
                "training_samples": len(self.df),
                "training_columns": len(self.df.columns),
                "trained_at": end_time.isoformat(),
                "model_size_mb": 0  # Sonradan hesaplanacak
            }

            return self.training_stats

        except Exception as e:
            self.training_stats = {
                "status": "failed",
                "error": str(e),
                "trained_at": datetime.now().isoformat()
            }
            raise

    def generate_synthetic_data(
        self,
        num_rows: int = 1000,
        batch_size: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Sentetik veri üret

        Args:
            num_rows: Üretilecek satır sayısı
            batch_size: Batch boyutu (None ise otomatik)

        Returns:
            Sentetik veri DataFrame
        """
        if self.synthesizer is None:
            raise ValueError("Model henüz eğitilmedi. Önce train_model() çağırın.")

        try:
            # Sentetik veri üret
            synthetic_data = self.synthesizer.sample(
                num_rows=num_rows,
                batch_size=batch_size
            )

            return synthetic_data

        except Exception as e:
            raise ValueError(f"Sentetik veri üretimi başarısız: {str(e)}")

    def save_model(self, model_path: str) -> Dict[str, Any]:
        """
        Eğitilmiş modeli kaydet

        Args:
            model_path: Model kaydedilecek dizin yolu

        Returns:
            Kayıt bilgileri
        """
        if self.synthesizer is None:
            raise ValueError("Kaydedilecek model yok. Önce train_model() çağırın.")

        model_dir = Path(model_path)
        model_dir.mkdir(parents=True, exist_ok=True)

        # Model dosyası
        model_file = model_dir / "ctgan_model.pkl"

        # Modeli kaydet
        with open(model_file, 'wb') as f:
            pickle.dump(self.synthesizer, f)

        # Metadata kaydet
        metadata_file = model_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata.to_dict(), f, indent=2)

        # Eğitim istatistiklerini kaydet
        stats_file = model_dir / "training_stats.json"

        # Model boyutunu hesapla
        model_size_mb = round(model_file.stat().st_size / (1024 * 1024), 2)
        self.training_stats["model_size_mb"] = model_size_mb

        with open(stats_file, 'w') as f:
            json.dump(self.training_stats, f, indent=2)

        return {
            "model_path": str(model_file),
            "metadata_path": str(metadata_file),
            "stats_path": str(stats_file),
            "model_size_mb": model_size_mb,
            "saved_at": datetime.now().isoformat()
        }

    def load_model(self, model_path: str) -> Dict[str, Any]:
        """
        Kaydedilmiş modeli yükle

        Args:
            model_path: Model dizin yolu

        Returns:
            Yükleme bilgileri
        """
        model_dir = Path(model_path)

        if not model_dir.exists():
            raise FileNotFoundError(f"Model dizini bulunamadı: {model_path}")

        # Model dosyası
        model_file = model_dir / "ctgan_model.pkl"
        if not model_file.exists():
            raise FileNotFoundError(f"Model dosyası bulunamadı: {model_file}")

        # Modeli yükle
        with open(model_file, 'rb') as f:
            self.synthesizer = pickle.load(f)

        # Metadata yükle
        metadata_file = model_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
                self.metadata = SingleTableMetadata.load_from_dict(metadata_dict)

        # Eğitim istatistiklerini yükle
        stats_file = model_dir / "training_stats.json"
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                self.training_stats = json.load(f)

        return {
            "status": "loaded",
            "model_path": str(model_file),
            "loaded_at": datetime.now().isoformat(),
            "training_stats": self.training_stats
        }

    def evaluate_synthetic_data(
        self,
        synthetic_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Üretilen sentetik verinin kalitesini değerlendir

        Args:
            synthetic_data: Üretilen sentetik veri

        Returns:
            Kalite metrikleri
        """
        evaluation = {
            "shape_match": {
                "original_rows": len(self.df),
                "synthetic_rows": len(synthetic_data),
                "original_columns": len(self.df.columns),
                "synthetic_columns": len(synthetic_data.columns),
                "columns_match": list(self.df.columns) == list(synthetic_data.columns)
            },
            "column_statistics": {},
            "data_quality": {}
        }

        # Her sütun için istatistikleri karşılaştır
        for col in self.df.columns:
            if col not in synthetic_data.columns:
                continue

            col_eval = {
                "dtype_match": str(self.df[col].dtype) == str(synthetic_data[col].dtype)
            }

            # Sayısal sütunlar için
            if pd.api.types.is_numeric_dtype(self.df[col]):
                col_eval.update({
                    "original_mean": float(self.df[col].mean()),
                    "synthetic_mean": float(synthetic_data[col].mean()),
                    "mean_difference": float(abs(self.df[col].mean() - synthetic_data[col].mean())),
                    "original_std": float(self.df[col].std()),
                    "synthetic_std": float(synthetic_data[col].std()),
                })

            # Kategorik sütunlar için
            else:
                original_unique = set(self.df[col].unique())
                synthetic_unique = set(synthetic_data[col].unique())

                col_eval.update({
                    "original_unique": len(original_unique),
                    "synthetic_unique": len(synthetic_unique),
                    "unique_overlap": len(original_unique & synthetic_unique),
                    "new_values": list(synthetic_unique - original_unique)[:10]  # İlk 10
                })

            evaluation["column_statistics"][col] = col_eval

        # Veri kalitesi skorları
        null_count = synthetic_data.isnull().sum().sum()
        evaluation["data_quality"] = {
            "total_nulls": int(null_count),
            "null_percentage": round(null_count / (len(synthetic_data) * len(synthetic_data.columns)) * 100, 2),
            "completeness_score": round((1 - null_count / (len(synthetic_data) * len(synthetic_data.columns))) * 100, 2)
        }

        return evaluation

    def get_model_info(self) -> Dict[str, Any]:
        """
        Model bilgilerini döndür

        Returns:
            Model bilgileri
        """
        if self.synthesizer is None:
            return {"status": "not_trained"}

        return {
            "status": "trained",
            "training_stats": self.training_stats,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "ready_for_generation": True
        }
