"""Veri Temizleme ve Ön İşleme Servisi"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path


class DataCleaner:
    """CSV verilerini temizleyen ve ön işleyen servis"""

    def __init__(self, file_path: str):
        """
        Args:
            file_path: CSV dosyasının yolu
        """
        self.file_path = Path(file_path)
        self.df = pd.read_csv(file_path)
        self.original_shape = self.df.shape
        self.cleaning_log = []

    def handle_missing_values(
        self,
        strategy: str = "auto",
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Eksik değerleri işle

        Args:
            strategy: Strateji (auto, drop, mean, median, mode, ffill, bfill)
            columns: İşlenecek sütunlar (None ise tümü)

        Returns:
            Temizlenmiş DataFrame
        """
        if columns is None:
            columns = self.df.columns.tolist()

        for col in columns:
            missing_count = self.df[col].isnull().sum()
            if missing_count == 0:
                continue

            if strategy == "drop":
                before = len(self.df)
                self.df = self.df.dropna(subset=[col])
                self.cleaning_log.append({
                    "column": col,
                    "action": "drop_rows",
                    "rows_removed": before - len(self.df)
                })

            elif strategy == "mean" or (strategy == "auto" and pd.api.types.is_numeric_dtype(self.df[col])):
                mean_value = self.df[col].mean()
                self.df[col].fillna(mean_value, inplace=True)
                self.cleaning_log.append({
                    "column": col,
                    "action": "fill_mean",
                    "fill_value": float(mean_value),
                    "filled_count": missing_count
                })

            elif strategy == "median":
                median_value = self.df[col].median()
                self.df[col].fillna(median_value, inplace=True)
                self.cleaning_log.append({
                    "column": col,
                    "action": "fill_median",
                    "fill_value": float(median_value),
                    "filled_count": missing_count
                })

            elif strategy == "mode" or (strategy == "auto" and not pd.api.types.is_numeric_dtype(self.df[col])):
                mode_value = self.df[col].mode()
                if len(mode_value) > 0:
                    self.df[col].fillna(mode_value[0], inplace=True)
                    self.cleaning_log.append({
                        "column": col,
                        "action": "fill_mode",
                        "fill_value": str(mode_value[0]),
                        "filled_count": missing_count
                    })

            elif strategy == "ffill":
                self.df[col].fillna(method='ffill', inplace=True)
                self.cleaning_log.append({
                    "column": col,
                    "action": "forward_fill",
                    "filled_count": missing_count
                })

            elif strategy == "bfill":
                self.df[col].fillna(method='bfill', inplace=True)
                self.cleaning_log.append({
                    "column": col,
                    "action": "backward_fill",
                    "filled_count": missing_count
                })

        return self.df

    def remove_outliers(
        self,
        columns: Optional[List[str]] = None,
        method: str = "iqr",
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """
        Aykırı değerleri kaldır

        Args:
            columns: İşlenecek sütunlar (None ise tüm sayısal sütunlar)
            method: Metod (iqr, zscore)
            threshold: Eşik değeri (IQR için çarpan, zscore için standart sapma)

        Returns:
            Temizlenmiş DataFrame
        """
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()

        initial_rows = len(self.df)

        for col in columns:
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                continue

            if method == "iqr":
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR

                outliers_mask = (self.df[col] < lower_bound) | (self.df[col] > upper_bound)
                outliers_count = outliers_mask.sum()

                self.df = self.df[~outliers_mask]

                if outliers_count > 0:
                    self.cleaning_log.append({
                        "column": col,
                        "action": "remove_outliers_iqr",
                        "outliers_removed": int(outliers_count),
                        "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)}
                    })

            elif method == "zscore":
                z_scores = np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std())
                outliers_mask = z_scores > threshold
                outliers_count = outliers_mask.sum()

                self.df = self.df[~outliers_mask]

                if outliers_count > 0:
                    self.cleaning_log.append({
                        "column": col,
                        "action": "remove_outliers_zscore",
                        "outliers_removed": int(outliers_count),
                        "threshold": threshold
                    })

        total_removed = initial_rows - len(self.df)
        if total_removed > 0:
            self.cleaning_log.append({
                "action": "total_outliers_removed",
                "rows_removed": total_removed
            })

        return self.df

    def normalize_columns(
        self,
        columns: Optional[List[str]] = None,
        method: str = "minmax"
    ) -> pd.DataFrame:
        """
        Sayısal sütunları normalize et

        Args:
            columns: İşlenecek sütunlar (None ise tüm sayısal sütunlar)
            method: Normalizasyon metodu (minmax, zscore)

        Returns:
            Normalize edilmiş DataFrame
        """
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns.tolist()

        for col in columns:
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                continue

            if method == "minmax":
                min_val = self.df[col].min()
                max_val = self.df[col].max()
                if max_val != min_val:
                    self.df[col] = (self.df[col] - min_val) / (max_val - min_val)
                    self.cleaning_log.append({
                        "column": col,
                        "action": "normalize_minmax",
                        "original_range": {"min": float(min_val), "max": float(max_val)}
                    })

            elif method == "zscore":
                mean_val = self.df[col].mean()
                std_val = self.df[col].std()
                if std_val != 0:
                    self.df[col] = (self.df[col] - mean_val) / std_val
                    self.cleaning_log.append({
                        "column": col,
                        "action": "normalize_zscore",
                        "original_stats": {"mean": float(mean_val), "std": float(std_val)}
                    })

        return self.df

    def encode_categorical(
        self,
        columns: Optional[List[str]] = None,
        method: str = "label"
    ) -> pd.DataFrame:
        """
        Kategorik sütunları encode et

        Args:
            columns: İşlenecek sütunlar (None ise tüm kategorik sütunlar)
            method: Encoding metodu (label, onehot)

        Returns:
            Encode edilmiş DataFrame
        """
        if columns is None:
            columns = self.df.select_dtypes(include=['object']).columns.tolist()

        for col in columns:
            if method == "label":
                categories = self.df[col].unique()
                category_mapping = {cat: idx for idx, cat in enumerate(categories)}
                self.df[col + '_encoded'] = self.df[col].map(category_mapping)

                self.cleaning_log.append({
                    "column": col,
                    "action": "label_encoding",
                    "new_column": col + '_encoded',
                    "mapping": {str(k): int(v) for k, v in category_mapping.items()}
                })

            elif method == "onehot":
                dummies = pd.get_dummies(self.df[col], prefix=col)
                self.df = pd.concat([self.df, dummies], axis=1)

                self.cleaning_log.append({
                    "column": col,
                    "action": "onehot_encoding",
                    "new_columns": dummies.columns.tolist()
                })

        return self.df

    def get_cleaning_summary(self) -> Dict[str, Any]:
        """
        Temizleme işlemlerinin özeti

        Returns:
            Özet bilgiler
        """
        return {
            "original_shape": self.original_shape,
            "current_shape": self.df.shape,
            "rows_removed": self.original_shape[0] - self.df.shape[0],
            "columns_added": self.df.shape[1] - self.original_shape[1],
            "cleaning_log": self.cleaning_log,
            "remaining_missing_values": int(self.df.isnull().sum().sum())
        }

    def save_cleaned_data(self, output_path: str) -> str:
        """
        Temizlenmiş veriyi kaydet

        Args:
            output_path: Çıktı dosyası yolu

        Returns:
            Kaydedilen dosyanın yolu
        """
        self.df.to_csv(output_path, index=False)
        return output_path
