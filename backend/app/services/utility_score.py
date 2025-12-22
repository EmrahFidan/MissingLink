"""
Utility Score Service
Faz 3.3: Kullanılabilirlik Modülü

Gerçek ve sentetik veri ile ML modelleri eğiterek kullanılabilirlik skorunu hesaplar.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
    classification_report, confusion_matrix
)
import warnings
warnings.filterwarnings('ignore')


class UtilityScore:
    """Utility assessment through ML model comparison"""

    def __init__(self):
        """Initialize utility scorer"""
        self.label_encoders = {}
        self.scaler = StandardScaler()

    def assess_utility(
        self,
        df_original: pd.DataFrame,
        df_synthetic: pd.DataFrame,
        target_column: str,
        task_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Gerçek ve sentetik veri ile ML modeli eğit ve karşılaştır

        Args:
            df_original: Orijinal DataFrame
            df_synthetic: Sentetik DataFrame
            target_column: Target sütun
            task_type: "classification", "regression" veya "auto"

        Returns:
            Utility assessment raporu
        """
        # Target sütunu kontrol et
        if target_column not in df_original.columns:
            return {"error": f"Target sütun bulunamadı: {target_column}"}

        if target_column not in df_synthetic.columns:
            return {"error": f"Sentetik veride target sütun yok: {target_column}"}

        # Task type belirleme
        if task_type == "auto":
            task_type = self._detect_task_type(df_original[target_column])

        # Veriyi hazırla
        X_orig, y_orig = self._prepare_data(df_original, target_column)
        X_synth, y_synth = self._prepare_data(df_synthetic, target_column)

        # Model eğit ve değerlendir
        if task_type == "classification":
            report = self._assess_classification(
                X_orig, y_orig,
                X_synth, y_synth,
                target_column
            )
        else:
            report = self._assess_regression(
                X_orig, y_orig,
                X_synth, y_synth,
                target_column
            )

        # Utility score hesapla
        report["utility_score"] = self._calculate_utility_score(report)
        report["assessment"] = self._get_utility_assessment(report["utility_score"])

        return report

    def _detect_task_type(self, series: pd.Series) -> str:
        """Task type'ı otomatik tespit et"""
        # Unique value sayısı
        unique_count = series.nunique()
        total_count = len(series)

        # Eğer unique/total oranı düşükse classification
        if unique_count / total_count < 0.05 or unique_count < 10:
            return "classification"
        else:
            return "regression"

    def _prepare_data(
        self,
        df: pd.DataFrame,
        target_column: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Veriyi ML için hazırla"""
        df_clean = df.copy()

        # Target'ı ayır
        y = df_clean[target_column]
        X = df_clean.drop(columns=[target_column])

        # Categorical sütunları encode et
        for column in X.columns:
            if X[column].dtype == 'object':
                if column not in self.label_encoders:
                    self.label_encoders[column] = LabelEncoder()
                    X[column] = self.label_encoders[column].fit_transform(X[column].astype(str))
                else:
                    # Mevcut encoder'ı kullan
                    try:
                        X[column] = self.label_encoders[column].transform(X[column].astype(str))
                    except:
                        # Yeni kategoriler varsa fit_transform yap
                        self.label_encoders[column] = LabelEncoder()
                        X[column] = self.label_encoders[column].fit_transform(X[column].astype(str))

        # Target'ı encode et (classification için)
        if y.dtype == 'object':
            if target_column not in self.label_encoders:
                self.label_encoders[target_column] = LabelEncoder()
                y = pd.Series(self.label_encoders[target_column].fit_transform(y.astype(str)))
            else:
                try:
                    y = pd.Series(self.label_encoders[target_column].transform(y.astype(str)))
                except:
                    self.label_encoders[target_column] = LabelEncoder()
                    y = pd.Series(self.label_encoders[target_column].fit_transform(y.astype(str)))

        # NaN değerleri doldur
        X = X.fillna(X.median(numeric_only=True))
        y = y.fillna(y.median() if pd.api.types.is_numeric_dtype(y) else y.mode()[0])

        return X, y

    def _assess_classification(
        self,
        X_orig: pd.DataFrame,
        y_orig: pd.Series,
        X_synth: pd.DataFrame,
        y_synth: pd.Series,
        target_column: str
    ) -> Dict[str, Any]:
        """Classification task için utility assessment"""
        report = {
            "task_type": "classification",
            "target_column": target_column,
            "models": {}
        }

        # Train-test split (orijinal veri için)
        X_train_orig, X_test_orig, y_train_orig, y_test_orig = train_test_split(
            X_orig, y_orig, test_size=0.2, random_state=42
        )

        # Model 1: Orijinal veri ile eğitilmiş
        model_orig = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        model_orig.fit(X_train_orig, y_train_orig)
        y_pred_orig = model_orig.predict(X_test_orig)

        report["models"]["trained_on_original"] = {
            "accuracy": float(accuracy_score(y_test_orig, y_pred_orig)),
            "f1_score": float(f1_score(y_test_orig, y_pred_orig, average='weighted')),
            "precision": float(precision_score(y_test_orig, y_pred_orig, average='weighted', zero_division=0)),
            "recall": float(recall_score(y_test_orig, y_pred_orig, average='weighted'))
        }

        # Model 2: Sentetik veri ile eğitilmiş, orijinal test seti ile test edilmiş
        X_train_synth, X_test_synth, y_train_synth, y_test_synth = train_test_split(
            X_synth, y_synth, test_size=0.2, random_state=42
        )

        model_synth = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        model_synth.fit(X_train_synth, y_train_synth)

        # Sentetik model'i orijinal test seti ile test et
        y_pred_synth_on_orig = model_synth.predict(X_test_orig)

        report["models"]["trained_on_synthetic"] = {
            "accuracy": float(accuracy_score(y_test_orig, y_pred_synth_on_orig)),
            "f1_score": float(f1_score(y_test_orig, y_pred_synth_on_orig, average='weighted')),
            "precision": float(precision_score(y_test_orig, y_pred_synth_on_orig, average='weighted', zero_division=0)),
            "recall": float(recall_score(y_test_orig, y_pred_synth_on_orig, average='weighted'))
        }

        # Performance comparison
        accuracy_diff = abs(
            report["models"]["trained_on_original"]["accuracy"] -
            report["models"]["trained_on_synthetic"]["accuracy"]
        )

        f1_diff = abs(
            report["models"]["trained_on_original"]["f1_score"] -
            report["models"]["trained_on_synthetic"]["f1_score"]
        )

        report["performance_difference"] = {
            "accuracy_diff": float(accuracy_diff),
            "f1_diff": float(f1_diff),
            "relative_accuracy": float(
                report["models"]["trained_on_synthetic"]["accuracy"] /
                report["models"]["trained_on_original"]["accuracy"]
            ) if report["models"]["trained_on_original"]["accuracy"] > 0 else 0
        }

        return report

    def _assess_regression(
        self,
        X_orig: pd.DataFrame,
        y_orig: pd.Series,
        X_synth: pd.DataFrame,
        y_synth: pd.Series,
        target_column: str
    ) -> Dict[str, Any]:
        """Regression task için utility assessment"""
        report = {
            "task_type": "regression",
            "target_column": target_column,
            "models": {}
        }

        # Train-test split (orijinal veri için)
        X_train_orig, X_test_orig, y_train_orig, y_test_orig = train_test_split(
            X_orig, y_orig, test_size=0.2, random_state=42
        )

        # Model 1: Orijinal veri ile eğitilmiş
        model_orig = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        model_orig.fit(X_train_orig, y_train_orig)
        y_pred_orig = model_orig.predict(X_test_orig)

        report["models"]["trained_on_original"] = {
            "mse": float(mean_squared_error(y_test_orig, y_pred_orig)),
            "rmse": float(np.sqrt(mean_squared_error(y_test_orig, y_pred_orig))),
            "mae": float(mean_absolute_error(y_test_orig, y_pred_orig)),
            "r2_score": float(r2_score(y_test_orig, y_pred_orig))
        }

        # Model 2: Sentetik veri ile eğitilmiş
        X_train_synth, X_test_synth, y_train_synth, y_test_synth = train_test_split(
            X_synth, y_synth, test_size=0.2, random_state=42
        )

        model_synth = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        model_synth.fit(X_train_synth, y_train_synth)
        y_pred_synth_on_orig = model_synth.predict(X_test_orig)

        report["models"]["trained_on_synthetic"] = {
            "mse": float(mean_squared_error(y_test_orig, y_pred_synth_on_orig)),
            "rmse": float(np.sqrt(mean_squared_error(y_test_orig, y_pred_synth_on_orig))),
            "mae": float(mean_absolute_error(y_test_orig, y_pred_synth_on_orig)),
            "r2_score": float(r2_score(y_test_orig, y_pred_synth_on_orig))
        }

        # Performance comparison
        r2_diff = abs(
            report["models"]["trained_on_original"]["r2_score"] -
            report["models"]["trained_on_synthetic"]["r2_score"]
        )

        report["performance_difference"] = {
            "r2_diff": float(r2_diff),
            "relative_r2": float(
                report["models"]["trained_on_synthetic"]["r2_score"] /
                report["models"]["trained_on_original"]["r2_score"]
            ) if report["models"]["trained_on_original"]["r2_score"] > 0 else 0
        }

        return report

    def _calculate_utility_score(self, report: Dict[str, Any]) -> float:
        """Utility score hesapla (0-1 arası)"""
        if report["task_type"] == "classification":
            # Accuracy ve F1 farkına göre
            accuracy_similarity = 1 - report["performance_difference"]["accuracy_diff"]
            f1_similarity = 1 - report["performance_difference"]["f1_diff"]

            return (accuracy_similarity * 0.5 + f1_similarity * 0.5)

        else:  # regression
            # R2 score farkına göre
            r2_similarity = 1 - report["performance_difference"]["r2_diff"]

            return r2_similarity

    def _get_utility_assessment(self, utility_score: float) -> Dict[str, str]:
        """Utility score'a göre değerlendirme"""
        if utility_score >= 0.9:
            return {
                "grade": "Mükemmel",
                "emoji": "🟢",
                "description": "Sentetik veri ML için orijinal kadar kullanışlı",
                "recommendation": "Güvenle kullanılabilir"
            }
        elif utility_score >= 0.75:
            return {
                "grade": "İyi",
                "emoji": "🔵",
                "description": "Sentetik veri ML için yeterli kalitede",
                "recommendation": "Çoğu kullanım senaryosu için uygun"
            }
        elif utility_score >= 0.6:
            return {
                "grade": "Orta",
                "emoji": "🟡",
                "description": "Sentetik veri bazı ML görevleri için kullanılabilir",
                "recommendation": "Kritik uygulamalarda dikkatli kullanılmalı"
            }
        elif utility_score >= 0.4:
            return {
                "grade": "Zayıf",
                "emoji": "🟠",
                "description": "Sentetik veri düşük ML performansı gösteriyor",
                "recommendation": "Yeniden üretim veya parametre ayarı önerilir"
            }
        else:
            return {
                "grade": "Yetersiz",
                "emoji": "🔴",
                "description": "Sentetik veri ML için uygun değil",
                "recommendation": "Kullanılmamalı, yeni model eğitimi gerekli"
            }
