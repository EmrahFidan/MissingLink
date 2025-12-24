"use client";

import { useState } from "react";
import FileUpload from "@/components/FileUpload";

export default function Home() {
  return (
    <main className="min-h-screen relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-grid-pattern opacity-20"></div>

      <div className="container mx-auto px-4 py-8 lg:py-16 relative z-10">
        {/* Header */}
        <header className="text-center mb-12 lg:mb-16">
          <div className="inline-flex items-center gap-3 mb-6 px-4 py-2 rounded-full glass-effect">
            <div className="w-2 h-2 rounded-full bg-primary-500 animate-pulse"></div>
            <span className="text-dark-300 text-sm font-medium">AI-Powered Synthetic Data Platform</span>
          </div>

          <h1 className="text-5xl lg:text-7xl font-bold mb-6">
            <span className="bg-gradient-to-r from-primary-400 via-primary-500 to-secondary-500 bg-clip-text text-transparent">
              MissingLink
            </span>
          </h1>

          <p className="text-xl lg:text-2xl text-dark-200 mb-4 font-light">
            Deep Learning Tabanlı Sentetik Veri Motoru
          </p>

          <p className="text-dark-400 max-w-2xl mx-auto leading-relaxed">
            CSV tablolarınızdan CTGAN ile matematiksel olarak benzer,
            <span className="text-primary-400 font-medium"> gizlilik korumalı </span>
            sentetik veriler üretin
          </p>
        </header>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto">
          <div className="glass-effect rounded-2xl p-6 lg:p-8 border border-dark-700">
            <FileUpload />
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-16 max-w-7xl mx-auto">
          <FeatureCard
            icon={
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
            title="Otomatik Şema Analizi"
            description="Pandas ile veri tiplerini otomatik tanıma ve istatistiksel profil çıkarma"
            metric="<50ms"
          />

          <FeatureCard
            icon={
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            }
            title="CTGAN Modeli"
            description="Deep Learning ile tabloya özgü sentetik veri üretimi"
            metric="300 epochs"
          />

          <FeatureCard
            icon={
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            }
            title="Gizlilik Koruması"
            description="PII detection, k-anonymity ve differential privacy"
            metric="GDPR Ready"
          />

          <FeatureCard
            icon={
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            title="Hızlı Üretim"
            description="Eğitilen modelden 1000+ satır gerçekçi veri"
            metric="~2s/100 rows"
          />
        </div>

        {/* Stats */}
        <div className="mt-16 max-w-4xl mx-auto">
          <div className="grid grid-cols-3 gap-8 glass-effect rounded-2xl p-8 text-center">
            <StatCard value="82.6%" label="Ortalama Benzerlik" />
            <StatCard value="<100ms" label="API Yanıt Süresi" />
            <StatCard value="99.9%" label="Veri Kalitesi" />
          </div>
        </div>
      </div>
    </main>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  metric
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  metric: string;
}) {
  return (
    <div className="glass-effect rounded-xl p-6 card-hover group border border-dark-700">
      <div className="text-primary-400 mb-4 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-dark-100">{title}</h3>
        <span className="text-xs font-mono text-primary-400 bg-primary-500/10 px-2 py-1 rounded">
          {metric}
        </span>
      </div>
      <p className="text-sm text-dark-400 leading-relaxed">{description}</p>
    </div>
  );
}

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="text-3xl font-bold text-primary-400 mb-2">{value}</div>
      <div className="text-sm text-dark-400 font-medium">{label}</div>
    </div>
  );
}
