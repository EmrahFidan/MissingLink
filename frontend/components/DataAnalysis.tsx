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
          className="w-full bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl border border-primary-500/20"
        >
          <span className="flex items-center justify-center gap-2">
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Detailed Analysis Running...
              </>
            ) : (
              'Run Detailed Analysis'
            )}
          </span>
        </button>
        {error && (
          <div className="mt-4 glass-effect border-2 border-red-500/50 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-semibold text-red-400">Error</p>
                <p className="text-sm text-dark-300 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-6">
      {/* Dataset Info */}
      <div className="glass-effect rounded-xl p-6 border border-dark-700">
        <h3 className="text-lg font-semibold text-dark-50 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Dataset Information
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Total Rows"
            value={profile.dataset_info.total_rows.toLocaleString()}
          />
          <StatCard
            label="Total Columns"
            value={profile.dataset_info.total_columns}
          />
          <StatCard
            label="Memory Usage"
            value={`${profile.dataset_info.memory_usage_mb} MB`}
          />
          <StatCard
            label="File Size"
            value={`${profile.dataset_info.file_size_mb} MB`}
          />
        </div>
      </div>

      {/* Missing Values */}
      {profile.missing_values.total_missing_values > 0 && (
        <div className="glass-effect rounded-xl p-6 border border-accent-500/30 bg-accent-500/5">
          <h3 className="text-lg font-semibold text-dark-50 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Missing Values
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <StatCard
              label="Total Missing"
              value={profile.missing_values.total_missing_values}
            />
            <StatCard
              label="Affected Columns"
              value={profile.missing_values.columns_with_missing}
            />
            <StatCard
              label="Completeness Score"
              value={`${profile.missing_values.completeness_score}%`}
            />
          </div>
          {Object.keys(profile.missing_values.missing_by_column).length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-dark-200 mb-2">By Column:</p>
              <div className="space-y-2">
                {Object.entries(profile.missing_values.missing_by_column).map(([col, data]) => (
                  <div key={col} className="flex items-center justify-between text-sm bg-dark-900/40 rounded-lg px-3 py-2">
                    <span className="font-medium text-dark-50">{col}</span>
                    <span className="text-dark-300">
                      {data.count} missing ({data.percentage}%)
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
        <div className="glass-effect rounded-xl p-6 border border-primary-500/30 bg-primary-500/5">
          <h3 className="text-lg font-semibold text-dark-50 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            High Correlations
          </h3>
          <div className="space-y-2">
            {profile.correlations.high_correlations.map((corr, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm bg-dark-900/40 rounded-lg p-3">
                <span className="font-medium text-dark-50">
                  {corr.column1} ↔ {corr.column2}
                </span>
                <span className={`font-bold ${corr.correlation > 0 ? 'text-secondary-400' : 'text-accent-400'}`}>
                  {corr.correlation > 0 ? '+' : ''}{corr.correlation}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Column Profiles */}
      <div className="glass-effect rounded-xl p-6 border border-dark-700">
        <h3 className="text-lg font-semibold text-dark-50 mb-4">
          Column Profiles
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
        <div className="glass-effect rounded-xl p-6 border border-primary-500/30 bg-primary-500/5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-dark-50 flex items-center gap-2">
              <svg className="w-5 h-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {selectedColumn} - Detailed Analysis
            </h3>
            <button
              onClick={() => setSelectedColumn(null)}
              className="text-dark-400 hover:text-dark-200 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
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
    <div className="bg-dark-900/40 rounded-lg p-4 border border-dark-700/50">
      <p className="text-dark-300 text-xs mb-1.5 uppercase tracking-wide">{label}</p>
      <p className="text-dark-50 font-semibold text-base truncate">{value}</p>
    </div>
  );
}

function ColumnCard({ name, data, onClick }: { name: string; data: ColumnProfile; onClick: () => void }) {
  const typeColors: Record<string, string> = {
    integer: 'bg-secondary-500/20 text-secondary-300 border-secondary-500/30',
    float: 'bg-secondary-500/20 text-secondary-300 border-secondary-500/30',
    categorical: 'bg-primary-500/20 text-primary-300 border-primary-500/30',
    text: 'bg-accent-500/20 text-accent-300 border-accent-500/30',
    boolean: 'bg-primary-500/20 text-primary-300 border-primary-500/30',
    datetime: 'bg-secondary-500/20 text-secondary-300 border-secondary-500/30',
  };

  return (
    <button
      onClick={onClick}
      className="bg-dark-900/40 rounded-lg p-4 text-left hover:bg-dark-900/60 transition-colors border border-dark-700/50 hover:border-primary-500/30"
    >
      <div className="flex items-center justify-between mb-2">
        <p className="font-medium text-dark-50 truncate">{name}</p>
        <span className={`text-xs px-2 py-1 rounded border ${typeColors[data.type] || 'bg-dark-800/50 text-dark-300 border-dark-600'}`}>
          {data.type}
        </span>
      </div>
      {data.null_count > 0 && (
        <p className="text-xs text-accent-400">
          {data.null_percentage}% missing
        </p>
      )}
      {data.outlier_count !== undefined && data.outlier_count > 0 && (
        <p className="text-xs text-accent-400">
          {data.outlier_count} outliers
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
          <DetailItem label="Mean" value={data.mean.toFixed(2)} />
          <DetailItem label="Median" value={data.median?.toFixed(2)} />
          <DetailItem label="Std Dev" value={data.std?.toFixed(2)} />
          <DetailItem label="Min" value={data.min?.toFixed(2)} />
          <DetailItem label="Max" value={data.max?.toFixed(2)} />
          {data.outlier_count !== undefined && (
            <DetailItem
              label="Outliers"
              value={`${data.outlier_count} (${data.outlier_percentage}%)`}
            />
          )}
        </div>
      )}

      {/* Categorical columns */}
      {data.unique_count !== undefined && (
        <div>
          <p className="text-sm font-medium text-dark-200 mb-2">
            Unique Values: {data.unique_count}
          </p>
          {data.mode && <p className="text-sm text-dark-300">Mode: {data.mode}</p>}
          {data.top_values && (
            <div className="mt-3">
              <p className="text-sm font-medium text-dark-200 mb-2">Most Frequent:</p>
              <div className="space-y-1">
                {Object.entries(data.top_values).slice(0, 5).map(([val, count]) => (
                  <div key={val} className="flex items-center justify-between text-sm bg-dark-900/40 rounded px-3 py-2">
                    <span className="text-dark-50">{val}</span>
                    <span className="text-dark-300">{count}</span>
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
    <div className="bg-dark-900/40 rounded-lg p-3 border border-dark-700/50">
      <p className="text-xs text-dark-300 uppercase tracking-wide">{label}</p>
      <p className="text-sm font-semibold text-dark-50 mt-1">{value}</p>
    </div>
  );
}
