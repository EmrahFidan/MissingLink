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
  const [trainingProgress, setTrainingProgress] = useState(0);
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
    setTrainingProgress(0);

    // Smooth progress simulation
    const progressInterval = setInterval(() => {
      setTrainingProgress(prev => {
        if (prev >= 95) {
          clearInterval(progressInterval);
          return 95;
        }
        // Slower, more realistic progress
        return prev + Math.random() * 5;
      });
    }, 800);

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
        clearInterval(progressInterval);
        throw new Error("Model eğitimi başarısız oldu");
      }

      const data = await response.json();
      clearInterval(progressInterval);
      setTrainingProgress(100);

      setTimeout(() => {
        setTrainingResult(data);
      }, 300);

      await loadModels();
    } catch (error: any) {
      clearInterval(progressInterval);
      setTrainingProgress(0);
      alert("Hata: " + error.message);
    } finally {
      setTimeout(() => {
        setIsTraining(false);
        setTrainingProgress(0);
      }, 1000);
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
    <div className="glass-effect rounded-xl border border-dark-700 p-6 mt-6">
      <h2 className="text-2xl font-bold text-dark-50 mb-6">CTGAN Model Yönetimi</h2>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab("train")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "train"
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-dark-400 hover:text-dark-200"
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
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-dark-400 hover:text-dark-200"
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
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-dark-400 hover:text-dark-200"
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
              <label className="block text-sm font-medium text-dark-200 mb-2">
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
                className="w-full px-4 py-3 border border-dark-600 bg-dark-900/40 text-dark-50 rounded-lg hover:border-primary-500/50 focus:border-primary-500 transition-colors duration-200 font-medium"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-200 mb-2">
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
                className="w-full px-4 py-3 border border-dark-600 bg-dark-900/40 text-dark-50 rounded-lg hover:border-primary-500/50 focus:border-primary-500 transition-colors duration-200 font-medium"
              />
            </div>
          </div>

          {isTraining && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-dark-200">Training Progress</span>
                <span className="text-primary-400 font-semibold">{Math.round(trainingProgress)}%</span>
              </div>
              <div className="relative h-3 bg-dark-800 rounded-full overflow-hidden border border-dark-700">
                <div
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-500 ease-out rounded-full"
                  style={{ width: `${trainingProgress}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleTrainModel}
            disabled={isTraining}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-xl hover:bg-primary-700 disabled:bg-dark-700 disabled:cursor-not-allowed font-semibold shadow-lg hover:shadow-xl transition-all duration-300 relative overflow-hidden group"
          >
            <span className="relative z-10 flex items-center justify-center gap-2">
              {isTraining ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Model Eğitiliyor...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Start Model Training
                </>
              )}
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
          </button>

          {trainingResult && (
            <div className="mt-6 p-4 glass-effect border border-primary-500/30 bg-primary-500/5 rounded-md">
              <h3 className="font-bold text-primary-300 mb-2">Eğitim Tamamlandı!</h3>
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
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Model Seç
            </label>
            <select
              value={generateParams.model_id}
              onChange={(e) =>
                setGenerateParams({ ...generateParams, model_id: e.target.value })
              }
              className="w-full px-3 py-2 border border-dark-600 bg-dark-900/40 text-dark-50 rounded-md"
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
            <label className="block text-sm font-medium text-dark-200 mb-2">
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
              className="w-full px-4 py-3 border border-dark-600 bg-dark-900/40 text-dark-50 rounded-lg hover:border-primary-500/50 focus:border-primary-500 transition-colors duration-200 font-medium"
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
            <label htmlFor="evaluate" className="text-sm text-dark-200">
              Kalite değerlendirmesi yap
            </label>
          </div>

          <button
            onClick={handleGenerateData}
            disabled={isGenerating || !generateParams.model_id}
            className="w-full bg-secondary-600 text-white py-3 px-4 rounded-md hover:bg-secondary-700 disabled:bg-dark-700 disabled:cursor-not-allowed font-medium"
          >
            {isGenerating ? "Üretiliyor..." : "Sentetik Veri Üret"}
          </button>

          {generateResult && (
            <div className="mt-6 p-4 glass-effect border border-primary-500/30 bg-primary-500/5 rounded-md">
              <h3 className="font-bold text-primary-300 mb-2">Veri Üretildi!</h3>
              <div className="text-sm space-y-1 mb-4">
                <p><strong>Dosya:</strong> {generateResult.filename}</p>
                <p><strong>Satır Sayısı:</strong> {generateResult.rows_generated}</p>
                <p><strong>Sütun Sayısı:</strong> {generateResult.columns}</p>
              </div>

              <button
                onClick={() => handleDownloadData(generateResult.filename)}
                className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700"
              >
                İndir
              </button>

              {generateResult.evaluation && (
                <div className="mt-4 p-3 bg-dark-900/40 rounded-lg border border-dark-700">
                  <h4 className="font-bold mb-2 text-dark-50">Kalite Değerlendirmesi</h4>
                  <p className="text-sm text-dark-200">
                    <strong>Tamamlanma Skoru:</strong>{" "}
                    {generateResult.evaluation.data_quality?.completeness_score}%
                  </p>
                  <p className="text-sm text-dark-200">
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
            <div className="text-center py-16">
              <svg className="w-24 h-24 mx-auto text-dark-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <p className="text-dark-400 text-lg">No trained models yet</p>
              <p className="text-dark-500 text-sm mt-2">Train your first model to get started</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {models.map((model) => (
                <div
                  key={model.model_id}
                  className="glass-effect border border-dark-700 rounded-xl p-5 hover:border-primary-500/30 transition-all duration-300 group relative overflow-hidden"
                >
                  {/* Gradient overlay on hover */}
                  <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

                  <div className="relative z-10">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-primary-500/10 border border-primary-500/30 flex items-center justify-center">
                          <svg className="w-6 h-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                          </svg>
                        </div>
                        <div>
                          <h4 className="font-semibold text-dark-50 text-sm mb-1">Model</h4>
                          <p className="text-xs text-dark-400 font-mono">{model.model_id.split('_').slice(-2).join('_')}</p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteModel(model.model_id)}
                        className="p-2 hover:bg-red-500/10 rounded-lg transition-colors group/delete"
                      >
                        <svg className="w-5 h-5 text-dark-400 group-hover/delete:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>

                    {model.training_stats && (
                      <>
                        {/* Stats Grid */}
                        <div className="grid grid-cols-2 gap-3 mb-4">
                          <div className="bg-dark-900/40 rounded-lg p-3 border border-dark-700/50">
                            <p className="text-dark-400 text-xs mb-1">Dataset</p>
                            <p className="text-dark-50 font-semibold text-sm">
                              {model.training_stats.training_samples.toLocaleString()} rows
                            </p>
                            <p className="text-dark-500 text-xs">{model.training_stats.training_columns} columns</p>
                          </div>

                          <div className="bg-dark-900/40 rounded-lg p-3 border border-dark-700/50">
                            <p className="text-dark-400 text-xs mb-1">Training</p>
                            <p className="text-dark-50 font-semibold text-sm">{model.training_stats.epochs} epochs</p>
                            <p className="text-dark-500 text-xs">{model.training_stats.training_duration_minutes?.toFixed(1)} min</p>
                          </div>
                        </div>

                        {/* Footer Info */}
                        <div className="flex items-center justify-between text-xs pt-3 border-t border-dark-700/50">
                          <div className="flex items-center gap-2 text-dark-400">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>{new Date(model.training_stats.trained_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                          </div>

                          <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 text-dark-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span className="text-dark-400">{model.training_stats.model_size_mb} MB</span>
                          </div>
                        </div>
                      </>
                    )}
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
