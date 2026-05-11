# 📚 BosMu — Kütüphane Koltuk Takip Sistemi

> *"Boş mu?" sorusunun dijital cevabı.*

BosMu, üniversite kütüphanelerindeki koltuk doluluk durumunu **gerçek zamanlı** olarak gösteren, QR kod ile **check-in/check-out** yapılabilen bir web uygulamasıdır.

---

## 🖥️ Ekran Görüntüleri

| Ana Sayfa | Canlı Harita |
|-----------|-------------|
| Giriş yapıldığında doluluk özeti | 144 koltuk, anlık durum |

---

## ✨ Özellikler

- 🗺️ **Canlı Koltuk Haritası** — 144 koltuğun anlık durumu (10 saniyede bir güncellenir)
- ✅ **Check-in / Check-out** — Haritadan tıklayarak veya QR kod okutarak
- 🔐 **Kullanıcı Sistemi** — Kayıt, giriş, çıkış
- 🖥️ **Bilgisayarlı Alan** — Orta bölgedeki 18 bilgisayarlı koltuk ayrı renkte
- 📊 **Admin Paneli** — Koltuk durumları, check-in geçmişi, süre takibi
- 📱 **QR Kod Desteği** — Her koltuğun benzersiz UUID'si ile check-in

---

## 🛠️ Teknolojiler

| Alan | Teknoloji |
|------|-----------|
| Backend | Django 5.2 |
| Veritabanı | SQLite |
| Frontend | HTML, CSS, JavaScript (AJAX) |
| API | Django REST Framework |
| Kimlik Doğrulama | Django Auth |

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.10+
- Git

### Adımlar

```bash
# 1. Repoyu klonla
git clone https://github.com/yagmur2004/BosMu.git
cd BosMu

# 2. Virtual environment oluştur ve aktif et
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Veritabanını hazırla
python manage.py migrate

# 5. 144 koltuğu otomatik ekle
python manage.py populate_seats

# 6. Admin hesabı oluştur
python manage.py createsuperuser

# 7. Sunucuyu başlat
python manage.py runserver
```

Tarayıcıda aç: **http://127.0.0.1:8000/**

---

## 📁 Proje Yapısı

```
BosMu/
├── config/
│   ├── settings.py
│   └── urls.py
├── library/
│   ├── management/
│   │   └── commands/
│   │       └── populate_seats.py   # 144 koltuğu ekler
│   ├── templates/
│   │   └── library/
│   │       ├── base.html           # Ana şablon
│   │       ├── home.html           # Ana sayfa
│   │       ├── seat_map.html       # Canlı harita
│   │       ├── login.html          # Giriş
│   │       ├── signup.html         # Kayıt
│   │       └── checkin_confirm.html
│   ├── models.py                   # Library, Zone, Seat, CheckIn
│   ├── views.py                    # Tüm view'lar + AJAX API
│   ├── urls.py                     # URL yönlendirmeleri
│   └── admin.py                    # Admin paneli özelleştirmeleri
├── manage.py
└── requirements.txt
```

---

## 🗺️ Koltuk Düzeni

```
SOL BÖLGE (93)    ORTA (22)     SAĞ BÖLGE (29)
┌─────────────┐   ┌─────────┐   ┌──────────────┐
│ 12 | 10 | 12│   │ 🖥️🖥️🖥️ │   │  5 koltuk    │
│ sütun sütun │   │ 6 sıra  │   │  6 koltuk    │
│             │   │ bilgisa-│   ├──────────────┤
│  alt blok   │   │ yarlı   │   │  6 koltuk    │
│  6+6+6+1    │   └─────────┘   │  6 koltuk    │
└─────────────┘                 ├──────────────┤
                                │  6 koltuk    │
                                └──────────────┘
```

---

## 🌐 URL'ler

| URL | Açıklama |
|-----|----------|
| `/` | Ana sayfa |
| `/map/` | Canlı koltuk haritası |
| `/login/` | Giriş |
| `/signup/` | Kayıt |
| `/logout/` | Çıkış |
| `/seat/<uuid>/` | QR ile check-in |
| `/checkout/` | Check-out |
| `/api/seats/` | Anlık koltuk durumu (JSON) |
| `/api/checkin/<id>/` | AJAX check-in |
| `/api/checkout/` | AJAX check-out |
| `/admin/` | Admin paneli |

---

## 👥 Ekip

| İsim | GitHub |
|------|--------|
| Yağmur | [@yagmur2004](https://github.com/yagmur2004) |
| Freed | [@SamiSidar](https://github.com/SamiSidar) |

---

## 📋 Sprint Geçmişi

| Sprint | İçerik | Durum |
|--------|--------|-------|
| Sprint 0 | Kurulum, GitHub, Django | ✅ |
| Sprint 1 | Modeller, Admin | ✅ |
| Sprint 2 | Authentication, Templates | ✅ |
| Sprint 3 | Harita, Check-in/out, AJAX | ✅ |
| Sprint 4 | README, Dokümantasyon | ✅ |

---

*Geliştirme: Mayıs 2026*
