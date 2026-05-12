from django.contrib import admin
from django.utils.html import format_html
from .models import Library, Zone, Seat, CheckIn, DutyStaff, Feedback


admin.site.site_header = "📚 BosMu Yönetim Paneli"
admin.site.site_title = "BosMu Admin"
admin.site.index_title = "Hoş Geldiniz"


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ("name", "opening_time", "closing_time", "address")
    fieldsets = (
        ("Kütüphane Bilgileri", {"fields": ("name", "address")}),
        ("Çalışma Saatleri", {"fields": ("opening_time", "closing_time")}),
    )


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "library", "zone_type", "floor", "seat_count")
    list_filter = ("zone_type", "library")

    def seat_count(self, obj):
        return obj.seats.filter(is_active=True).count()
    seat_count.short_description = "Koltuk Sayısı"


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("code", "zone", "status_badge", "is_active")
    list_filter = ("zone", "is_active", "zone__zone_type")
    search_fields = ("code",)
    readonly_fields = ("qr_uuid",)
    ordering = ("zone", "code")

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ("Koltuk Bilgisi", {"fields": ("zone", "code", "is_active")}),
            ("QR Kodu", {"fields": ("qr_uuid",), "classes": ("collapse",)}),
        ]
        if obj and obj.zone.zone_type == "computer":
            fieldsets.insert(1, ("Arıza Durumu", {
                "fields": ("is_broken",),
                "description": "Sadece bilgisayarlı koltuklar için."
            }))
        return fieldsets

    def status_badge(self, obj):
        if obj.is_broken:
            return format_html('<span style="color:white;background:#6b7280;padding:2px 10px;border-radius:4px;">⚠️ Arızalı</span>')
        if obj.is_occupied:
            return format_html('<span style="color:white;background:#ef4444;padding:2px 10px;border-radius:4px;">Dolu</span>')
        return format_html('<span style="color:white;background:#22c55e;padding:2px 10px;border-radius:4px;">Boş</span>')
    status_badge.short_description = "Durum"


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ("session_key_short", "seat", "checked_in_at", "checked_out_at", "duration", "is_active_badge")
    list_filter = ("seat__zone", "checked_in_at")
    search_fields = ("seat__code",)
    ordering = ("-checked_in_at",)
    readonly_fields = ("checked_in_at",)

    def is_active_badge(self, obj):
        if obj.checked_out_at is None:
            return format_html('<span style="color:white;background:#ef4444;padding:2px 10px;border-radius:4px;">İçeride</span>')
        return format_html('<span style="color:white;background:#6b7280;padding:2px 10px;border-radius:4px;">Çıktı</span>')
    is_active_badge.short_description = "Durum"

    def duration(self, obj):
        if obj.checked_out_at:
            delta = obj.checked_out_at - obj.checked_in_at
            mins = int(delta.total_seconds() // 60)
            return f"{mins} dk"
        return "—"
    duration.short_description = "Süre"

    def session_key_short(self, obj):
        return obj.session_key[:8] + "..." if obj.session_key else "—"
    session_key_short.short_description = "Oturum"


@admin.register(DutyStaff)
class DutyStaffAdmin(admin.ModelAdmin):
    list_display = ("full_name_display", "email", "duty_date", "start_time", "end_time", "today_badge")
    list_filter = ("duty_date",)
    search_fields = ("first_name", "last_name", "email")
    ordering = ("-duty_date",)
    fieldsets = (
        ("Çalışan Bilgileri", {"fields": ("first_name", "last_name", "email")}),
        ("Görev Zamanı", {"fields": ("duty_date", "start_time", "end_time")}),
        ("Ek Bilgi", {"fields": ("note",), "classes": ("collapse",)}),
    )

    def full_name_display(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name_display.short_description = "Ad Soyad"

    def today_badge(self, obj):
        from datetime import date
        if obj.duty_date == date.today():
            return format_html('<span style="color:white;background:#6366f1;padding:2px 10px;border-radius:4px;">📍 Bugün</span>')
        return "—"
    today_badge.short_description = "Bugün?"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("full_name_display", "school_email", "feedback_type_badge", "created_at", "is_read", "is_read_badge")
    list_filter = ("feedback_type", "is_read", "created_at")
    search_fields = ("first_name", "last_name", "school_email", "message")
    ordering = ("-created_at",)
    readonly_fields = ("first_name", "last_name", "school_email", "feedback_type", "message", "created_at")
    list_editable = ("is_read",)

    # Add butonu kaldır
    def has_add_permission(self, request):
        return False

    fieldsets = (
        ("Gönderen", {"fields": ("first_name", "last_name", "school_email")}),
        ("İçerik", {"fields": ("feedback_type", "message", "created_at")}),
        ("Durum", {"fields": ("is_read",)}),
    )

    def full_name_display(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name_display.short_description = "Ad Soyad"

    def feedback_type_badge(self, obj):
        colors = {"complaint": "#ef4444", "suggestion": "#3b82f6", "other": "#6b7280"}
        color = colors.get(obj.feedback_type, "#6b7280")
        return format_html('<span style="color:white;background:{};padding:2px 10px;border-radius:4px;">{}</span>', color, obj.get_feedback_type_display())
    feedback_type_badge.short_description = "Tür"

    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color:#22c55e;">✓ Okundu</span>')
        return format_html('<span style="color:#ef4444;font-weight:bold;">● Yeni</span>')
    is_read_badge.short_description = "Durum"