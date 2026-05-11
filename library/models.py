from django.db import models
import uuid
from django.contrib.auth.models import User


class Library(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kütüphane"
        verbose_name_plural = "Kütüphaneler"


class Zone(models.Model):
    ZONE_TYPES = [
        ("silent", "Sessiz Bölge"),
        ("group", "Grup Çalışma"),
        ("computer", "Bilgisayarlı"),
        ("general", "Genel"),
    ]
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES, default="general")
    floor = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.library.name} - {self.name}"

    class Meta:
        verbose_name = "Bölge"
        verbose_name_plural = "Bölgeler"


class Seat(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="seats")
    code = models.CharField(max_length=20)
    qr_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    is_broken = models.BooleanField(default=False, verbose_name="Arızalı")

    def __str__(self):
        return f"{self.zone} - Koltuk {self.code}"

    @property
    def is_occupied(self):
        return self.checkins.filter(checked_out_at__isnull=True).exists()

    class Meta:
        verbose_name = "Koltuk"
        verbose_name_plural = "Koltuklar"


class CheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="checkins")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name="checkins")
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "İçeride" if self.checked_out_at is None else "Çıktı"
        return f"{self.user.username} - {self.seat} ({status})"

    class Meta:
        ordering = ["-checked_in_at"]
        verbose_name = "Check-in"
        verbose_name_plural = "Check-in Kayıtları"


class DutyStaff(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Ad")
    last_name = models.CharField(max_length=100, verbose_name="Soyad")
    email = models.EmailField(verbose_name="E-posta")
    duty_date = models.DateField(verbose_name="Görev Tarihi")
    start_time = models.TimeField(verbose_name="Başlangıç Saati")
    end_time = models.TimeField(verbose_name="Bitiş Saati")
    note = models.TextField(blank=True, verbose_name="Not")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.duty_date})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["-duty_date"]
        verbose_name = "Görevli Çalışan"
        verbose_name_plural = "Görevli Çalışanlar"


class Feedback(models.Model):
    FEEDBACK_TYPES = [
        ("complaint", "Şikayet"),
        ("suggestion", "Öneri"),
        ("other", "Diğer"),
    ]
    first_name = models.CharField(max_length=100, verbose_name="Ad")
    last_name = models.CharField(max_length=100, verbose_name="Soyad")
    school_email = models.EmailField(verbose_name="Okul E-postası")
    feedback_type = models.CharField(
        max_length=20, choices=FEEDBACK_TYPES,
        default="complaint", verbose_name="Tür"
    )
    message = models.TextField(verbose_name="Mesaj")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name="Okundu")

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.get_feedback_type_display()} ({self.created_at.strftime('%d.%m.%Y')})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Geri Bildirim"
        verbose_name_plural = "Geri Bildirimler"
