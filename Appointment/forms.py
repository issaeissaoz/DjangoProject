from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class LoginForm(AuthenticationForm):
    """Styled login form. Authentication logic is wired up in phase 2."""

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
    """Styled sign-up form. Validation is hardened in phase 2."""

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
