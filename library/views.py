from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, ExpressionWrapper, F, DurationField
from django.db.models.functions import ExtractWeekDay, ExtractHour, ExtractDay
from datetime import date
from dateutil.relativedelta import relativedelta
import json
import qrcode
import io
import calendar
import time
from .models import Library, Zone, Seat, CheckIn, DutyStaff, Feedback, LibraryEntryQR


def is_staff_check(user):
    return user.is_authenticated and user.is_staff


def get_session_key(request):
    """Session key'i döndürür, yoksa oluşturur."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def home(request):
    """Ana sayfa."""
    total = Seat.objects.filter(is_active=True).count()
    occupied = CheckIn.objects.filter(checked_out_at__isnull=True).count()
    broken = Seat.objects.filter(is_broken=True).count()
    empty = total - occupied - broken
    today_staff = DutyStaff.objects.filter(duty_date=date.today()).first()
    library = Library.objects.first()
    has_entry = request.session.get("has_entry", False)
    context = {
        "total": total, "occupied": occupied, "empty": empty,
        "broken": broken, "today_staff": today_staff,
        "library": library, "has_entry": has_entry,
    }
    return render(request, "library/home.html", context)


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Hesabınız oluşturuldu!")
            return redirect("library:home")
    else:
        form = UserCreationForm()
    return render(request, "library/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Giriş yapıldı!")
            if user.is_staff:
                return redirect("library:staff_panel")
            return redirect("library:home")
    else:
        form = AuthenticationForm()
    return render(request, "library/login.html", {"form": form})


def logout_view(request):
    logout(request)
    request.session.pop("has_entry", None)
    messages.info(request, "Çıkış yapıldı.")
    return redirect("library:home")


def feedback_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        school_email = request.POST.get("school_email", "").strip()
        feedback_type = request.POST.get("feedback_type", "complaint")
        msg = request.POST.get("message", "").strip()
        if not all([first_name, last_name, school_email, msg]):
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            return redirect("library:home")
        Feedback.objects.create(
            first_name=first_name, last_name=last_name,
            school_email=school_email, feedback_type=feedback_type, message=msg,
        )
        messages.success(request, "Geri bildiriminiz iletildi. Teşekkürler! 🙏")
        return redirect("library:home")
    return redirect("library:home")


# ═══════════════════════════════════════
#  ANA GİRİŞ QR
# ═══════════════════════════════════════

def entry_qr_scan(request, token):
    """Ana QR okutulunca çağrılır. Token geçerliyse session'a giriş hakkı verir."""
    entry_qr = LibraryEntryQR.objects.first()
    if not entry_qr:
        messages.error(request, "Sistem hatası. Görevliye başvurun.")
        return redirect("library:home")

    if str(entry_qr.current_token) == str(token):
        request.session["has_entry"] = True
        entry_qr.refresh()
        messages.success(request, "Kütüphaneye hoş geldiniz! Koltuk seçebilirsiniz. 🎉")
        return redirect("library:seat_map")
    else:
        messages.error(request, "Bu QR kodu geçersiz veya süresi dolmuş.")
        return redirect("library:home")


def entry_qr_image(request):
    """Staff için ana QR kodunu PNG olarak gösterir."""
    if not request.user.is_staff:
        return redirect("library:home")
    entry_qr = LibraryEntryQR.objects.first()
    if not entry_qr:
        entry_qr = LibraryEntryQR.objects.create()
    url = f"https://bosmu.pythonanywhere.com/entry/{entry_qr.current_token}/"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    response = HttpResponse(buf, content_type='image/png')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


# ═══════════════════════════════════════
#  HARİTA
# ═══════════════════════════════════════

def seat_map(request):
    """Canlı koltuk haritası."""
    seats = Seat.objects.select_related("zone").filter(is_active=True)
    seat_list = []
    for seat in seats:
        active = seat.checkins.filter(checked_out_at__isnull=True).first()
        seat_list.append({
            "id": seat.id, "code": seat.code,
            "zone": seat.zone.name, "zone_type": seat.zone.zone_type,
            "is_occupied": active is not None,
            "is_broken": seat.is_broken,
        })

    session_key = get_session_key(request)
    user_checkin = CheckIn.objects.filter(
        session_key=session_key, checked_out_at__isnull=True
    ).select_related("seat").first()

    today_staff = DutyStaff.objects.filter(duty_date=date.today()).first()
    has_entry = request.session.get("has_entry", False)

    context = {
        "seats_json": json.dumps(seat_list),
        "user_checkin": user_checkin,
        "today_staff": today_staff,
        "has_entry": json.dumps(has_entry),
    }
    return render(request, "library/seat_map.html", context)


# ═══════════════════════════════════════
#  CHECK-IN / CHECK-OUT (session bazlı)
# ═══════════════════════════════════════

