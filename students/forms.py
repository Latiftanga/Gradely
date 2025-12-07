from django import forms
from django.db import transaction
from .models import Student, Parent
from accounts.models import User


class StudentBulkImportForm(forms.Form):
    """Form for bulk importing students from CSV/XLSX files."""
    file = forms.FileField(
        label="Import File",
        help_text="Upload a CSV or XLSX file with student data."
    )
    default_password = forms.CharField(
        max_length=128,
        initial='changeme123',
        label="Default Password",
        help_text="Initial password for all imported student accounts."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs['class'] = 'file-input file-input-bordered file-input-sm w-full'
        self.fields['file'].widget.attrs['accept'] = '.csv,.xlsx,.xls'
        self.fields['default_password'].widget.attrs['class'] = 'input input-bordered input-sm w-full'

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
    A form specifically for creating a new Student, which also involves creating a new User account.
    Inherits most fields from StudentForm, but adds email and password for user creation.
    """
    email = forms.EmailField(
        required=True,
        label="Student's Email",
        help_text="This will be used for the student's login account."
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Initial Password",
        help_text="Set an initial password for the student's account."
    )

    class Meta(StudentForm.Meta):
        fields = ['email', 'password'] + StudentForm.Meta.fields

    @transaction.atomic
    def save(self, commit=True):
        """
        Override the save method to handle the creation of both a User and a Student.
        """
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.add_error('email', 'A user with this email already exists.')
            raise forms.ValidationError("User already exists.")

        # Create the User instance
        user = User.objects.create_studentuser(email=email, password=password)

        # Create the Student instance, but don't save it to the DB yet
        student = super().save(commit=False)
        student.user = user  # Link the student profile to the new user

        if commit:
            student.save()

        return student


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
    """
    email = forms.EmailField(
        required=True,
        label="Parent's Email",
        help_text="This will be used for the parent's login account."
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Initial Password",
        help_text="Set an initial password for the parent's account."
    )

    class Meta(ParentForm.Meta):
        fields = ['email', 'password'] + ParentForm.Meta.fields

    @transaction.atomic
    def save(self, commit=True):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if User.objects.filter(email=email).exists():
            self.add_error('email', 'A user with this email already exists.')
            raise forms.ValidationError("User already exists.")

        # Create the User instance (assuming there's a create_parentuser method)
        user = User.objects.create_user(email=email, password=password, role='parent')

        parent = super().save(commit=False)
        parent.user = user

        if commit:
            parent.save()
            # Save M2M relationships
            self.save_m2m()

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
