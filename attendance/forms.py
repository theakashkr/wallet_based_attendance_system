"""
Forms for the attendance app.
Includes user registration and wallet recharge forms.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    """Extended registration form with email field."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-input",
            "placeholder": "Email address",
            "autocomplete": "email",
        }),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent styling to all fields
        self.fields["username"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Username",
            "autocomplete": "username",
        })
        self.fields["password1"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Password",
            "autocomplete": "new-password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Confirm password",
            "autocomplete": "new-password",
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class RechargeForm(forms.Form):
    """Simple form to recharge wallet credits."""

    amount = forms.DecimalField(
        min_value=1,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "form-input",
            "placeholder": "Enter amount (e.g. 50.00)",
            "step": "0.01",
            "min": "1",
        }),
    )
