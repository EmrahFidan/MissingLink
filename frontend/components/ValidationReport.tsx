"use client";

import { useState, useEffect, useCallback } from "react";

interface ValidationReportProps {
  filename: string;
}

export default function ValidationReport({ filename }: ValidationReportProps) {
  const [activeTab, setActiveTab] = useState<"similarity" | "utility">("similarity");
  const [syntheticFiles, setSyntheticFiles] = useState<any[]>([]);
  const [selectedSynthetic, setSelectedSynthetic] = useState("");
  const [targetColumn, setTargetColumn] = useState("");

  // Similarity
  const [isGeneratingSimilarity, setIsGeneratingSimilarity] = useState(false);
  const [similarityReport, setSimilarityReport] = useState<any>(null);

  // Utility
  const [isGeneratingUtility, setIsGeneratingUtility] = useState(false);
  const [utilityReport, setUtilityReport] = useState<any>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // Sentetik dosyaları yükle
  const loadSyntheticFiles = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/synthetic-files`);
      const data = await response.json();
      setSyntheticFiles(data.files || []);
    } catch (error) {
      console.error("Sentetik dosyalar yüklenemedi:", error);
    }
  }, [API_URL]);

  useEffect(() => {
    loadSyntheticFiles();
  }, [loadSyntheticFiles]);

  // Similarity raporu oluştur
  const handleGenerateSimilarity = async () => {
    if (!selectedSynthetic) {
      alert("Lütfen bir sentetik dosya seçin");
      return;
    }

    setIsGeneratingSimilarity(true);
    setSimilarityReport(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/similarity-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          original_file: filename,
          synthetic_file: selectedSynthetic,
        }),
      });

      if (!response.ok) throw new Error("Similarity raporu oluşturulamadı");

      const data = await response.json();
      setSimilarityReport(data.report);
    } catch (error: any) {
      alert("Hata: " + error.message);
    } finally {
      setIsGeneratingSimilarity(false);
    }
  };

  // Utility score hesapla
  const handleGenerateUtility = async () => {
    if (!selectedSynthetic || !targetColumn) {
      alert("Lütfen sentetik dosya ve target sütun seçin");
      return;
    }

    setIsGeneratingUtility(true);
    setUtilityReport(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/utility-score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          original_file: filename,
          synthetic_file: selectedSynthetic,
          target_column: targetColumn,
          task_type: "auto",
        }),
      });

      if (!response.ok) throw new Error("Utility score hesaplanamadı");

      const data = await response.json();
      setUtilityReport(data.report);
    } catch (error: any) {
      alert("Hata: " + error.message);
    } finally {
      setIsGeneratingUtility(false);
    }
  };

  return (
    <div className="glass-effect rounded-xl border border-dark-700 p-6 mt-6">
      <h2 className="text-2xl font-bold text-dark-50 mb-6">📊 Validation Report</h2>

      {/* Sentetik dosya seçimi */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Karşılaştırılacak Sentetik Dosya
        </label>
        <select
          value={selectedSynthetic}
          onChange={(e) => setSelectedSynthetic(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">Sentetik dosya seçin...</option>
          {syntheticFiles.map((file) => (
            <option key={file.filename} value={file.filename}>
              {file.filename} ({file.type})
            </option>
          ))}
        </select>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab("similarity")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "similarity"
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Similarity Report
        </button>
        <button
          onClick={() => setActiveTab("utility")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "utility"
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Utility Score
        </button>
      </div>

      {/* Similarity Tab */}
      {activeTab === "similarity" && (
        <div className="space-y-4">
          <button
            onClick={handleGenerateSimilarity}
            disabled={isGeneratingSimilarity || !selectedSynthetic}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isGeneratingSimilarity ? "Oluşturuluyor..." : "Similarity Report Oluştur"}
          </button>

          {similarityReport && (
            <div className="space-y-4">
              {/* Overall Score */}
              <div className={`p-6 rounded-lg border-2 ${
                similarityReport.overall_similarity >= 0.75
                  ? "bg-green-50 border-green-300"
                  : similarityReport.overall_similarity >= 0.5
                  ? "bg-yellow-50 border-yellow-300"
                  : "bg-red-50 border-red-300"
              }`}>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Overall Similarity</p>
                  <p className="text-5xl font-bold mb-2">
                    {(similarityReport.overall_similarity * 100).toFixed(1)}%
                  </p>
                  <p className="text-lg">
                    {similarityReport.assessment?.emoji}{" "}
                    {similarityReport.assessment?.grade}
                  </p>
                  <p className="text-sm mt-2">{similarityReport.assessment?.description}</p>
                </div>
              </div>

              {/* Column Similarities */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-bold mb-3">Column-Level Similarities</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {Object.entries(similarityReport.column_similarities || {}).map(
                    ([col, data]: [string, any]) => (
                      <div key={col} className="flex items-center justify-between p-2 bg-white rounded">
                        <span className="font-medium">{col}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary-600 h-2 rounded-full"
                              style={{ width: `${data.similarity_score * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-bold">
                            {(data.similarity_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Utility Tab */}
      {activeTab === "utility" && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Column (ML için)
            </label>
            <input
              type="text"
              placeholder="Örn: age, salary, category"
              value={targetColumn}
              onChange={(e) => setTargetColumn(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <button
            onClick={handleGenerateUtility}
            disabled={isGeneratingUtility || !selectedSynthetic || !targetColumn}
            className="w-full bg-secondary-600 text-white py-3 px-4 rounded-md hover:bg-secondary-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isGeneratingUtility ? "Hesaplanıyor..." : "Utility Score Hesapla"}
          </button>

          {utilityReport && (
            <div className="space-y-4">
              {/* Overall Utility Score */}
              <div className={`p-6 rounded-lg border-2 ${
                utilityReport.utility_score >= 0.75
                  ? "bg-green-50 border-green-300"
                  : utilityReport.utility_score >= 0.5
                  ? "bg-yellow-50 border-yellow-300"
                  : "bg-red-50 border-red-300"
              }`}>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Utility Score</p>
                  <p className="text-5xl font-bold mb-2">
                    {(utilityReport.utility_score * 100).toFixed(1)}%
                  </p>
                  <p className="text-lg">
                    {utilityReport.assessment?.emoji}{" "}
                    {utilityReport.assessment?.grade}
                  </p>
                  <p className="text-sm mt-2">{utilityReport.assessment?.description}</p>
                </div>
              </div>

              {/* Model Comparison */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-bold mb-2">Orijinal Veri ile Eğitilmiş</h4>
                  {utilityReport.task_type === "classification" ? (
                    <div className="text-sm space-y-1">
                      <p>Accuracy: {(utilityReport.models?.trained_on_original?.accuracy * 100).toFixed(2)}%</p>
                      <p>F1 Score: {(utilityReport.models?.trained_on_original?.f1_score * 100).toFixed(2)}%</p>
                    </div>
                  ) : (
                    <div className="text-sm space-y-1">
                      <p>R² Score: {utilityReport.models?.trained_on_original?.r2_score?.toFixed(4)}</p>
                      <p>RMSE: {utilityReport.models?.trained_on_original?.rmse?.toFixed(4)}</p>
                    </div>
                  )}
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-bold mb-2">Sentetik Veri ile Eğitilmiş</h4>
                  {utilityReport.task_type === "classification" ? (
                    <div className="text-sm space-y-1">
                      <p>Accuracy: {(utilityReport.models?.trained_on_synthetic?.accuracy * 100).toFixed(2)}%</p>
                      <p>F1 Score: {(utilityReport.models?.trained_on_synthetic?.f1_score * 100).toFixed(2)}%</p>
                    </div>
                  ) : (
                    <div className="text-sm space-y-1">
                      <p>R² Score: {utilityReport.models?.trained_on_synthetic?.r2_score?.toFixed(4)}</p>
                      <p>RMSE: {utilityReport.models?.trained_on_synthetic?.rmse?.toFixed(4)}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="font-bold mb-1">Öneri:</p>
                <p className="text-sm">{utilityReport.assessment?.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
