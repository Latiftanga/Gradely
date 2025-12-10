from django import forms
from .models import SchoolSettings


class SchoolSettingsForm(forms.ModelForm):
    """Form for editing school settings"""

    class Meta:
        model = SchoolSettings
        fields = [
            'logo', 'favicon', 'motto',
            'address', 'city', 'region', 'postal_code', 'country',
            'email', 'phone', 'alternate_phone', 'website',
            'principal_name', 'founded_year', 'school_type',
            'primary_color', 'secondary_color',
        ]
        widgets = {
            'logo': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered file-input-sm w-full',
                'accept': 'image/*'
            }),
            'favicon': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered file-input-sm w-full',
                'accept': 'image/*'
            }),
            'motto': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Excellence in Education'
            }),
            'address': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered textarea-sm w-full',
                'rows': 2,
                'placeholder': 'Street address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Accra'
            }),
            'region': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Greater Accra'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., GA-123-4567'
            }),
            'country': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'school@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': '+233 XX XXX XXXX'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': '+233 XX XXX XXXX'
            }),
            'website': forms.URLInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'https://www.school.edu.gh'
            }),
            'principal_name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Mr. John Mensah'
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., 1990',
                'min': 1800,
                'max': 2100
            }),
            'school_type': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'primary_color': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'color'
            }),
        }
