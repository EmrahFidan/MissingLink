# MissingLink - Faz 1: The Core Forge

Gerçek verinin matematiksel ikizini oluşturmak için Deep Learning tabanlı üretim motoru.

## 📋 Proje Açıklaması

MissingLink, CSV tablolarının yapısını öğrenen ve benzer sentetik veri üreten bir sistemdir. CTGAN (Conditional GAN) modeli kullanarak, yüklenen CSV dosyalarının istatistiksel özelliklerini koruyarak yeni veri setleri üretir.

## 🛠️ Teknoloji Stack

- **Backend:** Python 3.10+ | FastAPI | PyTorch | SDV (CTGAN)
- **Frontend:** Next.js 14+ | Tailwind CSS | TypeScript
- **AI Engine:** CTGAN (Conditional Tabular GAN)

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.10 veya üzeri
- Node.js 18 veya üzeri
- npm veya yarn

### 1. Backend Kurulumu (Terminal 1)

```bash
cd backend

# Windows
setup.bat
# veya manuel:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Uygulamayı başlat
run.bat
# veya manuel:
python -m uvicorn app.main:app --reload
```

Backend başarıyla çalışıyorsa: **http://localhost:8000**
API Dokümanları: **http://localhost:8000/docs**

### 2. Frontend Kurulumu (Terminal 2)

```bash
cd frontend

# Paketleri yükle
npm install

# .env.local dosyası oluştur
copy .env.example .env.local

# Uygulamayı başlat
npm run dev
```

Frontend başarıyla çalışıyorsa: **http://localhost:3000**

### 3. Test Etme

1. Frontend'e gidin: http://localhost:3000
2. Bir CSV dosyası yükleyin
3. Sistem dosyayı analiz edecek ve istatistikleri gösterecek

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

- [x] **1.1 Ortam Kurulumu** ✅
  - [x] Python ve Next.js boilerplate
  - [x] FastAPI dosya yükleme endpoint'i
  - [x] Frontend ile backend entegrasyonu
  - [x] GitHub repository
- [ ] **1.2 Şema Tanıma ve Veri Ön İşleme**
  - [x] Pandas ile veri tipi analizi (temel)
  - [ ] Null değerlerin temizlenmesi
  - [ ] Detaylı istatistiksel profil
- [ ] **1.3 CTGAN Model Entegrasyonu**
  - [ ] CTGAN modeli eğitimi
  - [ ] Sentetik veri üretimi
  - [ ] Model performans değerlendirmesi

## 🎯 Başarı Kriteri

Bir CSV yüklendiğinde, sistemin bu veriyi öğrenip benzer yapıda 1000 satır üretebilmesi.

## 📝 Lisans

MIT
