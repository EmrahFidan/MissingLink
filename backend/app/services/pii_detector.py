"""
PII Detection and Anonymization Service
Faz 2.1: PII Tespiti ve Maskeleme

Kişisel veriler (isim, email, telefon) tespit edilir ve Faker ile sentetik verilerle değiştirilir.
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from faker import Faker
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


class PIIDetector:
    """PII (Personally Identifiable Information) tespiti ve anonimleştirme servisi"""

    def __init__(self, locale: str = "tr_TR"):
        """
        Args:
            locale: Faker için locale (tr_TR, en_US, vb.)
        """
        self.locale = locale
        self.faker = Faker(locale)
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # Türkçe telefon numarası pattern'i ekle
        tr_phone_pattern = Pattern(
            name="tr_phone_pattern",
            regex=r"\b0?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b",
            score=0.9
        )

        tr_phone_recognizer = PatternRecognizer(
            supported_entity="TR_PHONE_NUMBER",
            patterns=[tr_phone_pattern]
        )

        self.analyzer.registry.add_recognizer(tr_phone_recognizer)

        # Cache: Her unique değer için üretilen sentetik veri
        self.replacement_cache: Dict[str, str] = {}

    def detect_pii_in_text(self, text: str, language: str = "tr") -> List[Dict[str, Any]]:
        """
        Metinde PII tespit et

        Args:
            text: Analiz edilecek metin
            language: Dil kodu (tr, en)

        Returns:
            Tespit edilen PII listesi
        """
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "TR_PHONE_NUMBER"]
        )

        pii_list = []
        for result in results:
            pii_list.append({
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
                "text": text[result.start:result.end]
            })

        return pii_list

    def detect_pii_in_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        DataFrame'deki tüm sütunlarda PII tespit et

        Args:
            df: Analiz edilecek DataFrame

        Returns:
            Sütun bazında PII bilgileri
        """
        pii_report = {
            "total_columns": len(df.columns),
            "columns_with_pii": [],
            "pii_summary": {}
        }

        for column in df.columns:
            # String sütunları kontrol et
            if df[column].dtype == 'object':
                column_pii = self._analyze_column(df[column], column)

                if column_pii["pii_count"] > 0:
                    pii_report["columns_with_pii"].append(column)
                    pii_report["pii_summary"][column] = column_pii

        return pii_report

    def _analyze_column(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Tek bir sütunu PII için analiz et"""
        pii_entities = {
            "PERSON": 0,
            "EMAIL_ADDRESS": 0,
            "PHONE_NUMBER": 0,
            "TR_PHONE_NUMBER": 0
        }

        sample_values = series.dropna().head(100).astype(str)

        for value in sample_values:
            results = self.analyzer.analyze(
                text=value,
                language="tr",
                entities=list(pii_entities.keys())
            )

            for result in results:
                pii_entities[result.entity_type] += 1

        total_pii = sum(pii_entities.values())

        # Dominant PII tipini belirle
        dominant_type = None
        if total_pii > 0:
            dominant_type = max(pii_entities, key=pii_entities.get)

        return {
            "column_name": column_name,
            "pii_count": total_pii,
            "pii_entities": pii_entities,
            "dominant_type": dominant_type,
            "sample_size": len(sample_values)
        }

    def anonymize_dataframe(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        consistent: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        DataFrame'deki PII'ları sentetik verilerle değiştir

        Args:
            df: Anonimleştirilecek DataFrame
            columns: Anonimleştirilecek sütunlar (None ise tüm sütunlar)
            consistent: Aynı değerler için aynı sentetik veriyi kullan

        Returns:
            (Anonimleştirilmiş DataFrame, Anonimleştirme raporu)
        """
        df_anonymized = df.copy()

        if columns is None:
            columns = df.columns.tolist()

        anonymization_report = {
            "columns_processed": [],
            "total_replacements": 0,
            "replacement_stats": {}
        }

        for column in columns:
            if column not in df.columns:
                continue

            if df[column].dtype != 'object':
                continue

            # Sütun tipini tespit et
            column_analysis = self._analyze_column(df[column], column)
            dominant_type = column_analysis.get("dominant_type")

            if dominant_type:
                replacements = 0

                for idx, value in df_anonymized[column].items():
                    if pd.isna(value):
                        continue

                    value_str = str(value)

                    # Consistent mode: cache kullan
                    if consistent and value_str in self.replacement_cache:
                        df_anonymized.at[idx, column] = self.replacement_cache[value_str]
                        replacements += 1
                        continue

                    # PII tipine göre sentetik veri üret
                    synthetic_value = self._generate_synthetic_data(dominant_type, value_str)

                    if synthetic_value != value_str:
                        df_anonymized.at[idx, column] = synthetic_value

                        if consistent:
                            self.replacement_cache[value_str] = synthetic_value

                        replacements += 1

                anonymization_report["columns_processed"].append(column)
                anonymization_report["total_replacements"] += replacements
                anonymization_report["replacement_stats"][column] = {
                    "pii_type": dominant_type,
                    "replacements": replacements
                }

        return df_anonymized, anonymization_report

    def _generate_synthetic_data(self, entity_type: str, original_value: str) -> str:
        """PII tipine göre sentetik veri üret"""
        try:
            if entity_type == "PERSON":
                return self.faker.name()

            elif entity_type == "EMAIL_ADDRESS":
                return self.faker.email()

            elif entity_type in ["PHONE_NUMBER", "TR_PHONE_NUMBER"]:
                # Türkçe telefon formatı: 05XX XXX XX XX
                return self.faker.phone_number()

            else:
                return original_value

        except Exception:
            return original_value

    def get_anonymization_preview(
        self,
        df: pd.DataFrame,
        num_samples: int = 5
    ) -> Dict[str, Any]:
        """
        Anonimleştirme önizlemesi

        Args:
            df: DataFrame
            num_samples: Önizleme için örnek sayısı

        Returns:
            Önizleme raporu
        """
        # PII tespit et
        pii_report = self.detect_pii_in_dataframe(df)

        preview = {
            "pii_columns": pii_report["columns_with_pii"],
            "samples": []
        }

        # Her PII sütunu için örnek göster
        for column in pii_report["columns_with_pii"][:3]:  # İlk 3 sütun
            samples = df[column].dropna().head(num_samples)

            column_preview = {
                "column": column,
                "pii_type": pii_report["pii_summary"][column]["dominant_type"],
                "before_after": []
            }

            for value in samples:
                value_str = str(value)
                synthetic = self._generate_synthetic_data(
                    pii_report["pii_summary"][column]["dominant_type"],
                    value_str
                )

                column_preview["before_after"].append({
                    "original": value_str,
                    "synthetic": synthetic
                })

            preview["samples"].append(column_preview)

        return preview

    def clear_cache(self):
        """Replacement cache'i temizle"""
        self.replacement_cache.clear()