def seat_checkin(request, uuid):
    """QR kod ile koltuğa check-in. Giriş tokeni gerekli."""
    seat = get_object_or_404(Seat, qr_uuid=uuid, is_active=True)

    if seat.is_broken:
        messages.error(request, f"{seat.code} koltuğu arızalı.")
        return redirect("library:seat_map")

    if not request.session.get("has_entry", False):
        messages.warning(request, "Önce kütüphane girişindeki QR kodu okutmalısın.")
        return redirect("library:seat_map")

    session_key = get_session_key(request)
    existing = CheckIn.objects.filter(session_key=session_key, checked_out_at__isnull=True).first()
    if existing:
        messages.warning(request, f"Zaten {existing.seat.code} koltuğundasın.")
        return redirect("library:seat_map")

    if seat.is_occupied:
        messages.error(request, f"{seat.code} koltuğu dolu.")
        return redirect("library:seat_map")

    if request.method == "POST":
        CheckIn.objects.create(seat=seat, session_key=session_key)
        messages.success(request, f"{seat.code} koltuğuna check-in yaptın! ✅")
        return redirect("library:seat_map")

    return render(request, "library/checkin_confirm.html", {"seat": seat})


def checkout(request):
    """Check-out yapar ve giriş hakkını sıfırlar."""
    session_key = get_session_key(request)
    active = CheckIn.objects.filter(session_key=session_key, checked_out_at__isnull=True).first()
    if not active:
        messages.info(request, "Aktif check-in'in yok.")
        return redirect("library:seat_map")
    if request.method == "POST":
        active.checked_out_at = timezone.now()
        active.save()
        request.session.pop("has_entry", None)
        messages.success(request, f"{active.seat.code} koltuğundan ayrıldın. Tekrar gelmek için kapıdaki QR'ı okut.")
        return redirect("library:seat_map")
    return redirect("library:seat_map")


# ═══════════════════════════════════════
#  STAFF PANELİ
# ═══════════════════════════════════════

@user_passes_test(is_staff_check, login_url="/login/")
def staff_panel(request):
    today_staff = DutyStaff.objects.filter(duty_date=date.today()).first()
    library = Library.objects.first()
    active_checkins = CheckIn.objects.filter(
        checked_out_at__isnull=True
    ).select_related("seat").order_by("-checked_in_at")
    entry_qr = LibraryEntryQR.objects.first()
    if not entry_qr:
        entry_qr = LibraryEntryQR.objects.create()
    context = {
        "today_staff": today_staff,
        "library": library,
        "active_checkins": active_checkins,
        "entry_qr": entry_qr,
        "now_ts": int(time.time()),
    }
    return render(request, "library/staff_panel.html", context)


@user_passes_test(is_staff_check, login_url="/login/")
def toggle_broken(request, seat_id):
    if request.method == "POST":
        seat = get_object_or_404(Seat, id=seat_id, zone__zone_type="computer")
        seat.is_broken = not seat.is_broken
        seat.save()
        status = "arızalı" if seat.is_broken else "normal"
        messages.success(request, f"{seat.code} koltuğu {status} olarak işaretlendi.")
    return redirect("library:staff_panel")


# ═══════════════════════════════════════
#  AJAX API
# ═══════════════════════════════════════

def api_seats_status(request):
    """Tüm koltukların anlık durumu."""
    seats = Seat.objects.select_related("zone").filter(is_active=True)
    data = []
    for seat in seats:
        active = seat.checkins.filter(checked_out_at__isnull=True).first()
        status = "broken" if seat.is_broken else ("occupied" if active else "empty")
        data.append({
            "id": seat.id, "code": seat.code,
            "zone": seat.zone.name, "zone_type": seat.zone.zone_type,
            "status": status,
        })
    total = len(data)
    occupied = sum(1 for s in data if s["status"] == "occupied")
    broken = sum(1 for s in data if s["status"] == "broken")
    return JsonResponse({"seats": data, "total": total, "occupied": occupied, "broken": broken, "empty": total - occupied - broken})


def api_checkin(request, seat_id):
    """AJAX check-in."""
    if request.method != "POST":
        return JsonResponse({"error": "POST gerekli"}, status=405)
    if not request.session.get("has_entry", False):
        return JsonResponse({"error": "Önce kapıdaki QR'ı okut.", "redirect": "/scan/"}, status=403)
    seat = get_object_or_404(Seat, id=seat_id, is_active=True)
    if seat.is_broken:
        return JsonResponse({"error": "Koltuk arızalı."}, status=400)
    session_key = get_session_key(request)
    existing = CheckIn.objects.filter(session_key=session_key, checked_out_at__isnull=True).first()
    if existing:
        return JsonResponse({"error": f"Zaten {existing.seat.code} koltuğundasın."}, status=400)
    if seat.is_occupied:
        return JsonResponse({"error": "Koltuk dolu."}, status=400)
    CheckIn.objects.create(seat=seat, session_key=session_key)
    return JsonResponse({"success": True, "seat": seat.code})


