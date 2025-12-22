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
      <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary-500 transition-colors">
        <div className="space-y-4">
          <div className="text-6xl">📁</div>
          <div>
            <label
              htmlFor="file-upload"
              className="cursor-pointer text-primary-600 hover:text-primary-700 font-semibold"
            >
              Dosya Seç
            </label>
            <input
              id="file-upload"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <p className="text-sm text-gray-500 mt-2">
              veya dosyayı buraya sürükleyin
            </p>
          </div>
          {file && (
            <div className="bg-gray-50 rounded-lg p-4 inline-block">
              <p className="text-sm font-medium text-gray-700">
                {file.name}
              </p>
              <p className="text-xs text-gray-500">
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Upload Button */}
      {file && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Yükleniyor...' : 'Yükle ve Analiz Et'}
        </button>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-medium">Hata</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Success Display */}
      {uploadResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 space-y-4">
          <div className="flex items-center gap-2 text-green-800">
            <span className="text-2xl">✅</span>
            <p className="font-semibold">Dosya Başarıyla Yüklendi!</p>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Dosya Adı</p>
              <p className="font-medium text-gray-900">
                {uploadResult.data.original_filename}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Boyut</p>
              <p className="font-medium text-gray-900">
                {uploadResult.data.file_size_mb} MB
              </p>
            </div>
            <div>
              <p className="text-gray-600">Toplam Satır</p>
              <p className="font-medium text-gray-900">
                {uploadResult.data.data_info.total_rows.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Toplam Sütun</p>
              <p className="font-medium text-gray-900">
                {uploadResult.data.data_info.total_columns}
              </p>
            </div>
          </div>

          <div>
            <p className="text-gray-600 text-sm mb-2">Sütunlar</p>
            <div className="flex flex-wrap gap-2">
              {uploadResult.data.data_info.column_names.map((col) => (
                <span
                  key={col}
                  className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
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
