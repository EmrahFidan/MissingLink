"""
Differential Privacy Service
Faz 2.2: Diferansiyel Gizlilik

Veri üretimine Laplace veya Gaussian gürültüsü ekleyerek re-identification'ı engeller.
Epsilon parametresi ile gizlilik bütçesi kontrolü sağlar.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Literal
from diffprivlib.mechanisms import Laplace, Gaussian
from diffprivlib.tools import mean, var, std, median


class DifferentialPrivacy:
    """Differential Privacy implementation for tabular data"""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        Args:
            epsilon: Privacy budget (daha küçük = daha fazla gizlilik, 0.1-10 arası önerilir)
            delta: Failure probability for (ε,δ)-DP (genellikle 1e-5)
        """
        self.epsilon = epsilon
        self.delta = delta
        self.privacy_budget_spent = 0.0

        # Gizlilik seviyesi açıklamaları
        self.privacy_levels = {
            "very_high": (0.1, 0.5, "Çok yüksek gizlilik, düşük doğruluk"),
            "high": (0.5, 1.0, "Yüksek gizlilik, orta doğruluk"),
            "medium": (1.0, 2.0, "Dengeli gizlilik ve doğruluk"),
            "low": (2.0, 5.0, "Düşük gizlilik, yüksek doğruluk"),
            "very_low": (5.0, 10.0, "Çok düşük gizlilik, çok yüksek doğruluk")
        }

    def get_privacy_level(self) -> str:
        """Mevcut epsilon değerine göre gizlilik seviyesini döndür"""
        for level, (min_eps, max_eps, _) in self.privacy_levels.items():
            if min_eps <= self.epsilon < max_eps:
                return level
        return "custom"

    def apply_noise_to_dataframe(
        self,
        df: pd.DataFrame,
        mechanism: Literal["laplace", "gaussian"] = "laplace",
        columns: Optional[List[str]] = None,
        bounds: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        DataFrame'e differential privacy gürültüsü ekle

        Args:
            df: Orijinal DataFrame
            mechanism: Gürültü mekanizması ("laplace" veya "gaussian")
            columns: İşlenecek sütunlar (None ise tüm numeric sütunlar)
            bounds: Her sütun için min-max değerleri

        Returns:
            (DP uygulanmış DataFrame, DP raporu)
        """
        df_dp = df.copy()

        if columns is None:
            # Sadece numeric sütunları seç
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if bounds is None:
            bounds = {}

        dp_report = {
            "epsilon": self.epsilon,
            "delta": self.delta,
            "mechanism": mechanism,
            "privacy_level": self.get_privacy_level(),
            "columns_processed": [],
            "noise_statistics": {},
            "privacy_budget_spent": 0.0
        }

        epsilon_per_column = self.epsilon / len(columns) if columns else self.epsilon

        for column in columns:
            if column not in df.columns:
                continue

            # Numeric olmayan sütunları atla
            if df[column].dtype not in [np.int64, np.float64, np.int32, np.float32]:
                continue

            # Bounds belirle
            if column in bounds:
                lower, upper = bounds[column]
            else:
                lower, upper = df[column].min(), df[column].max()

            # Gürültü ekle
            noisy_values = self._add_noise_to_column(
                df[column].values,
                mechanism=mechanism,
                epsilon=epsilon_per_column,
                lower=lower,
                upper=upper
            )

            df_dp[column] = noisy_values

            # İstatistikler
            original_mean = df[column].mean()
            noisy_mean = noisy_values.mean()
            noise_magnitude = abs(noisy_mean - original_mean)

            dp_report["columns_processed"].append(column)
            dp_report["noise_statistics"][column] = {
                "original_mean": float(original_mean),
                "noisy_mean": float(noisy_mean),
                "noise_magnitude": float(noise_magnitude),
                "relative_error": float(noise_magnitude / abs(original_mean)) if original_mean != 0 else 0,
                "epsilon_used": epsilon_per_column,
                "bounds": [float(lower), float(upper)]
            }

        dp_report["privacy_budget_spent"] = self.epsilon
        self.privacy_budget_spent += self.epsilon

        return df_dp, dp_report

    def _add_noise_to_column(
        self,
        values: np.ndarray,
        mechanism: str,
        epsilon: float,
        lower: float,
        upper: float
    ) -> np.ndarray:
        """Bir sütuna gürültü ekle"""
        sensitivity = upper - lower

        if mechanism == "laplace":
            # Laplace Mechanism
            mech = Laplace(epsilon=epsilon, sensitivity=sensitivity)
        elif mechanism == "gaussian":
            # Gaussian Mechanism
            mech = Gaussian(epsilon=epsilon, delta=self.delta, sensitivity=sensitivity)
        else:
            raise ValueError(f"Bilinmeyen mechanism: {mechanism}")

        # Her değere gürültü ekle
        noisy_values = np.array([mech.randomise(float(val)) for val in values])

        # Bounds içinde tut
        noisy_values = np.clip(noisy_values, lower, upper)

        return noisy_values

    def compute_dp_statistics(
        self,
        df: pd.DataFrame,
        column: str,
        epsilon_per_stat: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Differential privacy ile istatistik hesapla

        Args:
            df: DataFrame
            column: Sütun adı
            epsilon_per_stat: Her istatistik için epsilon (None ise self.epsilon/4)

        Returns:
            DP istatistikleri
        """
        if epsilon_per_stat is None:
            epsilon_per_stat = self.epsilon / 4  # 4 istatistik için böl

        values = df[column].values
        lower, upper = values.min(), values.max()

        # DP mean
        dp_mean = mean(
            values,
            epsilon=epsilon_per_stat,
            bounds=(lower, upper)
        )

        # DP variance
        dp_variance = var(
            values,
            epsilon=epsilon_per_stat,
            bounds=(lower, upper)
        )

        # DP std
        dp_std = std(
            values,
            epsilon=epsilon_per_stat,
            bounds=(lower, upper)
        )

        # DP median (yaklaşık)
        dp_median = median(
            values,
            epsilon=epsilon_per_stat,
            bounds=(lower, upper)
        )

        self.privacy_budget_spent += epsilon_per_stat * 4

        return {
            "mean": float(dp_mean),
            "variance": float(dp_variance),
            "std": float(dp_std),
            "median": float(dp_median),
            "epsilon_used": epsilon_per_stat * 4
        }

    def k_anonymity_check(
        self,
        df: pd.DataFrame,
        quasi_identifiers: List[str],
        k: int = 5
    ) -> Dict[str, Any]:
        """
        K-anonymity kontrolü (re-identification riskini değerlendir)

        Args:
            df: DataFrame
            quasi_identifiers: Quasi-identifier sütunlar
            k: Minimum grup büyüklüğü

        Returns:
            K-anonymity raporu
        """
        # Quasi-identifier'lara göre grupla
        groups = df.groupby(quasi_identifiers).size()

        # K'dan küçük grupları bul
        vulnerable_groups = groups[groups < k]

        total_records = len(df)
        vulnerable_records = vulnerable_groups.sum()
        vulnerable_percentage = (vulnerable_records / total_records) * 100

        return {
            "k_value": k,
            "total_records": total_records,
            "vulnerable_records": int(vulnerable_records),
            "vulnerable_percentage": float(vulnerable_percentage),
            "is_k_anonymous": len(vulnerable_groups) == 0,
            "smallest_group_size": int(groups.min()) if len(groups) > 0 else 0,
            "average_group_size": float(groups.mean()) if len(groups) > 0 else 0,
            "recommendation": self._get_k_anonymity_recommendation(vulnerable_percentage)
        }

    def _get_k_anonymity_recommendation(self, vulnerable_percentage: float) -> str:
        """K-anonymity durumuna göre öneri"""
        if vulnerable_percentage == 0:
            return "Veri k-anonymous, re-identification riski çok düşük"
        elif vulnerable_percentage < 5:
            return "Düşük risk: Küçük oranda kayıt risk altında"
        elif vulnerable_percentage < 20:
            return "Orta risk: Ek gizlilik önlemleri önerilir"
        else:
            return "Yüksek risk: Veriyi anonimleştirmek veya DP uygulamak zorunlu"

    def calculate_privacy_loss(self, num_queries: int) -> Dict[str, Any]:
        """
        Toplam gizlilik kaybını hesapla (composition)

        Args:
            num_queries: Yapılan sorgu sayısı

        Returns:
            Gizlilik kaybı raporu
        """
        # Sequential composition
        total_epsilon = self.epsilon * num_queries

        # Advanced composition (daha iyi bound)
        # ε' = √(2k ln(1/δ)) * ε + k * ε * (e^ε - 1)
        k = num_queries
        advanced_epsilon = (
            np.sqrt(2 * k * np.log(1 / self.delta)) * self.epsilon +
            k * self.epsilon * (np.exp(self.epsilon) - 1)
        )

        return {
            "num_queries": num_queries,
            "base_epsilon": self.epsilon,
            "sequential_composition": float(total_epsilon),
            "advanced_composition": float(advanced_epsilon),
            "privacy_budget_spent": self.privacy_budget_spent,
            "privacy_remaining": max(0, 10.0 - self.privacy_budget_spent),  # Varsayılan max budget: 10
            "recommendation": self._get_privacy_budget_recommendation(self.privacy_budget_spent)
        }

    def _get_privacy_budget_recommendation(self, spent: float) -> str:
        """Privacy budget durumuna göre öneri"""
        if spent < 1.0:
            return "Gizlilik bütçesi bol, daha fazla sorgu yapılabilir"
        elif spent < 5.0:
            return "Orta seviye kullanım, dikkatli olun"
        elif spent < 10.0:
            return "Yüksek kullanım, gizlilik azalıyor"
        else:
            return "Gizlilik bütçesi tükendi, yeni veri toplama gerekebilir"

    def reset_privacy_budget(self):
        """Privacy budget'ı sıfırla"""
        self.privacy_budget_spent = 0.0

    def get_epsilon_recommendation(
        self,
        data_sensitivity: Literal["low", "medium", "high"],
        use_case: Literal["research", "production", "public_release"]
    ) -> Dict[str, Any]:
        """
        Kullanım senaryosuna göre epsilon önerisi

        Args:
            data_sensitivity: Veri hassasiyeti
            use_case: Kullanım senaryosu

        Returns:
            Epsilon önerisi
        """
        # Öneriler matrisi
        recommendations = {
            "research": {"low": 2.0, "medium": 1.0, "high": 0.5},
            "production": {"low": 1.0, "medium": 0.5, "high": 0.1},
            "public_release": {"low": 0.5, "medium": 0.1, "high": 0.05}
        }

        recommended_epsilon = recommendations[use_case][data_sensitivity]

        return {
            "data_sensitivity": data_sensitivity,
            "use_case": use_case,
            "recommended_epsilon": recommended_epsilon,
            "current_epsilon": self.epsilon,
            "privacy_level": self._get_privacy_level_for_epsilon(recommended_epsilon),
            "explanation": self._get_epsilon_explanation(recommended_epsilon, use_case, data_sensitivity)
        }

    def _get_privacy_level_for_epsilon(self, epsilon: float) -> str:
        """Epsilon değerine göre gizlilik seviyesi"""
        if epsilon < 0.5:
            return "very_high"
        elif epsilon < 1.0:
            return "high"
        elif epsilon < 2.0:
            return "medium"
        elif epsilon < 5.0:
            return "low"
        else:
            return "very_low"

    def _get_epsilon_explanation(self, epsilon: float, use_case: str, sensitivity: str) -> str:
        """Epsilon önerisinin açıklaması"""
        return (
            f"{use_case} için {sensitivity} hassasiyetli veriye "
            f"epsilon={epsilon} önerilir. Bu, "
            f"{self._get_privacy_level_for_epsilon(epsilon)} seviyede gizlilik sağlar."
        )
