from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "input-box", "placeholder": "Enter your email"}),
        help_text="Required. Enter a valid email address."
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)  # Create user but don't save yet
        user.email = self.cleaned_data["email"]  # Assign email
        if commit:
            user.save()  # Now save user to database
        return user
