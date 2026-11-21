import datetime

from django.contrib.auth.models import User
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


class SignUpTests(TestCase):
    password = "Str0ngPass!2026"

    def data(self, **overrides):
        data = {
            "username": "amina",
            "first_name": "amina",
            "last_name": "rahim",
            "email": "Amina@Example.com",
            "password1": self.password,
            "password2": self.password,
        }
        data.update(overrides)
        return data

    def test_signup_creates_user_with_hashed_password(self):
        response = self.client.post(reverse("signup"), self.data())
        self.assertRedirects(response, reverse("login"))

        user = User.objects.get(username="amina")
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        self.assertTrue(user.password.startswith("pbkdf2_"))

    def test_signup_normalises_email_and_names(self):
        self.client.post(
            reverse("signup"),
            self.data(first_name="  amina ", last_name=" rahim ", email="Amina@Example.COM"),
        )
        user = User.objects.get(username="amina")
        self.assertEqual(user.email, "amina@example.com")
        self.assertEqual(user.first_name, "Amina")
        self.assertEqual(user.last_name, "Rahim")

    def test_signup_trims_username(self):
        self.client.post(reverse("signup"), self.data(username="  amina  "))
        self.assertTrue(User.objects.filter(username="amina").exists())

    def test_duplicate_username_is_rejected_case_insensitively(self):
        User.objects.create_user("Amina", "other@example.com", self.password)
        response = self.client.post(reverse("signup"), self.data(username="AMINA"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "That username is already taken.")
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user("someone", "amina@example.com", self.password)
        response = self.client.post(reverse("signup"), self.data(email="AMINA@example.com"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")
        self.assertEqual(User.objects.count(), 1)

    def test_email_is_required(self):
        response = self.client.post(reverse("signup"), self.data(email=""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_weak_numeric_password_is_rejected(self):
        response = self.client.post(
            reverse("signup"), self.data(password1="12345678", password2="12345678")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password is too common.")
        self.assertEqual(User.objects.count(), 0)

    def test_short_password_is_rejected(self):
        response = self.client.post(
            reverse("signup"), self.data(password1="aB3$x", password2="aB3$x")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "at least 8 characters")
        self.assertEqual(User.objects.count(), 0)

    def test_password_mismatch_is_rejected(self):
        response = self.client.post(
            reverse("signup"), self.data(password2="DifferentPass!2026")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "two password fields didn’t match")
        self.assertEqual(User.objects.count(), 0)

    def test_signup_page_redirects_authenticated_users(self):
        user = User.objects.create_user("amina", "amina@example.com", self.password)
        self.client.force_login(user)
        response = self.client.get(reverse("signup"))
        self.assertRedirects(response, reverse("home"))


class LoginTests(TestCase):
    password = "Str0ngPass!2026"

    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", self.password)

    def test_login_creates_session(self):
        response = self.client.post(
            reverse("login"), {"username": "amina", "password": self.password}
        )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(self.client.session["_auth_user_id"], str(self.user.pk))

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            reverse("login"), {"username": "amina", "password": "NotThePassword1!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_user_is_rejected(self):
        response = self.client.post(
            reverse("login"), {"username": "nobody", "password": self.password}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_returns_to_safe_next_url(self):
        response = self.client.post(
            reverse("login") + "?next=" + reverse("signup"),
            {"username": "amina", "password": self.password, "next": reverse("signup")},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("signup"))

    def test_login_ignores_offsite_next_url(self):
        response = self.client.post(
            reverse("login"),
            {"username": "amina", "password": self.password, "next": "https://evil.example/"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_authenticated_user_is_redirected_away_from_login(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("home"))


class LogoutTests(TestCase):
    password = "Str0ngPass!2026"

    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", self.password)
        self.client.force_login(self.user)

    def test_logout_requires_post(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_clears_authentication(self):
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_nav_shows_logout_when_authenticated(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Log out")
        self.assertNotContains(response, "Sign up")
