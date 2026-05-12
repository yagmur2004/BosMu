from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("map/", views.seat_map, name="seat_map"),
    path("seat/<uuid:uuid>/", views.seat_checkin, name="seat_checkin"),
    path("checkout/", views.checkout, name="checkout"),
    path("feedback/", views.feedback_view, name="feedback"),
    path("staff/", views.staff_panel, name="staff_panel"),
    path("staff/broken/<int:seat_id>/", views.toggle_broken, name="toggle_broken"),

    # Ana giriş QR
    path("entry/<uuid:token>/", views.entry_qr_scan, name="entry_qr_scan"),
    path("entry-qr/", views.entry_qr_image, name="entry_qr_image"),
    path("scan/", views.qr_scanner, name="qr_scanner"),
    # Koltuk QR
    path("qr/<int:seat_id>/", views.seat_qr, name="seat_qr"),

    # AJAX API
    path("api/seats/", views.api_seats_status, name="api_seats_status"),
    path("api/checkin/<int:seat_id>/", views.api_checkin, name="api_checkin"),
    path("api/checkout/", views.api_checkout, name="api_checkout"),
]