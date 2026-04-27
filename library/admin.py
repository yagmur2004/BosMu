from django.contrib import admin
from .models import Library, Zone, Seat, CheckIn


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ("name", "opening_time", "closing_time")


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "library", "zone_type", "floor")
    list_filter = ("zone_type", "library")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("code", "zone", "is_active", "is_occupied")
    list_filter = ("is_active", "zone")


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ("user", "seat", "checked_in_at", "checked_out_at")
    list_filter = ("checked_out_at",)