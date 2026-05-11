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
    path("api/seats/", views.api_seats_status, name="api_seats_status"),
    path("api/checkin/<int:seat_id>/", views.api_checkin, name="api_checkin"),
    path("api/checkout/", views.api_checkout, name="api_checkout"),
]