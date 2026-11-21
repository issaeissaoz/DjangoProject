from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import LoginForm, SignUpForm
from .models import Appointment


def home_view(request):
    appointments = Appointment.objects.select_related("user")
    context = {
        "appointments": appointments,
        "total_count": appointments.count(),
        "pending_count": appointments.filter(status=Appointment.Status.PENDING).count(),
        "confirmed_count": appointments.filter(status=Appointment.Status.CONFIRMED).count(),
        "completed_count": appointments.filter(status=Appointment.Status.COMPLETED).count(),
    }
    return render(request, "core/home.html", context)


def login_view(request):
    # Phase 2 replaces this stub with real authentication.
    if request.method == "POST":
        messages.info(request, "Authentication lands in phase 2 - nothing was submitted yet.")
        return redirect("home")
    return render(request, "core/login.html", {"form": LoginForm(request=request)})


def signup_view(request):
    # Phase 2 replaces this stub with validation and user creation.
    if request.method == "POST":
        messages.info(request, "Account creation lands in phase 2 - nothing was submitted yet.")
        return redirect("home")
    return render(request, "core/signup.html", {"form": SignUpForm()})
