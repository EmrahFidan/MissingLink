"use client";

import { useState } from "react";
import FileUpload from "@/components/FileUpload";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            MissingLink
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            Sentetik Veri Üretim Motoru
          </p>
          <p className="text-sm text-gray-500">
            CSV tablolarından Deep Learning ile matematiksel ikiz veri üretimi
          </p>
        </header>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <FileUpload />
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 max-w-6xl mx-auto">
          <InfoCard
            icon="📊"
            title="Şema Tanıma"
            description="Pandas ile veri tipi analizi ve istatistiksel profil çıkarma"
          />
          <InfoCard
            icon="🧠"
            title="CTGAN Modeli"
            description="Deep Learning ile tabloya özgü sentetik veri üretimi"
          />
          <InfoCard
            icon="⚡"
            title="Hızlı Üretim"
            description="Eğitilen modelden 1000+ satır benzer veri üretimi"
          />
        </div>
      </div>
    </main>
  );
}

function InfoCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-6 text-center hover:shadow-xl transition-shadow">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  );
}
