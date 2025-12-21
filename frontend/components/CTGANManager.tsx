"use client";

import { useState } from "react";

interface CTGANManagerProps {
  filename: string;
}

interface TrainingParams {
  epochs: number;
  batch_size: number;
  generator_dim: [number, number];
  discriminator_dim: [number, number];
}

interface Model {
  model_id: string;
  model_path: string;
  is_cached: boolean;
  training_stats?: {
    status: string;
    training_duration_seconds: number;
    training_duration_minutes: number;
    epochs: number;
    batch_size: number;
    training_samples: number;
    training_columns: number;
    trained_at: string;
    model_size_mb: number;
  };
}

export default function CTGANManager({ filename }: CTGANManagerProps) {
  const [activeTab, setActiveTab] = useState<"train" | "generate" | "models">("train");
  const [isTraining, setIsTraining] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [trainingParams, setTrainingParams] = useState<TrainingParams>({
    epochs: 300,
    batch_size: 500,
    generator_dim: [256, 256],
    discriminator_dim: [256, 256],
  });
  const [trainingResult, setTrainingResult] = useState<any>(null);
  const [generateParams, setGenerateParams] = useState({
    model_id: "",
    num_rows: 1000,
    evaluate: true,
  });
  const [generateResult, setGenerateResult] = useState<any>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // Model eğitimi
  const handleTrainModel = async () => {
    setIsTraining(true);
    setTrainingResult(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/train`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename,
          ...trainingParams,
        }),
      });

      if (!response.ok) {
        throw new Error("Model eğitimi başarısız oldu");
      }

      const data = await response.json();
      setTrainingResult(data);

      // Modelleri yeniden yükle
      await loadModels();
    } catch (error: any) {
      alert("Hata: " + error.message);
    } finally {
      setIsTraining(false);
    }
  };

  // Sentetik veri üretimi
  const handleGenerateData = async () => {
    setIsGenerating(true);
    setGenerateResult(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(generateParams),
      });

      if (!response.ok) {
        throw new Error("Veri üretimi başarısız oldu");
      }

      const data = await response.json();
      setGenerateResult(data);
    } catch (error: any) {
      alert("Hata: " + error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  // Modelleri yükle
  const loadModels = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/models`);
      if (!response.ok) {
        throw new Error("Modeller yüklenemedi");
      }
      const data = await response.json();
      setModels(data.models || []);
    } catch (error: any) {
      console.error("Model listesi yüklenirken hata:", error);
    }
  };

  // Model silme
  const handleDeleteModel = async (modelId: string) => {
    if (!confirm(`${modelId} modelini silmek istediğinize emin misiniz?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/v1/models/${modelId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Model silinemedi");
      }

      await loadModels();
      if (selectedModel?.model_id === modelId) {
        setSelectedModel(null);
      }
    } catch (error: any) {
      alert("Hata: " + error.message);
    }
  };

  // Model indir
  const handleDownloadData = async (filename: string) => {
    window.open(`${API_URL}/api/v1/download/${filename}`, "_blank");
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-6">
      <h2 className="text-2xl font-bold mb-6">CTGAN Model Yönetimi</h2>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab("train")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "train"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Model Eğit
        </button>
        <button
          onClick={() => {
            setActiveTab("generate");
            loadModels();
          }}
          className={`pb-2 px-4 font-medium ${
            activeTab === "generate"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Veri Üret
        </button>
        <button
          onClick={() => {
            setActiveTab("models");
            loadModels();
          }}
          className={`pb-2 px-4 font-medium ${
            activeTab === "models"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Modeller
        </button>
      </div>

      {/* Train Tab */}
      {activeTab === "train" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Epoch Sayısı
              </label>
              <input
                type="number"
                min="10"
                max="1000"
                value={trainingParams.epochs}
                onChange={(e) =>
                  setTrainingParams({
                    ...trainingParams,
                    epochs: parseInt(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Batch Size
              </label>
              <input
                type="number"
                min="100"
                max="2000"
                value={trainingParams.batch_size}
                onChange={(e) =>
                  setTrainingParams({
                    ...trainingParams,
                    batch_size: parseInt(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          <button
            onClick={handleTrainModel}
            disabled={isTraining}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isTraining ? "Eğitiliyor..." : "Modeli Eğit"}
          </button>

          {trainingResult && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <h3 className="font-bold text-green-800 mb-2">Eğitim Tamamlandı!</h3>
              <div className="text-sm space-y-1">
                <p><strong>Model ID:</strong> {trainingResult.model_id}</p>
                <p><strong>Süre:</strong> {trainingResult.training_stats?.training_duration_minutes?.toFixed(2)} dakika</p>
                <p><strong>Epoch:</strong> {trainingResult.training_stats?.epochs}</p>
                <p><strong>Eğitim Verisi:</strong> {trainingResult.training_stats?.training_samples} satır, {trainingResult.training_stats?.training_columns} sütun</p>
                <p><strong>Model Boyutu:</strong> {trainingResult.training_stats?.model_size_mb} MB</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Generate Tab */}
      {activeTab === "generate" && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model Seç
            </label>
            <select
              value={generateParams.model_id}
              onChange={(e) =>
                setGenerateParams({ ...generateParams, model_id: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">Model seçin...</option>
              {models.map((model) => (
                <option key={model.model_id} value={model.model_id}>
                  {model.model_id} ({model.training_stats?.trained_at ? new Date(model.training_stats.trained_at).toLocaleString('tr-TR') : 'Bilinmiyor'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Satır Sayısı
            </label>
            <input
              type="number"
              min="1"
              max="100000"
              value={generateParams.num_rows}
              onChange={(e) =>
                setGenerateParams({
                  ...generateParams,
                  num_rows: parseInt(e.target.value),
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="evaluate"
              checked={generateParams.evaluate}
              onChange={(e) =>
                setGenerateParams({
                  ...generateParams,
                  evaluate: e.target.checked,
                })
              }
              className="mr-2"
            />
            <label htmlFor="evaluate" className="text-sm text-gray-700">
              Kalite değerlendirmesi yap
            </label>
          </div>

          <button
            onClick={handleGenerateData}
            disabled={isGenerating || !generateParams.model_id}
            className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isGenerating ? "Üretiliyor..." : "Sentetik Veri Üret"}
          </button>

          {generateResult && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <h3 className="font-bold text-green-800 mb-2">Veri Üretildi!</h3>
              <div className="text-sm space-y-1 mb-4">
                <p><strong>Dosya:</strong> {generateResult.filename}</p>
                <p><strong>Satır Sayısı:</strong> {generateResult.rows_generated}</p>
                <p><strong>Sütun Sayısı:</strong> {generateResult.columns}</p>
              </div>

              <button
                onClick={() => handleDownloadData(generateResult.filename)}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
              >
                İndir
              </button>

              {generateResult.evaluation && (
                <div className="mt-4 p-3 bg-white rounded border">
                  <h4 className="font-bold mb-2">Kalite Değerlendirmesi</h4>
                  <p className="text-sm">
                    <strong>Tamamlanma Skoru:</strong>{" "}
                    {generateResult.evaluation.data_quality?.completeness_score}%
                  </p>
                  <p className="text-sm">
                    <strong>Null Yüzdesi:</strong>{" "}
                    {generateResult.evaluation.data_quality?.null_percentage}%
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Models Tab */}
      {activeTab === "models" && (
        <div className="space-y-4">
          {models.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Henüz eğitilmiş model yok</p>
          ) : (
            <div className="space-y-3">
              {models.map((model) => (
                <div
                  key={model.model_id}
                  className="p-4 border border-gray-200 rounded-md hover:bg-gray-50"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="font-bold text-lg">{model.model_id}</h4>
                      {model.training_stats && (
                        <div className="text-sm text-gray-600 mt-2 space-y-1">
                          <p>
                            <strong>Eğitim Tarihi:</strong>{" "}
                            {new Date(model.training_stats.trained_at).toLocaleString('tr-TR')}
                          </p>
                          <p>
                            <strong>Epoch:</strong> {model.training_stats.epochs}
                          </p>
                          <p>
                            <strong>Veri:</strong> {model.training_stats.training_samples} satır,{" "}
                            {model.training_stats.training_columns} sütun
                          </p>
                          <p>
                            <strong>Süre:</strong>{" "}
                            {model.training_stats.training_duration_minutes?.toFixed(2)} dakika
                          </p>
                          <p>
                            <strong>Boyut:</strong> {model.training_stats.model_size_mb} MB
                          </p>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteModel(model.model_id)}
                      className="ml-4 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                    >
                      Sil
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
