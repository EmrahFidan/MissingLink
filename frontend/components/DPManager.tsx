"use client";

import { useState, useEffect } from "react";

interface DPManagerProps {
  filename: string;
}

export default function DPManager({ filename }: DPManagerProps) {
  const [activeTab, setActiveTab] = useState<"apply" | "k-anonymity" | "recommendation">("apply");
  const [epsilon, setEpsilon] = useState(1.0);
  const [delta, setDelta] = useState(1e-5);
  const [mechanism, setMechanism] = useState<"laplace" | "gaussian">("laplace");
  const [isApplying, setIsApplying] = useState(false);
  const [dpResult, setDpResult] = useState<any>(null);
  const [privacyLevel, setPrivacyLevel] = useState("medium");

  // K-anonymity
  const [quasiIdentifiers, setQuasiIdentifiers] = useState<string[]>([]);
  const [kValue, setKValue] = useState(5);
  const [isCheckingK, setIsCheckingK] = useState(false);
  const [kAnonymityResult, setKAnonymityResult] = useState<any>(null);

  // Recommendation
  const [dataSensitivity, setDataSensitivity] = useState<"low" | "medium" | "high">("medium");
  const [useCase, setUseCase] = useState<"research" | "production" | "public_release">("research");
  const [recommendation, setRecommendation] = useState<any>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // Epsilon değiştiğinde privacy level güncelle
  useEffect(() => {
    if (epsilon < 0.5) setPrivacyLevel("very_high");
    else if (epsilon < 1.0) setPrivacyLevel("high");
    else if (epsilon < 2.0) setPrivacyLevel("medium");
    else if (epsilon < 5.0) setPrivacyLevel("low");
    else setPrivacyLevel("very_low");
  }, [epsilon]);

  // Privacy level renkleri
  const getPrivacyLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      "very_high": "text-secondary-300 glass-effect border border-secondary-500/30 bg-secondary-500/5",
      "high": "text-primary-300 glass-effect border border-primary-500/30 bg-primary-500/10",
      "medium": "text-accent-300 glass-effect border border-accent-500/30 bg-accent-500/10",
      "low": "text-accent-400 glass-effect border border-accent-500/40 bg-accent-500/15",
      "very_low": "text-red-400 glass-effect border border-red-500/30 bg-red-500/10"
    };
    return colors[level] || colors["medium"];
  };

  // Privacy level açıklamaları
  const getPrivacyDescription = (level: string) => {
    const descriptions: Record<string, string> = {
      "very_high": "Çok Yüksek Gizlilik - Re-identification neredeyse imkansız",
      "high": "Yüksek Gizlilik - Güçlü koruma sağlanır",
      "medium": "Dengeli - Gizlilik ve doğruluk dengesi",
      "low": "Düşük Gizlilik - Daha fazla doğruluk",
      "very_low": "Çok Düşük Gizlilik - Yüksek doğruluk ancak risk var"
    };
    return descriptions[level] || descriptions["medium"];
  };

  // DP uygula
  const handleApplyDP = async () => {
    setIsApplying(true);
    setDpResult(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/apply-dp`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename,
          epsilon,
          delta,
          mechanism,
          columns: null, // Tüm numeric sütunlar
        }),
      });

      if (!response.ok) {
        throw new Error("DP uygulaması başarısız oldu");
      }

      const data = await response.json();
      setDpResult(data);
    } catch (error: any) {
      alert("Hata: " + error.message);
    } finally {
      setIsApplying(false);
    }
  };

  // K-anonymity kontrolü
  const handleCheckKAnonymity = async () => {
    if (quasiIdentifiers.length === 0) {
      alert("Lütfen en az bir quasi-identifier sütun seçin");
      return;
    }

    setIsCheckingK(true);
    setKAnonymityResult(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/check-k-anonymity`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename,
          quasi_identifiers: quasiIdentifiers,
          k: kValue,
        }),
      });

      if (!response.ok) {
        throw new Error("K-anonymity kontrolü başarısız");
      }

      const data = await response.json();
      setKAnonymityResult(data.k_anonymity);
    } catch (error: any) {
      alert("Hata: " + error.message);
    } finally {
      setIsCheckingK(false);
    }
  };

  // Epsilon önerisi al
  const handleGetRecommendation = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/get-epsilon-recommendation`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          data_sensitivity: dataSensitivity,
          use_case: useCase,
        }),
      });

      if (!response.ok) {
        throw new Error("Öneri alınamadı");
      }

      const data = await response.json();
      setRecommendation(data.recommendation);

      // Önerilen epsilon'u uygula
      if (data.recommendation.recommended_epsilon) {
        setEpsilon(data.recommendation.recommended_epsilon);
      }
    } catch (error: any) {
      alert("Hata: " + error.message);
    }
  };

  // İndir
  const handleDownload = (path: string) => {
    window.open(`${API_URL}/api/v1/download/${path}`, "_blank");
  };

  return (
    <div className="glass-effect rounded-xl border border-dark-700 p-6 mt-6">
      <h2 className="text-2xl font-bold text-dark-50 mb-6">
        🔒 Differential Privacy (Diferansiyel Gizlilik)
      </h2>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab("apply")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "apply"
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-dark-400 hover:text-dark-200"
          }`}
        >
          DP Uygula
        </button>
        <button
          onClick={() => setActiveTab("k-anonymity")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "k-anonymity"
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-dark-400 hover:text-dark-200"
          }`}
        >
          K-Anonymity
        </button>
        <button
          onClick={() => setActiveTab("recommendation")}
          className={`pb-2 px-4 font-medium ${
            activeTab === "recommendation"
              ? "border-b-2 border-primary-500 text-primary-400"
              : "text-dark-400 hover:text-dark-200"
          }`}
        >
          Epsilon Önerisi
        </button>
      </div>

      {/* Apply DP Tab */}
      {activeTab === "apply" && (
        <div className="space-y-4">
          <div className="glass-effect border border-primary-500/30 bg-primary-500/5 rounded-lg p-4">
            <p className="text-sm text-primary-300">
              <strong>Differential Privacy:</strong> Veriye gürültü ekleyerek
              bireysel kayıtların gizliliğini korur. Epsilon değeri ne kadar küçükse
              gizlilik o kadar yüksektir.
            </p>
          </div>

          {/* Privacy Level Indicator */}
          <div className={`border rounded-lg p-4 ${getPrivacyLevelColor(privacyLevel)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-bold text-lg">Gizlilik Seviyesi</p>
                <p className="text-sm mt-1">{getPrivacyDescription(privacyLevel)}</p>
              </div>
              <div className="text-3xl font-bold">ε = {epsilon.toFixed(2)}</div>
            </div>
          </div>

          {/* Epsilon Slider */}
          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Epsilon (ε) - Privacy Budget
            </label>
            <input
              type="range"
              min="0.1"
              max="10"
              step="0.1"
              value={epsilon}
              onChange={(e) => setEpsilon(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-dark-400 mt-1">
              <span>0.1 (Yüksek Gizlilik)</span>
              <span>10.0 (Düşük Gizlilik)</span>
            </div>
          </div>

          {/* Mechanism Selection */}
          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Gürültü Mekanizması
            </label>
            <div className="flex gap-4">
              <button
                onClick={() => setMechanism("laplace")}
                className={`flex-1 py-2 px-4 rounded border ${
                  mechanism === "laplace"
                    ? "bg-primary-600 text-white border-blue-600"
                    : "bg-dark-900/40 text-dark-50 border-dark-600 hover:bg-dark-900/60"
                }`}
              >
                Laplace
              </button>
              <button
                onClick={() => setMechanism("gaussian")}
                className={`flex-1 py-2 px-4 rounded border ${
                  mechanism === "gaussian"
                    ? "bg-primary-600 text-white border-blue-600"
                    : "bg-dark-900/40 text-dark-50 border-dark-600 hover:bg-dark-900/60"
                }`}
              >
                Gaussian
              </button>
            </div>
          </div>

          <button
            onClick={handleApplyDP}
            disabled={isApplying}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md hover:bg-primary-700 disabled:bg-dark-700 disabled:cursor-not-allowed font-medium"
          >
            {isApplying ? "Uygulanıyor..." : "Differential Privacy Uygula"}
          </button>

          {/* DP Result */}
          {dpResult && (
            <div className="mt-6 p-4 glass-effect border border-primary-500/30 bg-primary-500/5 rounded-md">
              <h3 className="font-bold text-primary-300 mb-2">
                ✅ DP Başarıyla Uygulandı!
              </h3>
              <div className="text-sm space-y-1 mb-4">
                <p><strong>Dosya:</strong> {dpResult.dp_file}</p>
                <p><strong>Epsilon:</strong> {dpResult.dp_report?.epsilon}</p>
                <p><strong>Mekanizma:</strong> {dpResult.dp_report?.mechanism}</p>
                <p><strong>İşlenen Sütun:</strong> {dpResult.dp_report?.columns_processed?.length}</p>
              </div>

              {/* Noise Statistics */}
              {dpResult.dp_report?.noise_statistics && (
                <div className="bg-dark-900/40 rounded-lg border border-dark-700 border p-3 mb-4 max-h-60 overflow-y-auto">
                  <h4 className="font-bold text-sm mb-2">Gürültü İstatistikleri</h4>
                  {Object.entries(dpResult.dp_report.noise_statistics).map(
                    ([col, stats]: [string, any]) => (
                      <div key={col} className="text-xs py-2 border-t">
                        <p className="font-medium">{col}</p>
                        <p>Gürültü: {stats.noise_magnitude?.toFixed(4)}</p>
                        <p>Hata: {(stats.relative_error * 100)?.toFixed(2)}%</p>
                      </div>
                    )
                  )}
                </div>
              )}

              <button
                onClick={() => handleDownload(dpResult.dp_path)}
                className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700"
              >
                İndir
              </button>
            </div>
          )}
        </div>
      )}

      {/* K-Anonymity Tab */}
      {activeTab === "k-anonymity" && (
        <div className="space-y-4">
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <p className="text-sm text-accent-300">
              <strong>K-Anonymity:</strong> Her kayıt grubunda en az K adet kayıt
              olmasını garanti eder. Bu re-identification riskini azaltır.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              K Değeri (Minimum Grup Büyüklüğü)
            </label>
            <input
              type="number"
              min="2"
              max="100"
              value={kValue}
              onChange={(e) => setKValue(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-dark-600 bg-dark-900/40 text-dark-50 rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Quasi-Identifier Sütunlar (Örnek: age, zipcode, gender)
            </label>
            <input
              type="text"
              placeholder="Virgülle ayırın: age,city,gender"
              onChange={(e) => setQuasiIdentifiers(e.target.value.split(",").map(s => s.trim()))}
              className="w-full px-3 py-2 border border-dark-600 bg-dark-900/40 text-dark-50 rounded-md"
            />
          </div>

          <button
            onClick={handleCheckKAnonymity}
            disabled={isCheckingK}
            className="w-full bg-accent-600 text-white py-3 px-4 rounded-md hover:bg-accent-700 disabled:bg-dark-700 disabled:cursor-not-allowed font-medium"
          >
            {isCheckingK ? "Kontrol Ediliyor..." : "K-Anonymity Kontrol Et"}
          </button>

          {/* K-Anonymity Result */}
          {kAnonymityResult && (
            <div className={`mt-6 p-4 rounded-md border ${
              kAnonymityResult.is_k_anonymous
                ? "glass-effect border border-secondary-500/30 bg-secondary-500/5"
                : "bg-red-50 border-red-200"
            }`}>
              <h3 className={`font-bold mb-2 ${
                kAnonymityResult.is_k_anonymous ? "text-secondary-300" : "text-red-400"
              }`}>
                {kAnonymityResult.is_k_anonymous ? "✅ K-Anonymous" : "⚠️ Risk Var"}
              </h3>
              <div className="text-sm space-y-1">
                <p><strong>K Değeri:</strong> {kAnonymityResult.k_value}</p>
                <p><strong>Risk Altındaki Kayıt:</strong> {kAnonymityResult.vulnerable_records} ({kAnonymityResult.vulnerable_percentage?.toFixed(2)}%)</p>
                <p><strong>En Küçük Grup:</strong> {kAnonymityResult.smallest_group_size}</p>
                <p className="mt-2 pt-2 border-t"><strong>Öneri:</strong> {kAnonymityResult.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommendation Tab */}
      {activeTab === "recommendation" && (
        <div className="space-y-4">
          <div className="glass-effect border border-secondary-500/30 bg-secondary-500/5 rounded-lg p-4">
            <p className="text-sm text-secondary-300">
              <strong>Epsilon Önerisi:</strong> Kullanım senaryonuza ve veri hassasiyetinize
              göre optimal epsilon değeri önerilir.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Veri Hassasiyeti
            </label>
            <select
              value={dataSensitivity}
              onChange={(e) => setDataSensitivity(e.target.value as any)}
              className="w-full px-3 py-2 border border-dark-600 bg-dark-900/40 text-dark-50 rounded-md"
            >
              <option value="low">Düşük (Genel istatistikler)</option>
              <option value="medium">Orta (Kişisel veriler)</option>
              <option value="high">Yüksek (Hassas bilgiler)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-200 mb-2">
              Kullanım Senaryosu
            </label>
            <select
              value={useCase}
              onChange={(e) => setUseCase(e.target.value as any)}
              className="w-full px-3 py-2 border border-dark-600 bg-dark-900/40 text-dark-50 rounded-md"
            >
              <option value="research">Araştırma</option>
              <option value="production">Production Sistemi</option>
              <option value="public_release">Halka Açık Yayın</option>
            </select>
          </div>

          <button
            onClick={handleGetRecommendation}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-md hover:bg-primary-700 font-medium"
          >
            Öneri Al
          </button>

          {/* Recommendation Result */}
          {recommendation && (
            <div className="mt-6 p-4 glass-effect border border-secondary-500/30 bg-secondary-500/5 rounded-md">
              <h3 className="font-bold text-secondary-300 mb-2">Epsilon Önerisi</h3>
              <div className="text-sm space-y-1">
                <p><strong>Önerilen Epsilon:</strong> {recommendation.recommended_epsilon}</p>
                <p><strong>Gizlilik Seviyesi:</strong> {recommendation.privacy_level}</p>
                <p className="mt-2 pt-2 border-t">{recommendation.explanation}</p>
              </div>
              <button
                onClick={() => {
                  setEpsilon(recommendation.recommended_epsilon);
                  setActiveTab("apply");
                }}
                className="w-full mt-3 bg-secondary-600 text-white py-2 px-4 rounded-md hover:bg-secondary-700"
              >
                Bu Epsilon&apos;u Kullan
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
