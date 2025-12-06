from django.contrib.auth.forms import AuthenticationForm
from django import forms

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={
            'class': 'input input-bordered grow',
            'placeholder': 'your.email@school.com',
            'autocomplete': 'email'
        })
        self.fields['password'].widget = forms.PasswordInput(attrs={
            'class': 'input input-bordered grow',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
