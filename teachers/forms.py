import uuid
import secrets
import string
from django import forms
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .models import Teacher
from accounts.models import User


def generate_random_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class TeacherForm(forms.ModelForm):
    """Base form for creating/updating a Teacher."""

    class Meta:
        model = Teacher
        fields = [
            # Personal Information
            'first_name',
            'last_name',
            'middle_name',
            'date_of_birth',
            'gender',
            # Professional Information
            'staff_id',
            'ghana_card_number',
            'ssnit_number',
            # Employment Details
            'employment_status',
            'date_employed',
            'qualification',
            'specialization',
            # Contact Information
            'phone_number',
            'emergency_contact_name',
            'emergency_contact_phone',
            'residential_address',
            # Status
            'is_active',
            'termination_date',
            'termination_reason',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_employed': forms.DateInput(attrs={'type': 'date'}),
            'termination_date': forms.DateInput(attrs={'type': 'date'}),
            'residential_address': forms.Textarea(attrs={'rows': 2}),
            'termination_reason': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply DaisyUI styling classes based on widget type
        for field_name, field in self.fields.items():
            widget = field.widget
            widget_class = widget.__class__.__name__

            if widget_class == 'CheckboxInput':
                widget.attrs['class'] = 'checkbox checkbox-primary checkbox-sm'
            elif widget_class == 'Select':
                widget.attrs['class'] = 'select select-bordered select-sm w-full'
            elif widget_class == 'Textarea':
                widget.attrs['class'] = 'textarea textarea-bordered textarea-sm w-full'
            else:
                widget.attrs['class'] = 'input input-bordered input-sm w-full'


class TeacherCreateForm(TeacherForm):
    """Form for creating a new Teacher with optional user account."""

    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        label="Create login account",
        help_text="If checked, login credentials will be sent to the teacher's email."
    )
    email = forms.EmailField(
        required=False,
        label="Teacher's Email",
        help_text="Login credentials will be sent to this email address."
    )

    class Meta(TeacherForm.Meta):
        fields = ['create_user_account', 'email'] + TeacherForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['create_user_account'].widget.attrs['class'] = 'checkbox checkbox-primary checkbox-sm'

    def clean(self):
        cleaned_data = super().clean()
        create_account = cleaned_data.get('create_user_account')
        email = cleaned_data.get('email')

        if create_account:
            if not email:
                self.add_error('email', 'Email is required when creating a user account.')
            elif User.objects.filter(email=email).exists():
                self.add_error('email', 'A user with this email already exists.')

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        create_account = self.cleaned_data.get('create_user_account')
        email = self.cleaned_data.get('email')
        staff_id = self.cleaned_data.get('staff_id')
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')

        if create_account and email:
            # Generate random password
            password = generate_random_password()

            # Create user with teacher role
            user = User.objects.create_user(email=email, password=password, role=User.TEACHER)
            user.force_password_change = True
            user.save()

            # Send credentials email
            self._send_credentials_email(email, password, first_name, last_name)
        else:
            # Create placeholder user without login access
            placeholder_email = f"teacher.{staff_id.lower()}.{uuid.uuid4().hex[:6]}@teacher.placeholder"
            user = User.objects.create_user(email=placeholder_email, password=None, role=User.TEACHER)
            user.set_unusable_password()
            user.save()

        teacher = super().save(commit=False)
        teacher.user = user

        if commit:
            teacher.save()

        return teacher

    def _send_credentials_email(self, email, password, first_name, last_name):
        """Send login credentials to the teacher's email."""
        subject = 'Your Teacher Account Has Been Created'
        message = f"""
Hello {first_name} {last_name},

Your teacher account has been created. Here are your login credentials:

Email: {email}
Password: {password}

Please log in and change your password immediately for security purposes.

Best regards,
School Administration
"""
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )


class TeacherUpdateForm(TeacherForm):
    """Form for updating an existing Teacher's details."""

    email = forms.EmailField(
        required=True,
        label="Teacher's Email",
        help_text="This will be used for the teacher's login account."
    )

    class Meta(TeacherForm.Meta):
        fields = ['email'] + TeacherForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    @transaction.atomic
    def save(self, commit=True):
        teacher = super().save(commit=False)
        user = teacher.user
        new_email = self.cleaned_data.get('email')

        if user.email != new_email:
            if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                self.add_error('email', 'A user with this email already exists.')
                raise forms.ValidationError("User already exists.")
            user.email = new_email
            user.save()

        if commit:
            teacher.save()
        return teacher


class TeacherBulkImportForm(forms.Form):
    """Form for bulk importing teachers from CSV/XLSX files."""
    file = forms.FileField(
        label="Import File",
        help_text="Upload a CSV or XLSX file with teacher data."
    )
    send_credentials = forms.BooleanField(
        required=False,
        initial=True,
        label="Send login credentials",
        help_text="If checked, login credentials will be emailed to teachers."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs['class'] = 'file-input file-input-bordered file-input-sm w-full'
        self.fields['file'].widget.attrs['accept'] = '.csv,.xlsx,.xls'
        self.fields['send_credentials'].widget.attrs['class'] = 'checkbox checkbox-primary checkbox-sm'

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            filename = file.name.lower()
            if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
                raise forms.ValidationError("Only CSV and XLSX files are supported.")

            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB.")

        return file
