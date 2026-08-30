from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Create a password",
            }
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm your password",
            }
        )
    )

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "department",
            "role",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={"placeholder": "First name"}
            ),

            "last_name": forms.TextInput(
                attrs={"placeholder": "Last name"}
            ),

            "email": forms.EmailInput(
                attrs={"placeholder": "you@example.com"}
            ),

            "department": forms.TextInput(
                attrs={"placeholder": "e.g. Computer Science"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error(
                "confirm_password",
                "Passwords do not match."
            )

        return cleaned_data