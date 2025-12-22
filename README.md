# MissingLink - Deep Learning Sentetik Veri Üretim Motoru

Gerçek verinin matematiksel ikizini oluşturmak için Deep Learning tabanlı sentetik veri üretim platformu.

---

## 🎬 Portfolio Demo

**🌐 Live Frontend:** [https://missing-link-mk1wy5kca-emrahfidans-projects.vercel.app/](https://missing-link-mk1wy5kca-emrahfidans-projects.vercel.app/)

**🎥 Demo Video:** [Coming Soon - YouTube/Loom Link]

**💻 Source Code:** [GitHub Repository](https://github.com/EmrahFidan/MissingLink)

> **Note:** Backend requires significant computational resources (PyTorch, CTGAN) and runs locally. See [Local Setup](#-hızlı-başlangıç) for full functionality demonstration.

---

## 📋 Proje Açıklaması

MissingLink, CSV tablolarının yapısını öğrenen ve benzer sentetik veri üreten kapsamlı bir sistemdir. CTGAN (Conditional GAN) modeli kullanarak, yüklenen CSV dosyalarının istatistiksel özelliklerini koruyarak yeni veri setleri üretir. PII tespiti, anonymization, differential privacy ve kalite değerlendirme özellikleriyle production-ready bir çözümdür.

## 🛠️ Teknoloji Stack

- **Backend:** Python 3.10+ | FastAPI | PyTorch | SDV (CTGAN) | Celery | Redis
- **Frontend:** Next.js 14+ | Tailwind CSS | TypeScript
- **AI Engine:** CTGAN (Conditional Tabular GAN)
- **Privacy:** Presidio (PII Detection) | Faker (Anonymization) | diffprivlib (Differential Privacy)
- **Deployment:** Docker | Docker Compose | Flower (Celery Monitoring)

## 🚀 Hızlı Başlangıç

### Gereksinimler
- **Lokal Development:** Python 3.10+, Node.js 18+, Redis
- **Production:** Docker, Docker Compose

### Lokal Development

#### 1. Backend Kurulumu (Terminal 1)

```bash
cd backend

# Windows
setup.bat
# veya manuel:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Uygulamayı başlat
run.bat
# veya manuel:
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend: **http://127.0.0.1:8000**
API Docs: **http://127.0.0.1:8000/docs**

#### 2. Redis Başlatma (Terminal 2)

```bash
# Docker ile Redis
docker run -p 6379:6379 redis:7-alpine
```

#### 3. Celery Workers (Terminal 3)

```bash
cd backend

# Windows
scripts\start_workers.bat

# Linux/Mac
bash scripts/start_workers.sh
```

#### 4. Flower Monitoring (Terminal 4)

```bash
cd backend

# Windows
scripts\start_flower.bat

# Linux/Mac
bash scripts/start_flower.sh
```

Flower: **http://localhost:5555**

#### 5. Frontend Kurulumu (Terminal 5)

```bash
cd frontend

# Paketleri yükle
npm install

# .env.local oluştur
copy .env.example .env.local  # Windows
cp .env.example .env.local    # Linux/Mac

# Frontend'i başlat
npm run dev
```

Frontend: **http://localhost:3000**

### Production Deployment (Docker)

```bash
# Tüm servisleri başlat
docker-compose up -d

# Servisleri kontrol et
docker-compose ps

# Logları izle
docker-compose logs -f
```

Detaylı deployment bilgisi için: [DEPLOYMENT.md](DEPLOYMENT.md)

## 📁 Proje Yapısı

```
MissingLink/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── upload.py         # CSV yükleme
│   │   │   ├── analysis.py       # Veri analizi
│   │   │   ├── ctgan.py          # CTGAN sync API
│   │   │   ├── async_ctgan.py    # CTGAN async API
│   │   │   ├── pii.py            # PII detection/anonymization
│   │   │   ├── dp.py             # Differential Privacy
│   │   │   └── validation.py     # Similarity & Utility
│   │   ├── services/         # İş mantığı
│   │   │   ├── data_profiler.py      # İstatistiksel analiz
│   │   │   ├── data_cleaner.py       # Veri temizleme
│   │   │   ├── ctgan_trainer.py      # CTGAN eğitimi
│   │   │   ├── pii_detector.py       # PII tespiti
│   │   │   ├── differential_privacy.py # DP implementasyonu
│   │   │   ├── similarity_report.py  # Benzerlik analizi
│   │   │   └── utility_score.py      # ML utility değerlendirme
│   │   ├── tasks/            # Celery async tasks
│   │   │   ├── ctgan_tasks.py        # CTGAN async işlemleri
│   │   │   └── processing_tasks.py   # Veri işleme async
│   │   ├── celery_config.py  # Celery yapılandırması
│   │   └── main.py           # FastAPI uygulaması
│   ├── scripts/              # Başlatma scriptleri
│   │   ├── start_workers.bat     # Windows Celery workers
│   │   ├── start_workers.sh      # Linux/Mac Celery workers
│   │   ├── start_flower.bat      # Windows Flower
│   │   └── start_flower.sh       # Linux/Mac Flower
│   ├── Dockerfile            # Backend Docker image
│   ├── Dockerfile.worker     # Celery worker Docker image
│   └── requirements.txt
├── frontend/
│   ├── components/
│   │   ├── FileUpload.tsx        # Dosya yükleme UI
│   │   ├── DataAnalysis.tsx      # Veri analiz UI
│   │   ├── CTGANManager.tsx      # CTGAN yönetim UI
│   │   ├── PIIManager.tsx        # PII yönetim UI
│   │   ├── DPManager.tsx         # Differential Privacy UI
│   │   └── ValidationReport.tsx  # Kalite değerlendirme UI
│   └── (Next.js yapısı)
├── docker-compose.yml        # Orchestration
├── DEPLOYMENT.md             # Deployment guide
└── README.md
```

## 🎯 Özellikler

### Faz 1: Temel Veri İşleme ve CTGAN
- ✅ CSV dosya yükleme ve analiz
- ✅ İstatistiksel veri profilleme
- ✅ Veri temizleme ve ön işleme
- ✅ CTGAN model eğitimi
- ✅ Sentetik veri üretimi
- ✅ Model kaydetme/yükleme
- ✅ Kalite değerlendirmesi

### Faz 2: Privacy ve Güvenlik
- ✅ **PII Detection (2.1)**
  - Presidio ile otomatik PII tespiti
  - Çoklu dil desteği (Türkçe, İngilizce)
  - Kolon bazlı PII analizi
- ✅ **Anonymization (2.1)**
  - Faker ile sentetik veri değiştirme
  - Tutarlı anonymization
  - Korunmuş veri ilişkileri
- ✅ **Differential Privacy (2.2)**
  - Laplace ve Gaussian noise mekanizmaları
  - Epsilon-based privacy budget
  - K-anonymity validation
  - Privacy risk assessment

### Faz 3: Kalite Değerlendirme
- ✅ **Similarity Report (3.1)**
  - Statistical similarity metrics
  - Korelasyon karşılaştırması
  - Distribüsyon analizi
  - Histogram visualizations
- ✅ **Utility Score (3.2)**
  - ML-based comparison (RandomForest)
  - Classification & Regression support
  - Feature importance analysis
  - Prediction accuracy metrics
- ✅ **Frontend UI (3.3)**
  - Dual-tab validation interface
  - Interactive charts
  - Detailed metric displays

### Faz 4: Asenkron İşleme ve Deployment
- ✅ **Asenkron İşleme (4.1)**
  - Celery + Redis entegrasyonu
  - Async CTGAN training & generation
  - Async data processing tasks
  - Real-time progress tracking
  - Flower monitoring dashboard
- ✅ **Production Deployment (4.2)**
  - Docker containerization
  - Docker Compose orchestration
  - Production environment configs
  - Health checks & monitoring
  - Comprehensive deployment docs

## 🔄 Kullanım Senaryoları

### 1. Temel Sentetik Veri Üretimi
1. CSV dosyası yükle
2. Veri analizi ve temizleme yap
3. CTGAN modeli eğit
4. Sentetik veri üret
5. Kalite değerlendirmesi yap

### 2. Privacy-Preserving Veri Üretimi
1. CSV dosyası yükle
2. PII tespiti yap
3. Gerekirse anonymize et
4. Differential Privacy uygula
5. CTGAN ile sentetik veri üret
6. Privacy-aware kalite kontrolü

### 3. Production Async Pipeline
1. CSV dosyasını async upload et
2. Async data profiling ve cleaning
3. Async CTGAN training (long-running)
4. Async synthetic data generation
5. Real-time progress monitoring (Flower)
6. Download results

## 📊 API Endpoints

### Sync Endpoints
- `POST /api/v1/upload` - CSV dosya yükleme
- `POST /api/v1/analysis/profile` - Veri profilleme
- `POST /api/v1/ctgan/train` - Model eğitimi
- `POST /api/v1/ctgan/generate` - Veri üretimi
- `POST /api/v1/pii/detect` - PII tespiti
- `POST /api/v1/pii/anonymize` - Anonymization
- `POST /api/v1/dp/apply` - Differential Privacy
- `POST /api/v1/validation/similarity` - Similarity report
- `POST /api/v1/validation/utility` - Utility score

### Async Endpoints (Faz 4.1)
- `POST /api/v1/async/train` - Async CTGAN training
- `POST /api/v1/async/generate` - Async data generation
- `POST /api/v1/async/pipeline` - Full async pipeline
- `GET /api/v1/async/task/{task_id}` - Task status
- `GET /api/v1/async/result/{task_id}` - Task result
- `DELETE /api/v1/async/task/{task_id}` - Cancel task
- `GET /api/v1/async/tasks` - List active tasks

## 🔒 Güvenlik ve Privacy

### Privacy Features
- **PII Detection**: Email, telefon, adres, TC kimlik, kredi kartı
- **Anonymization**: Tutarlı sentetik veri değiştirme
- **Differential Privacy**: ε-based noise injection
- **K-Anonymity**: Grup bazlı anonimleştirme validation

### Security Best Practices
- Güvenli environment variable yönetimi
- CORS konfigürasyonu
- File upload size limits
- Input validation
- API rate limiting (önerilir)

## 📈 Monitoring

### Flower Dashboard (http://localhost:5555)
- Active tasks monitoring
- Worker status ve health
- Task history ve statistics
- Queue sizes ve throughput
- Failed task inspection

### Metrics
- Task success/failure rates
- Average task duration
- Worker resource usage
- Queue latency
- System health status

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🛠️ Troubleshooting

### Backend Bağlantı Hatası
- Backend'in 127.0.0.1:8000'de çalıştığından emin olun
- Frontend .env.local'de `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` kullanın

### Redis Bağlantı Hatası
- Redis'in çalıştığından emin olun: `docker ps`
- Redis loglarını kontrol edin: `docker logs <redis-container>`

### Celery Worker Sorunları
- Worker loglarını kontrol edin: `logs/celery_*.log`
- Redis connection string'i doğrulayın
- Worker'ları restart edin

### Docker Sorunları
- Detaylı bilgi için: [DEPLOYMENT.md](DEPLOYMENT.md)

## 📚 Dökümanlar

- [Deployment Guide](DEPLOYMENT.md) - Production deployment detayları
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Flower Dashboard](http://localhost:5555) - Celery monitoring

## 🎯 Roadmap

- [ ] **Faz 5: Advanced Features**
  - [ ] Multi-table CTGAN support
  - [ ] Time-series data generation
  - [ ] Custom constraint definitions
  - [ ] Advanced privacy metrics

- [ ] **Faz 6: Enterprise Features**
  - [ ] User authentication & authorization
  - [ ] Multi-tenant support
  - [ ] Audit logging
  - [ ] API rate limiting
  - [ ] Advanced analytics dashboard

## 🤝 Katkıda Bulunma

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 Lisans

MIT

## 👨‍💻 Geliştirici

[EmrahFidan](https://github.com/EmrahFidan)

## 📞 İletişim

GitHub Issues: [MissingLink Issues](https://github.com/EmrahFidan/MissingLink/issues)
