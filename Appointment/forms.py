from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Appointment


class LoginForm(AuthenticationForm):
    """Styled login form handling credential checks."""

    error_messages = {
        "invalid_login": "Invalid username or password. Please try again.",
        "inactive": "This account is inactive.",
    }

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "your username",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "input",
                "placeholder": "your password",
                "autocomplete": "current-password",
            }
        ),
    )


class SignUpForm(UserCreationForm):
    """Sign-up form with case-insensitive uniqueness checks."""

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "input", "placeholder": "you@example.com", "autocomplete": "email"}
        ),
    )
    first_name = forms.CharField(
        label="First name",
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "First name"}),
    )
    last_name = forms.CharField(
        label="Last name",
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Last name"}),
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {"username": "Username"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "input", "placeholder": "choose a username", "autocomplete": "username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "input", "placeholder": "choose a password", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "input", "placeholder": "repeat the password", "autocomplete": "new-password"}
        )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip().title()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip().title()


class AppointmentForm(forms.ModelForm):
    """Book or edit an appointment that belongs to the signed-in user."""

    title = forms.CharField(
        label="Title",
        min_length=3,
        max_length=120,
        error_messages={
            "min_length": "Give the appointment a title of at least 3 characters."
        },
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "e.g. Dental follow-up",
                "autocomplete": "off",
            }
        ),
    )
    description = forms.CharField(
        label="Description",
        required=False,
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "class": "input",
                "rows": 4,
                "placeholder": "Anything the clinic should know (optional)",
            }
        ),
    )

    class Meta:
        model = Appointment
        fields = ("title", "service", "date", "time", "description")
        widgets = {
            "service": forms.Select(attrs={"class": "input"}),
            "date": forms.DateInput(attrs={"class": "input", "type": "date"}),
            "time": forms.TimeInput(attrs={"class": "input", "type": "time"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_title(self):
        return " ".join(self.cleaned_data["title"].split())

    def clean_description(self):
        return self.cleaned_data["description"].strip()

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < timezone.localdate():
            raise ValidationError("Choose today or a future date.")
        return date

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")

        if date and time:
            if date == timezone.localdate() and time <= timezone.localtime().time():
                self.add_error("time", "Choose a time later than now.")
            elif self.user is not None:
                clash = Appointment.objects.filter(user=self.user, date=date, time=time)
                if self.instance.pk:
                    clash = clash.exclude(pk=self.instance.pk)
                if clash.exists():
                    self.add_error(
                        "time", "You already have an appointment at this date and time."
                    )

        return cleaned_data
