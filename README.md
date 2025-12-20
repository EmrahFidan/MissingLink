# MissingLink - Faz 1: The Core Forge

Gerçek verinin matematiksel ikizini oluşturmak için Deep Learning tabanlı üretim motoru.

## 📋 Proje Açıklaması

MissingLink, CSV tablolarının yapısını öğrenen ve benzer sentetik veri üreten bir sistemdir. CTGAN (Conditional GAN) modeli kullanarak, yüklenen CSV dosyalarının istatistiksel özelliklerini koruyarak yeni veri setleri üretir.

## 🛠️ Teknoloji Stack

- **Backend:** Python 3.10+ | FastAPI | PyTorch | SDV (CTGAN)
- **Frontend:** Next.js 14+ | Tailwind CSS | TypeScript
- **AI Engine:** CTGAN (Conditional Tabular GAN)

## 🚀 Kurulum

### Backend Kurulumu

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Kurulumu

```bash
cd frontend
npm install
npm run dev
```

## 📁 Proje Yapısı

```
MissingLink/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── models/        # Veri modelleri
│   │   ├── services/      # İş mantığı
│   │   └── main.py        # FastAPI uygulaması
│   ├── uploads/           # Yüklenen CSV dosyaları
│   └── requirements.txt
├── frontend/
│   └── (Next.js yapısı)
└── shared/
    └── (Ortak tipler ve yardımcılar)
```

## ✅ Faz 1 İlerleme

- [x] Ortam Kurulumu
- [ ] Şema Tanıma ve Veri Ön İşleme
- [ ] CTGAN Model Entegrasyonu

## 🎯 Başarı Kriteri

Bir CSV yüklendiğinde, sistemin bu veriyi öğrenip benzer yapıda 1000 satır üretebilmesi.

## 📝 Lisans

MIT
