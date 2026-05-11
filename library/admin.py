from django.contrib import admin
from django.utils.html import format_html
from .models import Library, Zone, Seat, CheckIn


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ("name", "opening_time", "closing_time", "address")


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "library", "zone_type", "floor", "seat_count")

    def seat_count(self, obj):
        return obj.seats.filter(is_active=True).count()
    seat_count.short_description = "Koltuk Sayısı"


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("code", "zone", "status_badge", "is_active", "qr_uuid")
    list_filter = ("zone", "is_active", "zone__zone_type")
    search_fields = ("code",)
    readonly_fields = ("qr_uuid",)
    ordering = ("zone", "code")

    def status_badge(self, obj):
        if obj.is_occupied:
            return format_html('<span style="color:white;background:#ef4444;padding:2px 8px;border-radius:4px;">Dolu</span>')
        return format_html('<span style="color:white;background:#22c55e;padding:2px 8px;border-radius:4px;">Boş</span>')
    status_badge.short_description = "Durum"


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ("user", "seat", "checked_in_at", "checked_out_at", "duration", "is_active_badge")
    list_filter = ("seat__zone", "checked_in_at")
    search_fields = ("user__username", "seat__code")
    ordering = ("-checked_in_at",)
    readonly_fields = ("checked_in_at",)

    def is_active_badge(self, obj):
        if obj.checked_out_at is None:
            return format_html('<span style="color:white;background:#ef4444;padding:2px 8px;border-radius:4px;">İçeride</span>')
        return format_html('<span style="color:white;background:#6b7280;padding:2px 8px;border-radius:4px;">Çıktı</span>')
    is_active_badge.short_description = "Durum"

    def duration(self, obj):
        if obj.checked_out_at:
            delta = obj.checked_out_at - obj.checked_in_at
            mins = int(delta.total_seconds() // 60)
            return f"{mins} dk"
        return "—"
    duration.short_description = "Süre"
