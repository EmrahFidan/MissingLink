"use client";

import { useState } from "react";

interface PIIManagerProps {
  filename: string;
}

interface PIIReport {
  total_columns: number;
  columns_with_pii: string[];
  pii_summary: Record<string, any>;
}

interface PIIPreview {
  pii_columns: string[];
  samples: Array<{
    column: string;
    pii_type: string;
    before_after: Array<{
      original: string;
      synthetic: string;
    }>;
  }>;
}

export default function PIIManager({ filename }: PIIManagerProps) {
  const [activeTab, setActiveTab] = useState<"detect" | "anonymize">("detect");
  const [isDetecting, setIsDetecting] = useState(false);
  const [isAnonymizing, setIsAnonymizing] = useState(false);
  const [piiReport, setPiiReport] = useState<PIIReport | null>(null);
  const [piiPreview, setPiiPreview] = useState<PIIPreview | null>(null);
  const [anonymizeResult, setAnonymizeResult] = useState<any>(null);
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [consistent, setConsistent] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // PII tespiti
  const handleDetectPII = async () => {
    setIsDetecting(true);
    setPiiReport(null);
    setPiiPreview(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/detect-pii`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename,
          preview_only: true,
        }),
      });

      if (!response.ok) {
        throw new Error("PII tespiti başarısız oldu");
      }

      const data = await response.json();
      setPiiReport(data.pii_report);
      setPiiPreview(data.preview);
    } catch (error: any) {
      alert("Hata: " + error.message);
    } finally {
      setIsDetecting(false);
    }
  };

  // Anonimleştirme
  const handleAnonymize = async () => {
    setIsAnonymizing(true);
    setAnonymizeResult(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/anonymize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename,
          columns: selectedColumns.length > 0 ? selectedColumns : null,
          consistent,
          locale: "tr_TR",
        }),
      });

      if (!response.ok) {
        throw new Error("Anonimleştirme başarısız oldu");
      }

      const data = await response.json();
      setAnonymizeResult(data);
    } catch (error: any) {
      alert("Hata: " + error.message);
    } finally {
      setIsAnonymizing(false);
    }
  };

  // Sütun seçimi toggle
  const toggleColumnSelection = (column: string) => {
    if (selectedColumns.includes(column)) {
      setSelectedColumns(selectedColumns.filter((c) => c !== column));
    } else {
      setSelectedColumns([...selectedColumns, column]);
    }
  };

  // İndir
  const handleDownload = (filename: string) => {
    window.open(`${API_URL}/api/v1/download/${filename}`, "_blank");
  };

  return (
    <div className="glass-effect rounded-xl border border-dark-700 p-6 mt-6">
      <h2 className="text-2xl font-bold text-dark-50 mb-6">
        🛡️ PII Tespiti ve Anonimleştirme
      </h2>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab("detect")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "detect"
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          PII Tespit Et
        </button>
        <button
          onClick={() => setActiveTab("anonymize")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "anonymize"
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Anonimleştir
        </button>
      </div>

      {/* Detect Tab */}
      {activeTab === "detect" && (
        <div className="space-y-4">
          <div className="glass-effect border border-secondary-500/30 bg-secondary-500/5 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>PII (Personally Identifiable Information):</strong> İsim,
              e-posta, telefon gibi kişisel veriler tespit edilir ve KVKK uyumu
              için raporlanır.
            </p>
          </div>

          <button
            onClick={handleDetectPII}
            disabled={isDetecting}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isDetecting ? "Tespit Ediliyor..." : "PII Tespit Et"}
          </button>

          {/* PII Report */}
          {piiReport && (
            <div className="mt-6 space-y-4">
              <div className="glass-effect border border-dark-700 rounded-lg p-4">
                <h3 className="font-bold text-lg mb-3">Tespit Sonuçları</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Toplam Sütun</p>
                    <p className="font-bold text-2xl">{piiReport.total_columns}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">PII İçeren Sütun</p>
                    <p className="font-bold text-2xl text-red-600">
                      {piiReport.columns_with_pii.length}
                    </p>
                  </div>
                </div>

                {piiReport.columns_with_pii.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      PII İçeren Sütunlar:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {piiReport.columns_with_pii.map((col) => (
                        <span
                          key={col}
                          className="bg-red-100 text-red-800 text-xs px-3 py-1 rounded-full"
                        >
                          {col}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Preview */}
              {piiPreview && piiPreview.samples.length > 0 && (
                <div className="space-y-3">
                  <h3 className="font-bold text-lg">Anonimleştirme Önizlemesi</h3>
                  {piiPreview.samples.map((sample, idx) => (
                    <div
                      key={idx}
                      className="bg-white border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <h4 className="font-bold">{sample.column}</h4>
                        <span className="bg-primary-500/20 text-primary-300 border border-primary-500/30 text-xs px-2 py-1 rounded">
                          {sample.pii_type}
                        </span>
                      </div>

                      <div className="space-y-2">
                        {sample.before_after.map((item, i) => (
                          <div
                            key={i}
                            className="grid grid-cols-2 gap-4 text-sm border-t pt-2"
                          >
                            <div>
                              <p className="text-gray-500 text-xs">Orijinal</p>
                              <p className="font-medium text-red-700">
                                {item.original}
                              </p>
                            </div>
                            <div>
                              <p className="text-gray-500 text-xs">Sentetik</p>
                              <p className="font-medium text-green-700">
                                {item.synthetic}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Anonymize Tab */}
      {activeTab === "anonymize" && (
        <div className="space-y-4">
          <div className="glass-effect border border-secondary-500/30 bg-secondary-500/5 rounded-lg p-4">
            <p className="text-sm text-green-800">
              <strong>Anonimleştirme:</strong> Tespit edilen PII&apos;lar Faker
              kütüphanesi ile sentetik verilerle değiştirilir. Gerçek veriler
              korunur.
            </p>
          </div>

          {/* Column Selection */}
          {piiReport && piiReport.columns_with_pii.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">
                Anonimleştirilecek Sütunlar (Boş bırakırsanız tümü):
              </p>
              <div className="flex flex-wrap gap-2">
                {piiReport.columns_with_pii.map((col) => (
                  <button
                    key={col}
                    onClick={() => toggleColumnSelection(col)}
                    className={`px-3 py-1 rounded text-sm ${
                      selectedColumns.includes(col)
                        ? "bg-primary-600 text-white"
                        : "bg-dark-900/40 text-dark-200 hover:bg-dark-900/60 border border-dark-600"
                    }`}
                  >
                    {col}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Consistent Mode */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="consistent"
              checked={consistent}
              onChange={(e) => setConsistent(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="consistent" className="text-sm text-gray-700">
              Tutarlı anonimleştirme (Aynı değerler için aynı sentetik veri)
            </label>
          </div>

          <button
            onClick={handleAnonymize}
            disabled={isAnonymizing}
            className="w-full bg-secondary-600 text-white py-3 px-4 rounded-md hover:bg-secondary-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isAnonymizing ? "Anonimleştiriliyor..." : "Anonimleştir"}
          </button>

          {/* Anonymize Result */}
          {anonymizeResult && (
            <div className="mt-6 p-4 glass-effect border border-secondary-500/30 bg-secondary-500/5 rounded-md">
              <h3 className="font-bold text-green-800 mb-2">
                ✅ Anonimleştirme Tamamlandı!
              </h3>
              <div className="text-sm space-y-1 mb-4">
                <p>
                  <strong>Dosya:</strong> {anonymizeResult.anonymized_file}
                </p>
                <p>
                  <strong>Boyut:</strong> {anonymizeResult.file_size_mb} MB
                </p>
                <p>
                  <strong>Toplam Değiştirme:</strong>{" "}
                  {anonymizeResult.anonymization_report.total_replacements}
                </p>
              </div>

              {/* Replacement Stats */}
              {anonymizeResult.anonymization_report.replacement_stats && (
                <div className="bg-white rounded border p-3 mb-4">
                  <h4 className="font-bold text-sm mb-2">Değiştirme İstatistikleri</h4>
                  {Object.entries(
                    anonymizeResult.anonymization_report.replacement_stats
                  ).map(([col, stats]: [string, any]) => (
                    <div key={col} className="text-xs py-1 border-t">
                      <span className="font-medium">{col}:</span>{" "}
                      {stats.replacements} değer ({stats.pii_type})
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={() =>
                  handleDownload(anonymizeResult.anonymized_path)
                }
                className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700"
              >
                İndir
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
