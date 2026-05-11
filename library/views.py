from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date
import json
from .models import Library, Zone, Seat, CheckIn, DutyStaff, Feedback


def home(request):
    total = Seat.objects.filter(is_active=True).count()
    occupied = CheckIn.objects.filter(checked_out_at__isnull=True).count()
    broken = Seat.objects.filter(is_broken=True).count()
    empty = total - occupied - broken

    # Bugünün görevli çalışanı
    today_staff = DutyStaff.objects.filter(duty_date=date.today()).first()

    # Kütüphane bilgisi
    library = Library.objects.first()

    context = {
        "total": total,
        "occupied": occupied,
        "empty": empty,
        "broken": broken,
        "today_staff": today_staff,
        "library": library,
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
            return redirect("library:home")
    else:
        form = AuthenticationForm()
    return render(request, "library/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Çıkış yapıldı.")
    return redirect("library:login")


# ═══════════════════════════════════════
#  ŞİKAYET / ÖNERİ
# ═══════════════════════════════════════

def feedback_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        school_email = request.POST.get("school_email", "").strip()
        feedback_type = request.POST.get("feedback_type", "complaint")
        message = request.POST.get("message", "").strip()

        if not all([first_name, last_name, school_email, message]):
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            return redirect("library:home")

        Feedback.objects.create(
            first_name=first_name,
            last_name=last_name,
            school_email=school_email,
            feedback_type=feedback_type,
            message=message,
        )
        messages.success(request, "Geri bildiriminiz iletildi. Teşekkürler! 🙏")
        return redirect("library:home")

    return redirect("library:home")


# ═══════════════════════════════════════
#  CANLI HARİTA
# ═══════════════════════════════════════

@login_required
def seat_map(request):
    seats = Seat.objects.select_related("zone").filter(is_active=True)

    seat_list = []
    for seat in seats:
        active = seat.checkins.filter(checked_out_at__isnull=True).first()
        seat_list.append({
            "id": seat.id,
            "code": seat.code,
            "zone": seat.zone.name,
            "zone_type": seat.zone.zone_type,
            "is_occupied": active is not None,
            "is_broken": seat.is_broken,
            "user": active.user.username if active else None,
        })

    user_checkin = CheckIn.objects.filter(
        user=request.user, checked_out_at__isnull=True
    ).select_related("seat").first()

    # Bugünün görevlisi
    today_staff = DutyStaff.objects.filter(duty_date=date.today()).first()

    context = {
        "seats_json": json.dumps(seat_list),
        "user_checkin": user_checkin,
        "today_staff": today_staff,
    }
    return render(request, "library/seat_map.html", context)


# ═══════════════════════════════════════
#  CHECK-IN / CHECK-OUT
# ═══════════════════════════════════════

@login_required
def seat_checkin(request, uuid):
    seat = get_object_or_404(Seat, qr_uuid=uuid, is_active=True)

    if seat.is_broken:
        messages.error(request, f"{seat.code} koltuğu arızalı, kullanılamaz.")
        return redirect("library:seat_map")

    existing = CheckIn.objects.filter(user=request.user, checked_out_at__isnull=True).first()
    if existing:
        messages.warning(request, f"Zaten {existing.seat.code} koltuğundasın.")
        return redirect("library:seat_map")

    if seat.is_occupied:
        messages.error(request, f"{seat.code} koltuğu dolu.")
        return redirect("library:seat_map")

    if request.method == "POST":
        CheckIn.objects.create(user=request.user, seat=seat)
        messages.success(request, f"{seat.code} koltuğuna check-in yaptın! ✅")
        return redirect("library:seat_map")

    return render(request, "library/checkin_confirm.html", {"seat": seat})


@login_required
def checkout(request):
    active = CheckIn.objects.filter(user=request.user, checked_out_at__isnull=True).first()
    if not active:
        messages.info(request, "Aktif check-in'in yok.")
        return redirect("library:seat_map")
    if request.method == "POST":
        active.checked_out_at = timezone.now()
        active.save()
        messages.success(request, f"{active.seat.code} koltuğundan check-out yaptın.")
        return redirect("library:seat_map")
    return redirect("library:seat_map")


# ═══════════════════════════════════════
#  AJAX API
# ═══════════════════════════════════════

@login_required
def api_seats_status(request):
    seats = Seat.objects.select_related("zone").filter(is_active=True)
    data = []
    for seat in seats:
        active = seat.checkins.filter(checked_out_at__isnull=True).first()
        status = "broken" if seat.is_broken else ("occupied" if active else "empty")
        data.append({
            "id": seat.id,
            "code": seat.code,
            "zone": seat.zone.name,
            "zone_type": seat.zone.zone_type,
            "status": status,
            "user": active.user.username if active else None,
        })
    total = len(data)
    occupied = sum(1 for s in data if s["status"] == "occupied")
    broken = sum(1 for s in data if s["status"] == "broken")
    return JsonResponse({
        "seats": data,
        "total": total,
        "occupied": occupied,
        "broken": broken,
        "empty": total - occupied - broken,
    })


@login_required
def api_checkin(request, seat_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST gerekli"}, status=405)
    seat = get_object_or_404(Seat, id=seat_id, is_active=True)
    if seat.is_broken:
        return JsonResponse({"error": "Koltuk arızalı."}, status=400)
    existing = CheckIn.objects.filter(user=request.user, checked_out_at__isnull=True).first()
    if existing:
        return JsonResponse({"error": f"Zaten {existing.seat.code} koltuğundasın."}, status=400)
    if seat.is_occupied:
        return JsonResponse({"error": "Koltuk dolu."}, status=400)
    CheckIn.objects.create(user=request.user, seat=seat)
    return JsonResponse({"success": True, "seat": seat.code, "status": "occupied"})


@login_required
def api_checkout(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST gerekli"}, status=405)
    active = CheckIn.objects.filter(user=request.user, checked_out_at__isnull=True).first()
    if not active:
        return JsonResponse({"error": "Aktif check-in yok."}, status=400)
    active.checked_out_at = timezone.now()
    active.save()
    return JsonResponse({"success": True, "seat": active.seat.code, "status": "empty"})
