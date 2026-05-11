from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
import json
from .models import Library, Zone, Seat, CheckIn


def home(request):
    total = Seat.objects.filter(is_active=True).count()
    occupied = CheckIn.objects.filter(checked_out_at__isnull=True).count()
    empty = total - occupied
    context = {"total": total, "occupied": occupied, "empty": empty}
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
            "user": active.user.username if active else None,
        })

    user_checkin = CheckIn.objects.filter(
        user=request.user, checked_out_at__isnull=True
    ).select_related("seat").first()

    context = {
        "seats_json": json.dumps(seat_list),
        "user_checkin": user_checkin,
    }
    return render(request, "library/seat_map.html", context)


@login_required
def seat_checkin(request, uuid):
    seat = get_object_or_404(Seat, qr_uuid=uuid, is_active=True)
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


@login_required
def api_seats_status(request):
    seats = Seat.objects.select_related("zone").filter(is_active=True)
    data = []
    for seat in seats:
        active = seat.checkins.filter(checked_out_at__isnull=True).first()
        data.append({
            "id": seat.id,
            "code": seat.code,
            "zone": seat.zone.name,
            "zone_type": seat.zone.zone_type,
            "status": "occupied" if active else "empty",
            "user": active.user.username if active else None,
        })
    total = len(data)
    occupied = sum(1 for s in data if s["status"] == "occupied")
    return JsonResponse({"seats": data, "total": total, "occupied": occupied, "empty": total - occupied})


@login_required
def api_checkin(request, seat_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST gerekli"}, status=405)
    seat = get_object_or_404(Seat, id=seat_id, is_active=True)
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
