"""Veri Profiling ve İstatistiksel Analiz Servisi"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from pathlib import Path


class DataProfiler:
    """CSV verilerini detaylı analiz eden servis"""

    def __init__(self, file_path: str):
        """
        Args:
            file_path: CSV dosyasının yolu
        """
        self.file_path = Path(file_path)
        self.df = pd.read_csv(file_path)

    def get_column_types(self) -> Dict[str, str]:
        """
        Her sütunun veri tipini belirle

        Returns:
            Sütun adı -> veri tipi mapping
        """
        column_types = {}

        for col in self.df.columns:
            dtype = self.df[col].dtype

            if pd.api.types.is_numeric_dtype(dtype):
                # Sayısal sütun
                if pd.api.types.is_integer_dtype(dtype):
                    column_types[col] = "integer"
                else:
                    column_types[col] = "float"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                column_types[col] = "datetime"
            elif pd.api.types.is_bool_dtype(dtype):
                column_types[col] = "boolean"
            else:
                # Object tipini kontrol et
                unique_ratio = self.df[col].nunique() / len(self.df)
                if unique_ratio < 0.5:  # %50'den az unique değer varsa kategorik
                    column_types[col] = "categorical"
                else:
                    column_types[col] = "text"

        return column_types

    def analyze_numeric_column(self, column: str) -> Dict[str, Any]:
        """
        Sayısal sütun için istatistiksel analiz

        Args:
            column: Sütun adı

        Returns:
            İstatistiksel metrikler
        """
        data = self.df[column].dropna()

        # Outlier tespiti (IQR metodu)
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = data[(data < lower_bound) | (data > upper_bound)]

        return {
            "count": int(data.count()),
            "mean": float(data.mean()),
            "median": float(data.median()),
            "std": float(data.std()),
            "min": float(data.min()),
            "max": float(data.max()),
            "q1": float(Q1),
            "q3": float(Q3),
            "iqr": float(IQR),
            "outlier_count": len(outliers),
            "outlier_percentage": round(len(outliers) / len(data) * 100, 2),
            "outlier_bounds": {
                "lower": float(lower_bound),
                "upper": float(upper_bound)
            },
            "skewness": float(data.skew()),
            "kurtosis": float(data.kurtosis()),
        }

    def analyze_categorical_column(self, column: str) -> Dict[str, Any]:
        """
        Kategorik sütun için analiz

        Args:
            column: Sütun adı

        Returns:
            Kategorik metrikler
        """
        data = self.df[column].dropna()
        value_counts = data.value_counts()

        return {
            "count": int(data.count()),
            "unique_count": int(data.nunique()),
            "mode": str(data.mode().iloc[0]) if len(data.mode()) > 0 else None,
            "top_values": value_counts.head(10).to_dict(),
            "value_distribution": {
                str(k): int(v) for k, v in value_counts.items()
            },
            "entropy": float(-sum((value_counts / len(data)) * np.log2(value_counts / len(data))))
        }

    def analyze_missing_values(self) -> Dict[str, Any]:
        """
        Eksik değerleri analiz et

        Returns:
            Eksik değer istatistikleri
        """
        missing_data = self.df.isnull().sum()
        total_rows = len(self.df)

        missing_info = {}
        for col in self.df.columns:
            missing_count = int(missing_data[col])
            if missing_count > 0:
                missing_info[col] = {
                    "count": missing_count,
                    "percentage": round(missing_count / total_rows * 100, 2)
                }

        return {
            "total_missing_values": int(missing_data.sum()),
            "columns_with_missing": len(missing_info),
            "missing_by_column": missing_info,
            "completeness_score": round((1 - missing_data.sum() / (total_rows * len(self.df.columns))) * 100, 2)
        }

    def get_full_profile(self) -> Dict[str, Any]:
        """
        Tüm veri setinin detaylı profili

        Returns:
            Kapsamlı veri profili
        """
        column_types = self.get_column_types()
        missing_analysis = self.analyze_missing_values()

        column_profiles = {}
        for col in self.df.columns:
            col_type = column_types[col]

            base_info = {
                "type": col_type,
                "null_count": int(self.df[col].isnull().sum()),
                "null_percentage": round(self.df[col].isnull().sum() / len(self.df) * 100, 2)
            }

            if col_type in ["integer", "float"]:
                base_info.update(self.analyze_numeric_column(col))
            elif col_type in ["categorical", "text", "boolean"]:
                base_info.update(self.analyze_categorical_column(col))

            column_profiles[col] = base_info

        return {
            "dataset_info": {
                "total_rows": len(self.df),
                "total_columns": len(self.df.columns),
                "memory_usage_mb": round(self.df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
                "file_size_mb": round(self.file_path.stat().st_size / (1024 * 1024), 2)
            },
            "column_types": column_types,
            "missing_values": missing_analysis,
            "column_profiles": column_profiles,
            "correlations": self._get_correlations() if any(column_types[col] in ["integer", "float"] for col in column_types) else {}
        }

    def _get_correlations(self) -> Dict[str, Any]:
        """
        Sayısal sütunlar arasındaki korelasyonları hesapla

        Returns:
            Korelasyon matrisi
        """
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) < 2:
            return {}

        corr_matrix = self.df[numeric_cols].corr()

        # Yüksek korelasyonları bul (>0.7 veya <-0.7)
        high_correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    high_correlations.append({
                        "column1": numeric_cols[i],
                        "column2": numeric_cols[j],
                        "correlation": round(float(corr_value), 3)
                    })

        return {
            "matrix": {
                col: {
                    other_col: round(float(corr_matrix.loc[col, other_col]), 3)
                    for other_col in numeric_cols
                }
                for col in numeric_cols
            },
            "high_correlations": high_correlations
        }
