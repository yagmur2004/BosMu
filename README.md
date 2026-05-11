# 📚 BosMu — Kütüphane Koltuk Takip Sistemi

🌐 **Canlı Demo:** https://bosmu.pythonanywhere.com

> *"Boş mu?" sorusunun dijital cevabı.*

BosMu, üniversite kütüphanelerindeki koltuk doluluk durumunu **gerçek zamanlı** olarak gösteren, QR kod ile **check-in/check-out** yapılabilen bir web uygulamasıdır.

---

## ✨ Özellikler

- 🗺️ **Canlı Koltuk Haritası** — 144 koltuğun anlık durumu (10 saniyede bir güncellenir)
- ✅ **Check-in / Check-out** — Haritadan tıklayarak veya QR kod okutarak
- 🔐 **Kullanıcı Sistemi** — Kayıt, giriş, çıkış
- 🛡️ **Rol Sistemi** — Herkes / Görevli (is_staff) / Admin (is_superuser)
- 🖥️ **Bilgisayarlı Alan** — Orta bölgedeki 18 bilgisayarlı koltuk ayrı renkte
- ⚠️ **Arıza Bildirimi** — Görevli panelinden bilgisayar arızası işaretlenir
- 💬 **Şikayet & Öneri** — İsim, soyisim, okul e-postası ile form
- 📊 **Admin Paneli** — Koltuk durumları, check-in geçmişi, süre takibi
- 👤 **Görevli Paneli** — Günlük görevli bilgisi, arıza yönetimi

---

## 🛠️ Teknolojiler

| Alan | Teknoloji |
|------|-----------|
| Backend | Django 5.2 |
| Veritabanı | SQLite |
| Frontend | HTML, CSS, JavaScript (AJAX) |
| API | Django REST Framework |
| Kimlik Doğrulama | Django Auth |
| Deploy | PythonAnywhere |

---

## 🚀 Kurulum

```bash
git clone https://github.com/yagmur2004/BosMu.git
cd BosMu
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py populate_seats
python manage.py createsuperuser
python manage.py runserver
```

Tarayıcıda aç: **http://127.0.0.1:8000/**

---

## 🏗️ Teknik Mimari & Tasarım Kararları

### Model Yapısı
```
Library (1) ──► Zone (N) ──► Seat (N) ──► CheckIn (N)
                                │
                          DutyStaff (bağımsız)
                          Feedback  (bağımsız)
```

| Model | Açıklama | Önemli Alanlar |
|-------|----------|----------------|
| `Library` | Kütüphane bilgisi | opening_time, closing_time |
| `Zone` | Bölge (Sol/Orta/Sağ) | zone_type |
| `Seat` | Koltuk | qr_uuid, is_active, is_broken |
| `CheckIn` | Oturum kaydı | checked_in_at, checked_out_at |
| `DutyStaff` | Günlük görevli | duty_date, start_time, end_time |
| `Feedback` | Şikayet/Öneri | school_email, is_read |

### Tasarım Kararları
- **`qr_uuid`** — Her koltuk için UUID4 ile benzersiz QR kimliği. `editable=False` ile değiştirilemez.
- **`is_occupied` property** — Ayrı alan tutmak yerine CheckIn tablosuna bakılır. Veri tutarsızlığı önlenir.
- **`select_related`** — Tüm koltuk sorgularında zone ilişkisi tek sorguda çekilir. N+1 sorgu problemi önlenir.
- **AJAX polling** — WebSocket yerine 10 saniyelik interval. Free tier kısıtları ve basitlik gözetildi.
- **`is_staff` flag** — Ayrı rol modeli yerine Django'nun yerleşik alanı kullanıldı.
- **`json.dumps()`** — Template'e Python listesi değil JSON string gönderilir. JS ile güvenli veri aktarımı.

---

## 🐛 Debugging & Bilinen Sorunlar

### Çözülen Sorunlar

| Sorun | Çözüm |
|-------|-------|
| `{{ seats\|safe }}` JS'de parse edilemiyordu | `json.dumps()` ile Python→JSON dönüşümü |
| Git merge conflict (template dosyaları) | `git rebase --abort` + force push |
| PythonAnywhere Python 3.13 uyumsuzluğu | venv Python 3.10 ile yeniden oluşturuldu |
| `list_editable` admin hatası | `is_read` alanı `list_display`'e eklendi |

### Bilinen Kısıtlamalar
- Harita 1380px genişliğinde tasarlanmıştır, mobilde yatay scroll gerektirir.
- SQLite production için önerilmez; büyük ölçekte PostgreSQL önerilir.

---

## 🧪 Testler

```bash
python manage.py test library
```

11 test — HomePageTest, AuthTest, SeatTest, FeedbackTest kapsamları mevcut.

---

## 📁 Proje Yapısı

```
BosMu/
├── config/
│   ├── settings.py
│   └── urls.py
├── library/
│   ├── management/commands/
│   │   └── populate_seats.py
│   ├── templates/library/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── seat_map.html
│   │   ├── staff_panel.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── checkin_confirm.html
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── manage.py
└── requirements.txt
```

---

## 🌐 URL'ler

| URL | Açıklama |
|-----|----------|
| `/` | Ana sayfa |
| `/map/` | Canlı koltuk haritası |
| `/login/` | Giriş |
| `/signup/` | Kayıt |
| `/staff/` | Görevli paneli |
| `/api/seats/` | Koltuk durumu (JSON) |
| `/api/checkin/<id>/` | AJAX check-in |
| `/api/checkout/` | AJAX check-out |
| `/admin/` | Admin paneli |

---

## 👥 Ekip

| İsim | GitHub |
|------|--------|
| Yağmur | [@yagmur2004](https://github.com/yagmur2004) |
| Freed | Collaborator |

---

## 📋 Sprint Geçmişi

| Sprint | İçerik | Durum |
|--------|--------|-------|
| Sprint 0 | Kurulum, GitHub, Django | ✅ |
| Sprint 1 | Modeller, Admin | ✅ |
| Sprint 2 | Authentication, Templates | ✅ |
| Sprint 3 | Harita, Check-in/out, AJAX | ✅ |
| Sprint 4 | Görevli, Şikayet, Arıza, Admin | ✅ |
| Sprint 5 | Rol sistemi, Staff paneli, Deploy | ✅ |

---

*Geliştirme: Mayıs 2026*