def api_checkout(request):
    """AJAX check-out."""
    if request.method != "POST":
        return JsonResponse({"error": "POST gerekli"}, status=405)
    session_key = get_session_key(request)
    active = CheckIn.objects.filter(session_key=session_key, checked_out_at__isnull=True).first()
    if not active:
        return JsonResponse({"error": "Aktif check-in yok."}, status=400)
    active.checked_out_at = timezone.now()
    active.save()
    request.session.pop("has_entry", None)
    return JsonResponse({"success": True, "seat": active.seat.code})


def seat_qr(request, seat_id):
    """Koltuk QR kodu."""
    seat = get_object_or_404(Seat, id=seat_id)
    url = f"https://bosmu.pythonanywhere.com/seat/{seat.qr_uuid}/"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf, content_type='image/png')


def qr_scanner(request):
    """Kamera ile QR okuma sayfası."""
    return render(request, "library/qr_scanner.html")


# ═══════════════════════════════════════
#  ANALİTİK
# ═══════════════════════════════════════

def analytics_view(request):
    """Analitik dashboard sayfası. Sadece staff erişebilir."""
    if not request.user.is_staff:
        return redirect("library:home")

    today = date.today()
    available_months = []
    for i in range(6):
        d = today - relativedelta(months=i)
        available_months.append({
            "value": d.strftime("%Y-%m"),
            "label": d.strftime("%B %Y"),
        })

    selected_month = request.GET.get("month", today.strftime("%Y-%m"))

    context = {
        "available_months": available_months,
        "selected_month": selected_month,
    }
    return render(request, "library/analytics.html", context)


def analytics_data(request):
    """Gerçek CheckIn verisini JSON olarak döndürür. Sadece staff erişebilir."""
    if not request.user.is_staff:
        return JsonResponse({"error": "Yetkisiz"}, status=403)

    month_str = request.GET.get("month", date.today().strftime("%Y-%m"))
    try:
        year, month = int(month_str.split("-")[0]), int(month_str.split("-")[1])
    except Exception:
        year, month = date.today().year, date.today().month

    qs = CheckIn.objects.filter(
        checked_in_at__year=year,
        checked_in_at__month=month,
    )

    total = qs.count()

    days_in_month = calendar.monthrange(year, month)[1]
    daily_avg = round(total / days_in_month) if days_in_month else 0

    by_weekday_qs = (
        qs.annotate(wd=ExtractWeekDay("checked_in_at"))
        .values("wd").annotate(count=Count("id")).order_by("wd")
    )
    weekday_map = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 1: 6}
    by_weekday = [0] * 7
    for row in by_weekday_qs:
        idx = weekday_map.get(row["wd"], 0)
        by_weekday[idx] = row["count"]

    day_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    peak_day = day_names[by_weekday.index(max(by_weekday))] if total else "—"

    by_hour_qs = (
        qs.annotate(hr=ExtractHour("checked_in_at"))
        .values("hr").annotate(count=Count("id")).order_by("hr")
    )
    hour_map = {h: 0 for h in range(8, 23)}
    for row in by_hour_qs:
        if row["hr"] in hour_map:
            hour_map[row["hr"]] = row["count"]
    by_hour = list(hour_map.values())

    by_day_qs = (
        qs.annotate(d=ExtractDay("checked_in_at"))
        .values("d").annotate(count=Count("id")).order_by("d")
    )
    day_map = {d: 0 for d in range(1, days_in_month + 1)}
    for row in by_day_qs:
        day_map[row["d"]] = row["count"]
    daily_trend = list(day_map.values())

    completed = qs.filter(checked_out_at__isnull=False).annotate(
        duration=ExpressionWrapper(
            F("checked_out_at") - F("checked_in_at"),
            output_field=DurationField()
        )
    )
    avg_dur = 0
    if completed.exists():
        total_seconds = sum(c.duration.total_seconds() for c in completed)
        avg_dur = round(total_seconds / completed.count() / 60)

    today = date.today()
    compare_labels = []
    compare_data = []
    month_names = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                   "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    for i in range(5, -1, -1):
        d = today - relativedelta(months=i)
        count = CheckIn.objects.filter(
            checked_in_at__year=d.year,
            checked_in_at__month=d.month
        ).count()
        compare_labels.append(month_names[d.month - 1])
        compare_data.append(count)

    return JsonResponse({
        "total_checkins": total,
        "daily_avg": daily_avg,
        "peak_day": peak_day,
        "avg_duration_min": avg_dur,
        "by_weekday": by_weekday,
        "by_hour": by_hour,
        "daily_trend": daily_trend,
        "monthly_compare": {"labels": compare_labels, "data": compare_data},
    })