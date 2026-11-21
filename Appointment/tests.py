import datetime

from django.test import TestCase
from django.urls import reverse

from .models import Appointment


class PageTests(TestCase):
    def test_home_page_renders_dashboard(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertTemplateUsed(response, "base.html")

    def test_login_page_renders_form(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/login.html")
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_signup_page_renders_form(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/signup.html")
        for field in ("username", "email", "password1", "password2"):
            self.assertContains(response, f'name="{field}"')


class AppointmentModelTests(TestCase):
    def test_string_representation(self):
        appointment = Appointment.objects.create(
            service=Appointment.Service.DENTAL,
            date=datetime.date(2026, 3, 4),
            time=datetime.time(9, 30),
        )
        self.assertEqual(str(appointment), "Dental check-up on 04 Mar 2026 at 09:30")

    def test_default_status_is_pending(self):
        appointment = Appointment.objects.create(
            service=Appointment.Service.GENERAL,
            date=datetime.date(2026, 3, 4),
            time=datetime.time(10, 0),
        )
        self.assertEqual(appointment.status, Appointment.Status.PENDING)

    def test_ordering_is_by_date_then_time(self):
        later = Appointment.objects.create(
            service=Appointment.Service.GENERAL,
            date=datetime.date(2026, 5, 1),
            time=datetime.time(8, 0),
        )
        earlier = Appointment.objects.create(
            service=Appointment.Service.EYE,
            date=datetime.date(2026, 4, 1),
            time=datetime.time(16, 0),
        )
        same_day_later = Appointment.objects.create(
            service=Appointment.Service.PHYSIO,
            date=datetime.date(2026, 4, 1),
            time=datetime.time(17, 0),
        )
        self.assertEqual(
            list(Appointment.objects.all()), [earlier, same_day_later, later]
        )


class DashboardTests(TestCase):
    def test_dashboard_counts_and_rows(self):
        Appointment.objects.create(
            service=Appointment.Service.GENERAL,
            date=datetime.date(2026, 6, 1),
            time=datetime.time(9, 0),
            status=Appointment.Status.CONFIRMED,
        )
        Appointment.objects.create(
            service=Appointment.Service.EYE,
            date=datetime.date(2026, 6, 2),
            time=datetime.time(11, 0),
        )
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["total_count"], 2)
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["confirmed_count"], 1)
        self.assertContains(response, "Eye examination")

    def test_dashboard_shows_empty_state(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "No appointments yet")
