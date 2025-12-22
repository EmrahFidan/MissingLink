"""
Similarity Report Service
Faz 3.2: Benzerlik Raporu

Orijinal ve sentetik veri arasındaki istatistiksel benzerliği hesaplar ve raporlar.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from scipy.stats import ks_2samp, wasserstein_distance
from scipy.spatial.distance import jensenshannon
from sklearn.preprocessing import LabelEncoder
import json


class SimilarityReport:
    """Similarity analysis between original and synthetic data"""

    def __init__(self):
        """Initialize similarity report generator"""
        self.label_encoders = {}

    def generate_full_report(
        self,
        df_original: pd.DataFrame,
        df_synthetic: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Orijinal ve sentetik veri için tam benzerlik raporu oluştur

        Args:
            df_original: Orijinal DataFrame
            df_synthetic: Sentetik DataFrame

        Returns:
            Tam benzerlik raporu
        """
        report = {
            "overall_similarity": 0.0,
            "column_similarities": {},
            "correlation_comparison": {},
            "distribution_comparison": {},
            "statistical_tests": {},
            "shape_comparison": {
                "original_shape": df_original.shape,
                "synthetic_shape": df_synthetic.shape,
                "shape_match": df_original.shape == df_synthetic.shape
            }
        }

        # Ortak sütunları bul
        common_columns = list(set(df_original.columns) & set(df_synthetic.columns))

        if len(common_columns) == 0:
            report["error"] = "Ortak sütun bulunamadı"
            return report

        # Her sütun için benzerlik skoru
        column_scores = []
        for column in common_columns:
            similarity = self._column_similarity(
                df_original[column],
                df_synthetic[column]
            )
            report["column_similarities"][column] = similarity
            column_scores.append(similarity["similarity_score"])

        # Overall similarity (tüm sütunların ortalaması)
        report["overall_similarity"] = np.mean(column_scores)

        # Korelasyon karşılaştırması (numeric sütunlar için)
        report["correlation_comparison"] = self._compare_correlations(
            df_original,
            df_synthetic,
            common_columns
        )

        # Dağılım karşılaştırması
        report["distribution_comparison"] = self._compare_distributions(
            df_original,
            df_synthetic,
            common_columns
        )

        # İstatistiksel testler
        report["statistical_tests"] = self._run_statistical_tests(
            df_original,
            df_synthetic,
            common_columns
        )

        # Genel değerlendirme
        report["assessment"] = self._get_quality_assessment(
            report["overall_similarity"]
        )

        return report

    def _column_similarity(
        self,
        series_orig: pd.Series,
        series_synth: pd.Series
    ) -> Dict[str, Any]:
        """Tek bir sütun için benzerlik analizi"""
        similarity_info = {
            "column_type": str(series_orig.dtype),
            "similarity_score": 0.0,
            "metrics": {}
        }

        # Numeric sütunlar
        if pd.api.types.is_numeric_dtype(series_orig):
            similarity_info["metrics"] = self._numeric_similarity(
                series_orig,
                series_synth
            )
            similarity_info["similarity_score"] = similarity_info["metrics"]["overall_score"]

        # Categorical sütunlar
        elif pd.api.types.is_object_dtype(series_orig) or pd.api.types.is_categorical_dtype(series_orig):
            similarity_info["metrics"] = self._categorical_similarity(
                series_orig,
                series_synth
            )
            similarity_info["similarity_score"] = similarity_info["metrics"]["overall_score"]

        return similarity_info

    def _numeric_similarity(
        self,
        series_orig: pd.Series,
        series_synth: pd.Series
    ) -> Dict[str, Any]:
        """Numeric sütunlar için benzerlik metrikleri"""
        # Temel istatistikler
        orig_mean = series_orig.mean()
        synth_mean = series_synth.mean()
        orig_std = series_orig.std()
        synth_std = series_synth.std()

        # Mean similarity (0-1 arası normalize edilmiş)
        mean_diff = abs(orig_mean - synth_mean)
        mean_range = max(abs(orig_mean), abs(synth_mean), 1)
        mean_similarity = max(0, 1 - (mean_diff / mean_range))

        # Std similarity
        std_diff = abs(orig_std - synth_std)
        std_range = max(abs(orig_std), abs(synth_std), 1)
        std_similarity = max(0, 1 - (std_diff / std_range))

        # Wasserstein distance (Earth Mover's Distance)
        wasserstein_dist = wasserstein_distance(
            series_orig.dropna().values,
            series_synth.dropna().values
        )
        # Normalize to 0-1 (smaller is better, convert to similarity)
        max_value = max(series_orig.max(), series_synth.max())
        min_value = min(series_orig.min(), series_synth.min())
        value_range = max_value - min_value if max_value != min_value else 1
        wasserstein_similarity = max(0, 1 - (wasserstein_dist / value_range))

        # Overall score (weighted average)
        overall_score = (
            mean_similarity * 0.3 +
            std_similarity * 0.3 +
            wasserstein_similarity * 0.4
        )

        return {
            "mean_original": float(orig_mean),
            "mean_synthetic": float(synth_mean),
            "mean_similarity": float(mean_similarity),
            "std_original": float(orig_std),
            "std_synthetic": float(synth_std),
            "std_similarity": float(std_similarity),
            "wasserstein_distance": float(wasserstein_dist),
            "wasserstein_similarity": float(wasserstein_similarity),
            "overall_score": float(overall_score)
        }

    def _categorical_similarity(
        self,
        series_orig: pd.Series,
        series_synth: pd.Series
    ) -> Dict[str, Any]:
        """Categorical sütunlar için benzerlik metrikleri"""
        # Value counts
        orig_counts = series_orig.value_counts(normalize=True)
        synth_counts = series_synth.value_counts(normalize=True)

        # Ortak kategoriler
        all_categories = set(orig_counts.index) | set(synth_counts.index)

        # Distribution vectors oluştur
        orig_dist = np.array([orig_counts.get(cat, 0) for cat in all_categories])
        synth_dist = np.array([synth_counts.get(cat, 0) for cat in all_categories])

        # Jensen-Shannon divergence (0-1 arası, 0=identical)
        js_divergence = jensenshannon(orig_dist, synth_dist)
        js_similarity = max(0, 1 - js_divergence)

        # Category coverage (kaç kategori korunmuş)
        orig_categories = set(orig_counts.index)
        synth_categories = set(synth_counts.index)
        category_overlap = len(orig_categories & synth_categories) / len(orig_categories) if len(orig_categories) > 0 else 0

        # Overall score
        overall_score = (js_similarity * 0.6 + category_overlap * 0.4)

        return {
            "original_categories": len(orig_categories),
            "synthetic_categories": len(synth_categories),
            "category_overlap": float(category_overlap),
            "js_divergence": float(js_divergence),
            "js_similarity": float(js_similarity),
            "overall_score": float(overall_score)
        }

    def _compare_correlations(
        self,
        df_original: pd.DataFrame,
        df_synthetic: pd.DataFrame,
        common_columns: List[str]
    ) -> Dict[str, Any]:
        """Korelasyon matrislerini karşılaştır"""
        # Sadece numeric sütunlar
        numeric_cols = [
            col for col in common_columns
            if pd.api.types.is_numeric_dtype(df_original[col])
        ]

        if len(numeric_cols) < 2:
            return {
                "error": "Korelasyon analizi için en az 2 numeric sütun gerekli",
                "correlation_similarity": 0.0
            }

        # Korelasyon matrisleri
        corr_orig = df_original[numeric_cols].corr()
        corr_synth = df_synthetic[numeric_cols].corr()

        # Flatten ve karşılaştır (üst üçgen, diagonal hariç)
        mask = np.triu(np.ones_like(corr_orig, dtype=bool), k=1)
        orig_values = corr_orig.where(mask).stack().values
        synth_values = corr_synth.where(mask).stack().values

        # Correlation of correlations
        correlation_similarity = np.corrcoef(orig_values, synth_values)[0, 1]
        correlation_similarity = max(0, correlation_similarity)  # Negative değerleri 0 yap

        # RMSE
        rmse = np.sqrt(np.mean((orig_values - synth_values) ** 2))

        return {
            "correlation_similarity": float(correlation_similarity),
            "rmse": float(rmse),
            "numeric_columns": numeric_cols,
            "correlation_matrix_original": corr_orig.to_dict(),
            "correlation_matrix_synthetic": corr_synth.to_dict()
        }

    def _compare_distributions(
        self,
        df_original: pd.DataFrame,
        df_synthetic: pd.DataFrame,
        common_columns: List[str]
    ) -> Dict[str, Any]:
        """Dağılımları karşılaştır"""
        distribution_info = {}

        for column in common_columns:
            if pd.api.types.is_numeric_dtype(df_original[column]):
                # Histogram data
                orig_values = df_original[column].dropna()
                synth_values = df_synthetic[column].dropna()

                # Bins oluştur (ortak)
                min_val = min(orig_values.min(), synth_values.min())
                max_val = max(orig_values.max(), synth_values.max())
                bins = np.linspace(min_val, max_val, 30)

                orig_hist, _ = np.histogram(orig_values, bins=bins, density=True)
                synth_hist, _ = np.histogram(synth_values, bins=bins, density=True)

                distribution_info[column] = {
                    "type": "numeric",
                    "bins": bins.tolist(),
                    "original_histogram": orig_hist.tolist(),
                    "synthetic_histogram": synth_hist.tolist()
                }

        return distribution_info

    def _run_statistical_tests(
        self,
        df_original: pd.DataFrame,
        df_synthetic: pd.DataFrame,
        common_columns: List[str]
    ) -> Dict[str, Any]:
        """İstatistiksel testler çalıştır"""
        tests = {}

        for column in common_columns:
            if pd.api.types.is_numeric_dtype(df_original[column]):
                # Kolmogorov-Smirnov test
                ks_statistic, ks_pvalue = ks_2samp(
                    df_original[column].dropna(),
                    df_synthetic[column].dropna()
                )

                # p-value > 0.05 ise dağılımlar benzer
                tests[column] = {
                    "test": "Kolmogorov-Smirnov",
                    "statistic": float(ks_statistic),
                    "p_value": float(ks_pvalue),
                    "distributions_similar": bool(ks_pvalue > 0.05),
                    "interpretation": "Dağılımlar benzer" if ks_pvalue > 0.05 else "Dağılımlar farklı"
                }

        return tests

    def _get_quality_assessment(self, overall_similarity: float) -> Dict[str, str]:
        """Similarity score'a göre kalite değerlendirmesi"""
        if overall_similarity >= 0.9:
            return {
                "grade": "Mükemmel",
                "emoji": "🟢",
                "description": "Sentetik veri orijinale çok benzer, güvenle kullanılabilir"
            }
        elif overall_similarity >= 0.75:
            return {
                "grade": "İyi",
                "emoji": "🔵",
                "description": "Sentetik veri yeterli kalitede, çoğu kullanım için uygun"
            }
        elif overall_similarity >= 0.6:
            return {
                "grade": "Orta",
                "emoji": "🟡",
                "description": "Sentetik veri kabul edilebilir, bazı iyileştirmeler yapılabilir"
            }
        elif overall_similarity >= 0.4:
            return {
                "grade": "Zayıf",
                "emoji": "🟠",
                "description": "Sentetik veri düşük kalitede, yeniden üretim önerilir"
            }
        else:
            return {
                "grade": "Yetersiz",
                "emoji": "🔴",
                "description": "Sentetik veri orijinalden çok farklı, kullanılmamalı"
            }

    def generate_column_comparison(
        self,
        df_original: pd.DataFrame,
        df_synthetic: pd.DataFrame,
        column: str
    ) -> Dict[str, Any]:
        """Tek bir sütun için detaylı karşılaştırma"""
        if column not in df_original.columns or column not in df_synthetic.columns:
            return {"error": f"Sütun bulunamadı: {column}"}

        comparison = {
            "column": column,
            "type": str(df_original[column].dtype),
            "similarity": self._column_similarity(
                df_original[column],
                df_synthetic[column]
            )
        }

        # Numeric için histogram data
        if pd.api.types.is_numeric_dtype(df_original[column]):
            orig_values = df_original[column].dropna()
            synth_values = df_synthetic[column].dropna()

            min_val = min(orig_values.min(), synth_values.min())
            max_val = max(orig_values.max(), synth_values.max())
            bins = np.linspace(min_val, max_val, 30)

            orig_hist, _ = np.histogram(orig_values, bins=bins)
            synth_hist, _ = np.histogram(synth_values, bins=bins)

            comparison["histogram"] = {
                "bins": bins.tolist(),
                "original": orig_hist.tolist(),
                "synthetic": synth_hist.tolist()
            }

        # Categorical için value counts
        elif pd.api.types.is_object_dtype(df_original[column]):
            orig_counts = df_original[column].value_counts().head(10)
            synth_counts = df_synthetic[column].value_counts().head(10)

            comparison["value_counts"] = {
                "original": orig_counts.to_dict(),
                "synthetic": synth_counts.to_dict()
            }

        return comparison
