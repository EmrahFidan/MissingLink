"use client";

import { useState } from "react";
import axios from "axios";

interface ColumnProfile {
  type: string;
  null_count: number;
  null_percentage: number;
  mean?: number;
  median?: number;
  std?: number;
  min?: number;
  max?: number;
  outlier_count?: number;
  outlier_percentage?: number;
  unique_count?: number;
  mode?: string;
  top_values?: Record<string, number>;
}

interface DataProfile {
  dataset_info: {
    total_rows: number;
    total_columns: number;
    memory_usage_mb: number;
    file_size_mb: number;
  };
  column_types: Record<string, string>;
  missing_values: {
    total_missing_values: number;
    columns_with_missing: number;
    completeness_score: number;
    missing_by_column: Record<string, { count: number; percentage: number }>;
  };
  column_profiles: Record<string, ColumnProfile>;
  correlations?: {
    high_correlations: Array<{
      column1: string;
      column2: string;
      correlation: number;
    }>;
  };
}

interface Props {
  filename: string;
}

export default function DataAnalysis({ filename }: Props) {
  const [profile, setProfile] = useState<DataProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);

  const analyzeData = async () => {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.get(
        `${apiUrl}/api/v1/analyze/${filename}`
      );

      setProfile(response.data.profile);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Analiz sırasında bir hata oluştu'
      );
    } finally {
      setLoading(false);
    }
  };

  if (!profile) {
    return (
      <div className="mt-6">
        <button
          onClick={analyzeData}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Detaylı Analiz Yapılıyor...' : 'Detaylı Analiz Yap'}
        </button>
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <p className="font-medium">Hata</p>
            <p className="text-sm">{error}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-6">
      {/* Dataset Info */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          📊 Veri Seti Bilgileri
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Toplam Satır"
            value={profile.dataset_info.total_rows.toLocaleString()}
          />
          <StatCard
            label="Toplam Sütun"
            value={profile.dataset_info.total_columns}
          />
          <StatCard
            label="Hafıza Kullanımı"
            value={`${profile.dataset_info.memory_usage_mb} MB`}
          />
          <StatCard
            label="Dosya Boyutu"
            value={`${profile.dataset_info.file_size_mb} MB`}
          />
        </div>
      </div>

      {/* Missing Values */}
      {profile.missing_values.total_missing_values > 0 && (
        <div className="bg-yellow-50 rounded-xl p-6 border border-yellow-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            ⚠️ Eksik Değerler
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <StatCard
              label="Toplam Eksik"
              value={profile.missing_values.total_missing_values}
            />
            <StatCard
              label="Etkilenen Sütun"
              value={profile.missing_values.columns_with_missing}
            />
            <StatCard
              label="Tamlık Skoru"
              value={`${profile.missing_values.completeness_score}%`}
            />
          </div>
          {Object.keys(profile.missing_values.missing_by_column).length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Sütun Bazında:</p>
              <div className="space-y-2">
                {Object.entries(profile.missing_values.missing_by_column).map(([col, data]) => (
                  <div key={col} className="flex items-center justify-between text-sm">
                    <span className="font-medium text-gray-900">{col}</span>
                    <span className="text-gray-600">
                      {data.count} eksik ({data.percentage}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* High Correlations */}
      {profile.correlations?.high_correlations && profile.correlations.high_correlations.length > 0 && (
        <div className="bg-purple-50 rounded-xl p-6 border border-purple-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            🔗 Yüksek Korelasyonlar
          </h3>
          <div className="space-y-2">
            {profile.correlations.high_correlations.map((corr, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm bg-white rounded-lg p-3">
                <span className="font-medium text-gray-900">
                  {corr.column1} ↔ {corr.column2}
                </span>
                <span className={`font-bold ${corr.correlation > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {corr.correlation > 0 ? '+' : ''}{corr.correlation}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Column Profiles */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📋 Sütun Profilleri
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(profile.column_profiles).map(([colName, colData]) => (
            <ColumnCard
              key={colName}
              name={colName}
              data={colData}
              onClick={() => setSelectedColumn(colName)}
            />
          ))}
        </div>
      </div>

      {/* Selected Column Details */}
      {selectedColumn && profile.column_profiles[selectedColumn] && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              🔍 {selectedColumn} - Detaylı Analiz
            </h3>
            <button
              onClick={() => setSelectedColumn(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          <ColumnDetails data={profile.column_profiles[selectedColumn]} />
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-lg p-4 shadow-sm">
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-900">{value}</p>
    </div>
  );
}

function ColumnCard({ name, data, onClick }: { name: string; data: ColumnProfile; onClick: () => void }) {
  const typeColors: Record<string, string> = {
    integer: 'bg-blue-100 text-blue-800',
    float: 'bg-green-100 text-green-800',
    categorical: 'bg-purple-100 text-purple-800',
    text: 'bg-yellow-100 text-yellow-800',
    boolean: 'bg-pink-100 text-pink-800',
    datetime: 'bg-indigo-100 text-indigo-800',
  };

  return (
    <button
      onClick={onClick}
      className="bg-gray-50 rounded-lg p-4 text-left hover:bg-gray-100 transition-colors border border-gray-200"
    >
      <div className="flex items-center justify-between mb-2">
        <p className="font-medium text-gray-900 truncate">{name}</p>
        <span className={`text-xs px-2 py-1 rounded ${typeColors[data.type] || 'bg-gray-100 text-gray-800'}`}>
          {data.type}
        </span>
      </div>
      {data.null_count > 0 && (
        <p className="text-xs text-red-600">
          {data.null_percentage}% eksik
        </p>
      )}
      {data.outlier_count !== undefined && data.outlier_count > 0 && (
        <p className="text-xs text-orange-600">
          {data.outlier_count} outlier
        </p>
      )}
    </button>
  );
}

function ColumnDetails({ data }: { data: ColumnProfile }) {
  return (
    <div className="space-y-4">
      {/* Numeric columns */}
      {data.mean !== undefined && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <DetailItem label="Ortalama" value={data.mean.toFixed(2)} />
          <DetailItem label="Medyan" value={data.median?.toFixed(2)} />
          <DetailItem label="Std. Sapma" value={data.std?.toFixed(2)} />
          <DetailItem label="Min" value={data.min?.toFixed(2)} />
          <DetailItem label="Max" value={data.max?.toFixed(2)} />
          {data.outlier_count !== undefined && (
            <DetailItem
              label="Outlier"
              value={`${data.outlier_count} (${data.outlier_percentage}%)`}
            />
          )}
        </div>
      )}

      {/* Categorical columns */}
      {data.unique_count !== undefined && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            Benzersiz Değerler: {data.unique_count}
          </p>
          {data.mode && <p className="text-sm text-gray-600">Mod: {data.mode}</p>}
          {data.top_values && (
            <div className="mt-3">
              <p className="text-sm font-medium text-gray-700 mb-2">En Sık Değerler:</p>
              <div className="space-y-1">
                {Object.entries(data.top_values).slice(0, 5).map(([val, count]) => (
                  <div key={val} className="flex items-center justify-between text-sm bg-white rounded px-3 py-2">
                    <span className="text-gray-900">{val}</span>
                    <span className="text-gray-600">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string | number | undefined }) {
  if (value === undefined) return null;

  return (
    <div className="bg-white rounded-lg p-3">
      <p className="text-xs text-gray-600">{label}</p>
      <p className="text-sm font-semibold text-gray-900">{value}</p>
    </div>
  );
}
