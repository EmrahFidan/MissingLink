# MissingLink Deployment Guide

## Faz 4: Asenkron İşleme ve Production Deployment

Bu doküman MissingLink projesinin production ortamına deploy edilmesi için gerekli adımları içerir.

## 📋 Gereksinimler

### Minimum Sistem Gereksinimleri
- **CPU**: 4 core (8 core önerilir)
- **RAM**: 8 GB (16 GB önerilir, CTGAN eğitimi için)
- **Disk**: 50 GB boş alan
- **OS**: Linux (Ubuntu 20.04+ önerilir) veya Windows 10/11

### Yazılım Gereksinimleri
- Docker 20.10+
- Docker Compose 2.0+
- Git
- (Opsiyonel) NVIDIA GPU + CUDA (hızlı model eğitimi için)

## 🚀 Deployment Adımları

### 1. Repository'yi Klonlayın

```bash
git clone https://github.com/EmrahFidan/MissingLink.git
cd MissingLink
```

### 2. Environment Ayarları

Backend production ayarlarını düzenleyin:

```bash
cd backend
cp .env.production .env
```

`.env` dosyasında aşağıdaki değerleri güncelleyin:
- `SECRET_KEY`: Güvenli bir secret key oluşturun
- `JWT_SECRET_KEY`: JWT için güvenli bir key oluşturun
- `ALLOWED_ORIGINS`: Frontend domain'inizi ekleyin

### 3. Docker ile Deployment

#### Tüm Servisleri Başlatın

```bash
# Projenin root dizininde
docker-compose up -d
```

Bu komut şu servisleri başlatır:
- **Redis**: Message broker (port 6379)
- **Backend API**: FastAPI sunucusu (port 8000)
- **Celery CTGAN Worker**: CTGAN işlemleri için (1 worker)
- **Celery Processing Worker**: Genel işlemler için (4 worker)
- **Flower**: Celery monitoring dashboard (port 5555)

#### Servisleri Kontrol Edin

```bash
# Tüm servislerin durumunu kontrol et
docker-compose ps

# Backend loglarını görüntüle
docker-compose logs -f backend

# Worker loglarını görüntüle
docker-compose logs -f celery-ctgan celery-processing
```

### 4. Servis Erişim Bilgileri

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Flower Dashboard**: http://localhost:5555
- **Frontend** (ayrı çalıştırılıyorsa): http://localhost:3000

### 5. Frontend Deployment (Opsiyonel)

Frontend'i Docker ile çalıştırmak için docker-compose.yml içindeki frontend servisini aktif edin veya ayrı bir sunucuda çalıştırın:

```bash
cd frontend
npm install
npm run build
npm start
```

## 🔧 Lokal Development

### Backend + Celery Lokal Çalıştırma

#### Windows:

```bash
# Terminal 1: Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload

# Terminal 3: Celery Workers
cd backend
scripts\start_workers.bat

# Terminal 4: Flower Monitoring
cd backend
scripts\start_flower.bat
```

#### Linux/Mac:

```bash
# Terminal 1: Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload

# Terminal 3: Celery Workers
cd backend
bash scripts/start_workers.sh

# Terminal 4: Flower Monitoring
cd backend
bash scripts/start_flower.sh
```

## 📊 Monitoring ve Logs

### Flower Dashboard

Flower monitoring dashboard'u kullanarak:
- Aktif task'ları görüntüleme
- Worker durumlarını kontrol etme
- Task geçmişini inceleme
- İstatistikleri görüntüleme

Erişim: http://localhost:5555

### Docker Logs

```bash
# Tüm servis logları
docker-compose logs -f

# Belirli bir servis
docker-compose logs -f backend
docker-compose logs -f celery-ctgan
docker-compose logs -f flower

# Son N satır
docker-compose logs --tail=100 backend
```

### Log Dosyaları

Backend container içindeki loglar:
- `/app/logs/app.log` - Application logs
- `/app/logs/celery_ctgan.log` - CTGAN worker logs
- `/app/logs/celery_processing.log` - Processing worker logs

## 🔒 Güvenlik

### Production Checklist

- [ ] `.env` dosyasındaki SECRET_KEY'leri değiştirin
- [ ] ALLOWED_ORIGINS'i sadece gerçek domain'lerinize ayarlayın
- [ ] Redis için authentication ekleyin
- [ ] HTTPS/SSL sertifikası ekleyin (Nginx/Caddy ile)
- [ ] Rate limiting uygulayın
- [ ] Firewall kurallarını ayarlayın
- [ ] Backup stratejisi oluşturun

### Önerilen Reverse Proxy Yapılandırması

Nginx örnek konfigürasyonu:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;  # Frontend
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;  # Backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /flower {
        proxy_pass http://localhost:5555;
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

## 🔄 Güncelleme ve Bakım

### Uygulama Güncellemesi

```bash
# Yeni kodu çek
git pull origin main

# Servisleri yeniden başlat
docker-compose down
docker-compose build
docker-compose up -d
```

### Veri Yedekleme

```bash
# Redis verilerini yedekle
docker exec missinglink-redis redis-cli SAVE
docker cp missinglink-redis:/data/dump.rdb ./backup/

# Upload ve model dosyalarını yedekle
docker cp missinglink-backend:/app/uploads ./backup/
docker cp missinglink-backend:/app/models ./backup/
```

### Performans Optimizasyonu

1. **Worker Sayısını Ayarlayın**: docker-compose.yml'de `--concurrency` parametresini değiştirin
2. **Redis Memory Limit**: Redis konfigürasyonunu optimize edin
3. **Uvicorn Workers**: Backend servisinde `--workers` sayısını artırın

## 🐛 Troubleshooting

### Redis Bağlantı Hatası

```bash
# Redis'in çalıştığından emin olun
docker-compose ps redis

# Redis loglarını kontrol edin
docker-compose logs redis
```

### Celery Worker Başlamıyor

```bash
# Worker loglarını kontrol edin
docker-compose logs celery-ctgan
docker-compose logs celery-processing

# Worker'ı yeniden başlatın
docker-compose restart celery-ctgan
```

### Model Eğitimi Yavaş

- GPU kullanımını kontrol edin (NVIDIA GPU varsa)
- Worker concurrency'yi azaltın (memory kullanımı)
- Batch size'ı küçültün
- Epoch sayısını azaltın

## 📞 Destek

Sorunlarla karşılaşırsanız:
1. GitHub Issues: https://github.com/EmrahFidan/MissingLink/issues
2. Documentation: Proje README.md dosyası
3. Logs: Detaylı hata loglarını kontrol edin

## 📝 Notlar

- İlk deployment yaklaşık 5-10 dakika sürebilir (Docker image build)
- CTGAN model eğitimi büyük veri setleri için uzun sürebilir
- Production ortamında GPU kullanımı şiddetle önerilir
- Flower dashboard'u production'da authentication ile korunmalı
