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
        verbose_name_plural = "Libraries"


class Zone(models.Model):
    ZONE_TYPES = [
        ("silent", "Sessiz Bölge"),
        ("group", "Grup Çalışma"),
        ("computer", "Bilgisayarlı"),
        ("general", "Genel"),
    ]

    library = models.ForeignKey(
        Library, on_delete=models.CASCADE, related_name="zones"
    )
    name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES, default="general")
    floor = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.library.name} - {self.name}"


class Seat(models.Model):
    zone = models.ForeignKey(
        Zone, on_delete=models.CASCADE, related_name="seats"
    )
    code = models.CharField(max_length=20)
    qr_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.zone} - Koltuk {self.code}"

    @property
    def is_occupied(self):
        return self.checkins.filter(checked_out_at__isnull=True).exists()


class CheckIn(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="checkins"
    )
    seat = models.ForeignKey(
        Seat, on_delete=models.CASCADE, related_name="checkins"
    )
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "İçeride" if self.checked_out_at is None else "Çıktı"
        return f"{self.user.username} - {self.seat} ({status})"

    class Meta:
        ordering = ["-checked_in_at"]
