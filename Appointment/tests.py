import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import AppointmentForm
from .models import Appointment

PASSWORD = "Str0ngPass!2026"


def make_appointment(user=None, **overrides):
    data = {
        "user": user,
        "title": "Dental follow-up",
        "service": Appointment.Service.GENERAL,
        "date": datetime.date(2026, 6, 1),
        "time": datetime.time(9, 0),
    }
    data.update(overrides)
    return Appointment.objects.create(**data)


def future_date(days=3):
    return timezone.localdate() + datetime.timedelta(days=days)


def booking_payload(**overrides):
    data = {
        "title": "Weekly physiotherapy",
        "service": Appointment.Service.PHYSIO,
        "date": future_date().isoformat(),
        "time": "10:30",
        "description": "Bring the referral letter.",
    }
    data.update(overrides)
    return data


class PageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", PASSWORD)

    def test_home_page_renders_dashboard(self):
        self.client.force_login(self.user)
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
        appointment = make_appointment(
            title="Dental check-up",
            service=Appointment.Service.DENTAL,
            date=datetime.date(2026, 3, 4),
            time=datetime.time(9, 30),
        )
        self.assertEqual(str(appointment), "Dental check-up on 04 Mar 2026 at 09:30")

    def test_default_status_is_pending(self):
        appointment = make_appointment(date=datetime.date(2026, 3, 4), time=datetime.time(10, 0))
        self.assertEqual(appointment.status, Appointment.Status.PENDING)

    def test_ordering_is_by_date_then_time(self):
        later = make_appointment(date=datetime.date(2026, 5, 1), time=datetime.time(8, 0))
        earlier = make_appointment(
            service=Appointment.Service.EYE,
            date=datetime.date(2026, 4, 1),
            time=datetime.time(16, 0),
        )
        same_day_later = make_appointment(
            service=Appointment.Service.PHYSIO,
            date=datetime.date(2026, 4, 1),
            time=datetime.time(17, 0),
        )
        self.assertEqual(list(Appointment.objects.all()), [earlier, same_day_later, later])


class AppointmentFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", PASSWORD)
        self.other = User.objects.create_user("bilal", "bilal@example.com", PASSWORD)

    def test_valid_booking_saves_pending_appointment(self):
        form = AppointmentForm(booking_payload(), user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

        appointment = form.save(commit=False)
        appointment.user = self.user
        appointment.save()

        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(appointment.status, Appointment.Status.PENDING)

    def test_title_and_description_are_trimmed(self):
        form = AppointmentForm(
            booking_payload(title="  Annual review  ", description="  Bring ID.  "),
            user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["title"], "Annual review")
        self.assertEqual(form.cleaned_data["description"], "Bring ID.")

    def test_short_title_is_rejected(self):
        form = AppointmentForm(booking_payload(title="ab"), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_blank_title_is_rejected(self):
        form = AppointmentForm(booking_payload(title=""), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_past_date_is_rejected(self):
        form = AppointmentForm(
            booking_payload(date=future_date(-1).isoformat()), user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Choose today or a future date.", form.errors["date"])

    def test_time_in_the_past_today_is_rejected(self):
        form = AppointmentForm(
            booking_payload(date=timezone.localdate().isoformat(), time="00:00"),
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Choose a time later than now.", form.errors["time"])

    def test_duplicate_slot_for_same_user_is_rejected(self):
        make_appointment(
            user=self.user,
            title="Existing booking",
            date=future_date(),
            time=datetime.time(10, 30),
        )
        form = AppointmentForm(booking_payload(), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "You already have an appointment at this date and time.", form.errors["time"]
        )

    def test_same_slot_is_allowed_for_another_user(self):
        make_appointment(
            user=self.other,
            title="Taken by someone else",
            date=future_date(),
            time=datetime.time(10, 30),
        )
        form = AppointmentForm(booking_payload(), user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_editing_does_not_clash_with_itself(self):
        appointment = make_appointment(
            user=self.user, date=future_date(), time=datetime.time(10, 30)
        )
        form = AppointmentForm(
            booking_payload(title="Renamed review"), instance=appointment, user=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", PASSWORD)
        self.client.force_login(self.user)

    def test_dashboard_counts_and_rows(self):
        make_appointment(
            user=self.user,
            status=Appointment.Status.CONFIRMED,
            date=datetime.date(2026, 6, 1),
        )
        make_appointment(
            user=self.user,
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


class BookingViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", PASSWORD)
        self.other = User.objects.create_user("bilal", "bilal@example.com", PASSWORD)
        self.client.force_login(self.user)

    def test_create_page_renders_booking_form(self):
        response = self.client.get(reverse("appointment_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/appointment_form.html")
        for field in ("title", "service", "date", "time", "description"):
            self.assertContains(response, f'name="{field}"')

    def test_create_saves_appointment_for_signed_in_user(self):
        response = self.client.post(reverse("appointment_create"), booking_payload())
        self.assertRedirects(response, reverse("home"))

        appointment = Appointment.objects.get()
        self.assertEqual(appointment.user, self.user)
        self.assertEqual(appointment.title, "Weekly physiotherapy")
        self.assertEqual(appointment.status, Appointment.Status.PENDING)

    def test_invalid_booking_shows_errors_and_saves_nothing(self):
        response = self.client.post(reverse("appointment_create"), booking_payload(title=""))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        self.assertEqual(Appointment.objects.count(), 0)

    def test_create_rejects_a_past_date(self):
        response = self.client.post(
            reverse("appointment_create"),
            booking_payload(date=future_date(-2).isoformat()),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose today or a future date.")
        self.assertEqual(Appointment.objects.count(), 0)

    def test_update_changes_appointment(self):
        appointment = make_appointment(
            user=self.user, date=future_date(), time=datetime.time(9, 0)
        )
        response = self.client.post(
            reverse("appointment_update", args=[appointment.pk]),
            booking_payload(title="Rescheduled review", time="11:00"),
        )
        self.assertRedirects(response, reverse("home"))

        appointment.refresh_from_db()
        self.assertEqual(appointment.title, "Rescheduled review")
        self.assertEqual(appointment.time, datetime.time(11, 0))

    def test_update_page_shows_existing_values(self):
        appointment = make_appointment(
            user=self.user, title="Eye check", date=future_date()
        )
        response = self.client.get(reverse("appointment_update", args=[appointment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Eye check")

    def test_other_users_appointment_cannot_be_edited(self):
        appointment = make_appointment(
            user=self.other, title="Not yours", date=future_date()
        )
        url = reverse("appointment_update", args=[appointment.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, booking_payload()).status_code, 404)

    def test_delete_page_asks_for_confirmation(self):
        appointment = make_appointment(
            user=self.user, title="Old booking", date=future_date()
        )
        response = self.client.get(reverse("appointment_delete", args=[appointment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Old booking")
        self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())

    def test_delete_removes_appointment(self):
        appointment = make_appointment(user=self.user, date=future_date())
        response = self.client.post(
            reverse("appointment_delete", args=[appointment.pk])
        )
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Appointment.objects.filter(pk=appointment.pk).exists())

    def test_other_users_appointment_cannot_be_deleted(self):
        appointment = make_appointment(user=self.other, date=future_date())
        response = self.client.post(
            reverse("appointment_delete", args=[appointment.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Appointment.objects.filter(pk=appointment.pk).exists())

    def test_booking_views_require_login(self):
        self.client.logout()
        appointment = make_appointment(user=self.user, date=future_date())
        for name, args in (
            ("appointment_create", []),
            ("appointment_update", [appointment.pk]),
            ("appointment_delete", [appointment.pk]),
        ):
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("login"), response.url)

    def test_dashboard_lists_booking_actions(self):
        appointment = make_appointment(
            user=self.user, title="Dental follow-up", date=future_date()
        )
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Dental follow-up")
        self.assertContains(response, "Book appointment")
        self.assertContains(
            response, reverse("appointment_update", args=[appointment.pk])
        )
        self.assertContains(
            response, reverse("appointment_delete", args=[appointment.pk])
        )


class SignUpTests(TestCase):
    def data(self, **overrides):
        data = {
            "username": "amina",
            "first_name": "amina",
            "last_name": "rahim",
            "email": "Amina@Example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_signup_creates_user_with_hashed_password(self):
        response = self.client.post(reverse("signup"), self.data())
        self.assertRedirects(response, reverse("login"))

        user = User.objects.get(username="amina")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
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
        User.objects.create_user("Amina", "other@example.com", PASSWORD)
        response = self.client.post(reverse("signup"), self.data(username="AMINA"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "That username is already taken.")
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user("someone", "amina@example.com", PASSWORD)
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
        user = User.objects.create_user("amina", "amina@example.com", PASSWORD)
        self.client.force_login(user)
        response = self.client.get(reverse("signup"))
        self.assertRedirects(response, reverse("home"))


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", PASSWORD)

    def test_login_creates_session(self):
        response = self.client.post(
            reverse("login"), {"username": "amina", "password": PASSWORD}
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
            reverse("login"), {"username": "nobody", "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_returns_to_safe_next_url(self):
        response = self.client.post(
            reverse("login"),
            {"username": "amina", "password": PASSWORD, "next": reverse("signup")},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("signup"))

    def test_login_ignores_offsite_next_url(self):
        response = self.client.post(
            reverse("login"),
            {"username": "amina", "password": PASSWORD, "next": "https://evil.example/"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_authenticated_user_is_redirected_away_from_login(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("home"))


class LogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", PASSWORD)
        self.client.force_login(self.user)

    def test_logout_requires_post(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_clears_authentication(self):
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_nav_shows_logout_when_authenticated(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Log out")
        self.assertContains(response, "Signed in as")
        self.assertNotContains(response, "Sign up")


class SessionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("amina", "amina@example.com", PASSWORD)
        self.other = User.objects.create_user("bilal", "bilal@example.com", PASSWORD)

    def login(self, username="amina"):
        return self.client.post(
            reverse("login"), {"username": username, "password": PASSWORD}
        )

    def test_anonymous_dashboard_redirects_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('home')}"
        )

    def test_dashboard_shows_only_own_appointments(self):
        make_appointment(user=self.user, service=Appointment.Service.DENTAL)
        make_appointment(
            user=self.other,
            service=Appointment.Service.EYE,
            date=datetime.date(2026, 7, 1),
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Dental check-up")
        self.assertNotContains(response, "Eye examination")
        self.assertEqual(response.context["total_count"], 1)

    def test_session_persists_across_requests(self):
        self.login()
        self.assertIn("_auth_user_id", self.client.session)

        first = self.client.get(reverse("home"))
        second = self.client.get(reverse("home"))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.context["user"], self.user)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_sets_persistent_httponly_cookie(self):
        response = self.login()
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertEqual(int(cookie["max-age"]), settings.SESSION_COOKIE_AGE)
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertFalse(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)

    def test_session_expiry_is_refreshed_on_requests(self):
        self.login()
        self.assertGreater(
            self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE - 60
        )
        self.assertLessEqual(
            self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE
        )
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_login_returns_to_protected_dashboard(self):
        response = self.client.get(reverse("home"))
        login_url = response.url
        response = self.client.post(
            login_url,
            {"username": "amina", "password": PASSWORD, "next": reverse("home")},
        )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_logout_ends_the_session(self):
        self.login()
        old_key = self.client.session.session_key

        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotEqual(self.client.session.session_key, old_key)

        dashboard = self.client.get(reverse("home"))
        self.assertEqual(dashboard.status_code, 302)
        self.assertIn(reverse("login"), dashboard.url)
