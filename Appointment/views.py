from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AppointmentForm, LoginForm, SignUpForm
from .models import Appointment


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


@login_required
def home_view(request):
    appointments = Appointment.objects.select_related("user").filter(user=request.user)
    context = {
        "appointments": appointments,
        "total_count": appointments.count(),
        "pending_count": appointments.filter(status=Appointment.Status.PENDING).count(),
        "confirmed_count": appointments.filter(status=Appointment.Status.CONFIRMED).count(),
        "completed_count": appointments.filter(status=Appointment.Status.COMPLETED).count(),
    }
    return render(request, "core/home.html", context)


@login_required
def appointment_create(request):
    form = AppointmentForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        appointment = form.save(commit=False)
        appointment.user = request.user
        appointment.save()
        messages.success(request, f"Appointment booked: {appointment.title}.")
        return redirect("home")

    return render(request, "core/appointment_form.html", {"form": form, "is_edit": False})


@login_required
def appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)
    form = AppointmentForm(
        request.POST or None, instance=appointment, user=request.user
    )
    if request.method == "POST" and form.is_valid():
        appointment = form.save()
        messages.success(request, f"Appointment updated: {appointment.title}.")
        return redirect("home")

    return render(
        request,
        "core/appointment_form.html",
        {"form": form, "is_edit": True, "appointment": appointment},
    )


@login_required
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)
    if request.method == "POST":
        title = appointment.title
        appointment.delete()
        messages.success(request, f"Appointment deleted: {title}.")
        return redirect("home")

    return render(
        request, "core/appointment_confirm_delete.html", {"appointment": appointment}
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, f"Welcome back, {request.user.username}.")
        return redirect(_safe_next_url(request) or "home")

    return render(
        request,
        "core/login.html",
        {"form": form, "next": request.GET.get("next", "")},
    )


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Account created for {user.username}. You can log in now.")
        return redirect("login")

    return render(request, "core/signup.html", {"form": form})


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect("home")
