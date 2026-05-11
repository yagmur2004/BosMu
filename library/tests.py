from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Library, Zone, Seat, CheckIn, Feedback


class HomePageTest(TestCase):
    """Ana sayfa testleri."""

    def test_home_page_loads(self):
        """Ana sayfa login gerektirmeden açılmalı."""
        response = self.client.get(reverse("library:home"))
        self.assertEqual(response.status_code, 200)

    def test_map_page_loads(self):
        """Harita sayfası login gerektirmeden açılmalı."""
        response = self.client.get(reverse("library:seat_map"))
        self.assertEqual(response.status_code, 200)


class AuthTest(TestCase):
    """Kimlik doğrulama testleri."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_login(self):
        """Geçerli kullanıcı giriş yapabilmeli."""
        response = self.client.post(reverse("library:login"), {
            "username": "testuser",
            "password": "testpass123",
        })
        self.assertRedirects(response, reverse("library:home"))

    def test_wrong_password(self):
        """Yanlış şifreyle giriş yapılamamalı."""
        response = self.client.post(reverse("library:login"), {
            "username": "testuser",
            "password": "wrongpass",
        })
        self.assertEqual(response.status_code, 200)

    def test_staff_panel_requires_staff(self):
        """Staff paneli normal kullanıcıya kapalı olmalı."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("library:staff_panel"))
        self.assertNotEqual(response.status_code, 200)


class SeatTest(TestCase):
    """Koltuk ve check-in testleri."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.library = Library.objects.create(
            name="Test Kütüphane",
            opening_time="08:00",
            closing_time="20:00"
        )
        self.zone = Zone.objects.create(
            library=self.library,
            name="Sol Bölge",
            zone_type="general"
        )
        self.seat = Seat.objects.create(zone=self.zone, code="L-001")

    def test_seat_initially_empty(self):
        """Yeni koltuk boş olmalı."""
        self.assertFalse(self.seat.is_occupied)

    def test_seat_occupied_after_checkin(self):
        """Check-in sonrası koltuk dolu görünmeli."""
        CheckIn.objects.create(user=self.user, seat=self.seat)
        self.assertTrue(self.seat.is_occupied)

    def test_broken_seat_not_occupied(self):
        """Arızalı koltuk dolu sayılmamalı."""
        self.seat.is_broken = True
        self.seat.save()
        self.assertFalse(self.seat.is_occupied)

    def test_api_seats_status(self):
        """API endpoint JSON dönmeli."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("library:api_seats_status"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("seats", data)
        self.assertIn("total", data)


class FeedbackTest(TestCase):
    """Geri bildirim testleri."""

    def test_feedback_submission(self):
        """Geçerli form verisiyle geri bildirim gönderilebilmeli."""
        response = self.client.post(reverse("library:feedback"), {
            "first_name": "Ali",
            "last_name": "Yılmaz",
            "school_email": "ali@uni.edu.tr",
            "feedback_type": "complaint",
            "message": "Test mesajı",
        })
        self.assertEqual(Feedback.objects.count(), 1)

    def test_feedback_missing_fields(self):
        """Eksik alanlarla geri bildirim gönderilememeli."""
        self.client.post(reverse("library:feedback"), {
            "first_name": "Ali",
        })
        self.assertEqual(Feedback.objects.count(), 0)