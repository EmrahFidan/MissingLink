"use client";

import { useState } from "react";
import axios from "axios";
import DataAnalysis from "./DataAnalysis";
import CTGANManager from "./CTGANManager";
import PIIManager from "./PIIManager";
import DPManager from "./DPManager";
import ValidationReport from "./ValidationReport";

interface UploadResponse {
  message: string;
  data: {
    filename: string;
    original_filename: string;
    file_size_mb: number;
    data_info: {
      total_rows: number;
      total_columns: number;
      column_names: string[];
      memory_usage_mb: number;
      missing_values: Record<string, number>;
    };
    column_types: Record<string, string>;
  };
}

function MetricCard({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="bg-dark-900/40 rounded-lg p-4 border border-dark-700/50">
      <p className="text-dark-300 text-xs mb-1.5 uppercase tracking-wide">{label}</p>
      <p className={`text-dark-50 font-semibold ${mono ? 'font-mono text-sm' : 'text-base'} truncate`}>
        {value}
      </p>
    </div>
  );
}

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Sadece CSV dosyaları yüklenebilir');
        return;
      }
      setFile(selectedFile);
      setError(null);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Lütfen bir dosya seçin');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.post<UploadResponse>(
        `${apiUrl}/api/v1/upload/csv`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setUploadResult(response.data);
      setFile(null);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Dosya yüklenirken bir hata oluştu'
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <label
        htmlFor="file-upload"
        className="border-2 border-dashed border-dark-700 rounded-xl p-8 text-center hover:border-primary-400 hover:bg-dark-900/30 transition-all duration-300 group cursor-pointer block"
      >
        <div className="space-y-4">
          <div className="text-primary-300 group-hover:scale-105 transition-transform">
            <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div>
            <span className="text-primary-300 hover:text-primary-200 font-semibold text-lg transition-colors">
              CSV Dosyası Seç
            </span>
            <input
              id="file-upload"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <p className="text-sm text-dark-400 mt-2">
              veya dosyayı buraya sürükleyin
            </p>
            <p className="text-xs text-dark-500 mt-1">
              Maksimum 100MB • CSV formatı
            </p>
          </div>
        </div>
        {file && (
          <div className="glass-effect rounded-lg p-4 inline-block border border-dark-700 mt-4">
            <div className="flex items-center gap-3">
              <svg className="w-8 h-8 text-primary-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <div className="text-left">
                <p className="text-sm font-medium text-dark-50">
                  {file.name}
                </p>
                <p className="text-xs text-dark-300">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
          </div>
        )}
      </label>

      {/* Upload Button */}
      {file && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="w-full bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl relative overflow-hidden group border border-primary-500/20"
        >
          <span className="relative z-10 flex items-center justify-center gap-2">
            {uploading ? (
              <>
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Yükleniyor...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Yükle ve Analiz Et
              </>
            )}
          </span>
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000"></div>
        </button>
      )}

      {/* Error Display */}
      {error && (
        <div className="glass-effect border-2 border-red-500/50 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="font-semibold text-red-400">Hata Oluştu</p>
              <p className="text-sm text-dark-300 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Display */}
      {uploadResult && (
        <div className="glass-effect border-2 border-primary-400/20 rounded-xl p-6 space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500/15 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-primary-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="font-semibold text-dark-50 text-lg">Upload Successful</p>
              <p className="text-sm text-dark-300">Dataset analysis complete</p>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Dosya Adı"
              value={uploadResult.data.original_filename}
              mono={true}
            />
            <MetricCard
              label="Boyut"
              value={`${uploadResult.data.file_size_mb} MB`}
            />
            <MetricCard
              label="Toplam Satır"
              value={uploadResult.data.data_info.total_rows.toLocaleString()}
            />
            <MetricCard
              label="Toplam Sütun"
              value={uploadResult.data.data_info.total_columns.toString()}
            />
          </div>

          <div>
            <p className="text-dark-300 text-sm font-medium mb-3">Sütunlar</p>
            <div className="flex flex-wrap gap-2">
              {uploadResult.data.data_info.column_names.map((col) => (
                <span
                  key={col}
                  className="bg-secondary-500/10 text-secondary-300 text-xs font-mono px-3 py-1.5 rounded-lg border border-secondary-500/20"
                >
                  {col}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Detailed Analysis */}
      {uploadResult && (
        <DataAnalysis filename={uploadResult.data.filename} />
      )}

      {/* CTGAN Manager */}
      {uploadResult && (
        <CTGANManager filename={uploadResult.data.filename} />
      )}

      {/* PII Manager */}
      {uploadResult && (
        <PIIManager filename={uploadResult.data.filename} />
      )}

      {/* DP Manager */}
      {uploadResult && (
        <DPManager filename={uploadResult.data.filename} />
      )}

      {/* Validation Report */}
      {uploadResult && (
        <ValidationReport filename={uploadResult.data.filename} />
      )}
    </div>
  );
}
