import uuid
import secrets
import string
from django import forms
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Student, Parent
from accounts.models import User


def generate_placeholder_email(student_id):
    """Generate a placeholder email for students without user account."""
    clean_id = student_id.lower().replace(' ', '_').replace('-', '_')
    return f"{clean_id}.{uuid.uuid4().hex[:6]}@student.placeholder"


def generate_random_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class StudentBulkImportForm(forms.Form):
    """Form for bulk importing students from CSV/XLSX files."""
    file = forms.FileField(
        label="Import File",
        help_text="Upload a CSV or XLSX file with student data."
    )
    create_user_accounts = forms.BooleanField(
        required=False,
        initial=True,
        label="Create login accounts",
        help_text="If checked, login accounts will be created for students with email addresses."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs['class'] = 'file-input file-input-bordered file-input-sm w-full'
        self.fields['file'].widget.attrs['accept'] = '.csv,.xlsx,.xls'
        self.fields['create_user_accounts'].widget.attrs['class'] = 'checkbox checkbox-primary checkbox-sm'

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


class StudentForm(forms.ModelForm):
    """
    A form for creating/updating a Student.
    It can be used for both creating a new student (and a new User)
    or updating an existing student's details.
    """
    class Meta:
        model = Student
        fields = [
            # Personal Information
            'first_name',
            'last_name',
            'middle_name',
            'date_of_birth',
            'gender',
            # Identification
            'student_id',
            'index_number',
            'admission_number',
            'ghana_card_number',
            # Academic Information
            'current_class',
            'admission_date',
            'previous_school',
            # Location
            'hometown',
            'region',
            'nationality',
            # Residential
            'residential_status',
            'house',
            'residential_address',
            # Health
            'medical_conditions',
            'allergies',
            'blood_group',
            # Status
            'is_active',
            'withdrawal_date',
            'withdrawal_reason',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'withdrawal_date': forms.DateInput(attrs={'type': 'date'}),
            'residential_address': forms.Textarea(attrs={'rows': 2}),
            'withdrawal_reason': forms.Textarea(attrs={'rows': 2}),
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
            elif widget_class == 'PasswordInput':
                widget.attrs['class'] = 'input input-bordered input-sm w-full'
            else:
                widget.attrs['class'] = 'input input-bordered input-sm w-full'


class StudentCreateForm(StudentForm):
    """
    A form specifically for creating a new Student, with optional user account creation.
    Inherits most fields from StudentForm, but adds email for user creation.
    Password is auto-generated and sent via email.
    """
    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        label="Create login account",
        help_text="If checked, a login account will be created and credentials sent via email."
    )
    email = forms.EmailField(
        required=False,
        label="Student's Email",
        help_text="Login credentials will be sent to this email address."
    )

    class Meta(StudentForm.Meta):
        fields = ['create_user_account', 'email'] + StudentForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style the checkbox
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
        """
        Override the save method to handle the creation of both a User and a Student.
        If create_user_account is True, generates a random password and sends it via email.
        If create_user_account is False, creates a placeholder user without login access.
        """
        create_account = self.cleaned_data.get('create_user_account')
        email = self.cleaned_data.get('email')
        student_id = self.cleaned_data.get('student_id')
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')

        if create_account:
            # Generate a random password
            password = generate_random_password()

            # Create the User instance with login access
            user = User.objects.create_studentuser(email=email, password=password)
            user.force_password_change = True
            user.save()

            # Send email with credentials
            self._send_credentials_email(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
        else:
            # Create placeholder user without login access
            placeholder_email = generate_placeholder_email(student_id)
            user = User.objects.create_studentuser(email=placeholder_email, password=None)
            user.set_unusable_password()
            user.save()

        # Create the Student instance, but don't save it to the DB yet
        student = super().save(commit=False)
        student.user = user  # Link the student profile to the new user

        if commit:
            student.save()

        return student

    def _send_credentials_email(self, email, password, first_name, last_name):
        """Send login credentials to the student's email."""
        subject = 'Your Student Account Has Been Created'
        message = f"""
Hello {first_name} {last_name},

Your student account has been created. Here are your login credentials:

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
            fail_silently=False,
        )


class StudentUpdateForm(StudentForm):
    """
    A form for updating an existing Student's details.
    Includes the 'is_active' field which might be hidden on creation.
    """
    email = forms.EmailField(
        required=True,
        label="Student's Email",
        help_text="This will be used for the student's login account."
    )

    class Meta(StudentForm.Meta):
        fields = ['email'] + StudentForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    @transaction.atomic
    def save(self, commit=True):
        student = super().save(commit=False)
        user = student.user
        new_email = self.cleaned_data.get('email')

        if user.email != new_email:
            if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                self.add_error('email', 'A user with this email already exists.')
                raise forms.ValidationError("User already exists.")
            user.email = new_email
            user.save()

        if commit:
            student.save()
        return student


class ParentForm(forms.ModelForm):
    """
    A form for creating/updating a Parent.
    """
    class Meta:
        model = Parent
        fields = [
            # Personal Information
            'title',
            'first_name',
            'middle_name',
            'last_name',
            'phone_number',
            'alternate_phone',
            # Relationship
            'relationship',
            'students',
            # Professional
            'occupation',
            'employer',
            'work_phone',
            'work_address',
            # Address
            'residential_address',
            'hometown',
            'region',
            # Preferences
            'is_primary_contact',
            'is_emergency_contact',
            'can_pickup_student',
            # Status
            'is_active',
        ]
        widgets = {
            'work_address': forms.Textarea(attrs={'rows': 2}),
            'residential_address': forms.Textarea(attrs={'rows': 2}),
            'students': forms.SelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply DaisyUI styling classes based on widget type
        for field_name, field in self.fields.items():
            widget = field.widget
            widget_class = widget.__class__.__name__

            if widget_class == 'CheckboxInput':
                widget.attrs['class'] = 'checkbox checkbox-primary checkbox-sm'
            elif widget_class in ['Select', 'SelectMultiple']:
                widget.attrs['class'] = 'select select-bordered select-sm w-full'
            elif widget_class == 'Textarea':
                widget.attrs['class'] = 'textarea textarea-bordered textarea-sm w-full'
            else:
                widget.attrs['class'] = 'input input-bordered input-sm w-full'


class ParentCreateForm(ParentForm):
    """
    A form specifically for creating a new Parent with User account.
    Password is auto-generated and sent via email.
    """
    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        label="Create login account",
        help_text="If checked, login credentials will be sent to the parent's email."
    )
    email = forms.EmailField(
        required=False,
        label="Parent's Email",
        help_text="Login credentials will be sent to this email address."
    )

    class Meta(ParentForm.Meta):
        # Remove 'students' from fields - will be set in the view
        fields = ['create_user_account', 'email'] + [
            f for f in ParentForm.Meta.fields if f != 'students'
        ]

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
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
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')

        if create_account and email:
            # Generate random password
            password = generate_random_password()

            # Create user with parent role
            user = User.objects.create_user(email=email, password=password, role='parent')
            user.force_password_change = True
            user.save()

            # Send credentials email
            self._send_credentials_email(email, password, first_name, last_name)
        else:
            # Create placeholder user
            placeholder_email = f"parent.{uuid.uuid4().hex[:8]}@parent.placeholder"
            user = User.objects.create_user(email=placeholder_email, password=None, role='parent')
            user.set_unusable_password()
            user.save()

        parent = super().save(commit=False)
        parent.user = user

        if commit:
            parent.save()
            # Link to student if provided
            if self.student:
                parent.students.add(self.student)

        return parent

    def _send_credentials_email(self, email, password, first_name, last_name):
        """Send login credentials to the parent's email."""
        subject = 'Your Parent Account Has Been Created'
        message = f"""
Hello {first_name} {last_name},

Your parent account has been created. Here are your login credentials:

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
            fail_silently=False,
        )


class LinkExistingParentForm(forms.Form):
    """
    Form for linking an existing parent to a student.
    """
    parent = forms.ModelChoiceField(
        queryset=Parent.objects.none(),
        label="Select Parent",
        help_text="Choose an existing parent to link to this student."
    )
    is_primary_contact = forms.BooleanField(
        required=False,
        label="Set as primary contact"
    )
    is_emergency_contact = forms.BooleanField(
        required=False,
        label="Set as emergency contact"
    )

    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        # Get parents not already linked to this student
        if self.student:
            linked_parents = self.student.parents.all()
            self.fields['parent'].queryset = Parent.objects.exclude(
                pk__in=linked_parents.values_list('pk', flat=True)
            )

        # Apply styling
        self.fields['parent'].widget.attrs['class'] = 'select select-bordered select-sm w-full'
        self.fields['is_primary_contact'].widget.attrs['class'] = 'checkbox checkbox-primary checkbox-sm'
        self.fields['is_emergency_contact'].widget.attrs['class'] = 'checkbox checkbox-primary checkbox-sm'

    def save(self):
        parent = self.cleaned_data['parent']

        if self.student:
            parent.students.add(self.student)

            # Update contact preferences if set
            if self.cleaned_data.get('is_primary_contact'):
                parent.is_primary_contact = True
            if self.cleaned_data.get('is_emergency_contact'):
                parent.is_emergency_contact = True
            parent.save()

        return parent


class ParentUpdateForm(ParentForm):
    """
    A form for updating an existing Parent's details.
    """
    email = forms.EmailField(
        required=True,
        label="Parent's Email",
        help_text="This will be used for the parent's login account."
    )

    class Meta(ParentForm.Meta):
        fields = ['email'] + ParentForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    @transaction.atomic
    def save(self, commit=True):
        parent = super().save(commit=False)
        user = parent.user
        new_email = self.cleaned_data.get('email')

        if user.email != new_email:
            if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                self.add_error('email', 'A user with this email already exists.')
                raise forms.ValidationError("User already exists.")
            user.email = new_email
            user.save()

        if commit:
            parent.save()
            self.save_m2m()
        return parent
