from django import forms
from .models import (
    Programme, GradeLevel, AcademicYear, Term, Class, Subject, ClassSubject,
    ClassEnrollment
)
from teachers.models import Teacher


class ProgrammeForm(forms.ModelForm):
    """Form for creating and editing programmes"""

    class Meta:
        model = Programme
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., General Science'
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., SCI'
            }),
            'description': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Brief description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
        }


class GradeLevelForm(forms.ModelForm):
    """Form for creating and editing grade levels"""

    class Meta:
        model = GradeLevel
        fields = ['name', 'code', 'level_type', 'numeric_level', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Form 1, Primary 3'
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., F1, P3'
            }),
            'level_type': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'numeric_level': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': 1, 'max': 6
            }),
            'order': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
        }


class AcademicYearForm(forms.ModelForm):
    """Form for creating and editing academic years"""

    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., 2024/2025'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
        }


class TermForm(forms.ModelForm):
    """Form for creating and editing terms"""

    class Meta:
        model = Term
        fields = ['academic_year', 'term_number', 'start_date', 'end_date', 'is_current', 'is_active']
        widgets = {
            'academic_year': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'term_number': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
        }


class ClassForm(forms.ModelForm):
    """Form for creating and editing classes (year-independent)"""

    class Meta:
        model = Class
        fields = [
            'grade_level', 'section', 'programme', 'capacity',
            'class_teacher', 'room_number', 'building', 'is_active'
        ]
        widgets = {
            'grade_level': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'section': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., A, Gold'
            }),
            'programme': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': 1
            }),
            'class_teacher': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Room 101'
            }),
            'building': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Science Block'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active teachers
        self.fields['class_teacher'].queryset = Teacher.objects.filter(is_active=True)
        self.fields['class_teacher'].required = False
        self.fields['programme'].required = False


class ClassEnrollmentForm(forms.ModelForm):
    """Form for enrolling a student in a class for an academic year"""

    class Meta:
        model = ClassEnrollment
        fields = ['student', 'class_instance', 'academic_year', 'is_active', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'class_instance': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered textarea-sm w-full',
                'rows': 2,
                'placeholder': 'Optional notes about this enrollment'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['class_instance'].queryset = Class.objects.filter(is_active=True)
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_active=True)


class BulkEnrollmentForm(forms.Form):
    """Form for enrolling multiple students in a class"""
    class_instance = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full'
        }),
        label='Class'
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full'
        })
    )


class SubjectForm(forms.ModelForm):
    """Form for creating and editing subjects"""

    class Meta:
        model = Subject
        fields = [
            'name', 'code', 'description', 'subject_type',
            'applicable_levels', 'programmes', 'credit_hours', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Mathematics'
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., MATH'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered textarea-sm w-full',
                'rows': 2,
                'placeholder': 'Brief description of the subject'
            }),
            'subject_type': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'applicable_levels': forms.SelectMultiple(attrs={
                'class': 'select select-bordered select-sm w-full h-24'
            }),
            'programmes': forms.SelectMultiple(attrs={
                'class': 'select select-bordered select-sm w-full h-24'
            }),
            'credit_hours': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'step': '0.5', 'min': '0.5'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
        }


class ClassSubjectForm(forms.ModelForm):
    """Form for assigning subjects to classes with teachers"""

    class Meta:
        model = ClassSubject
        fields = ['class_instance', 'subject', 'teacher', 'periods_per_week', 'is_active']
        widgets = {
            'class_instance': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'subject': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'teacher': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'periods_per_week': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': 1, 'max': 20
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary checkbox-sm'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = Teacher.objects.filter(is_active=True)
        self.fields['teacher'].required = False
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True)
        self.fields['class_instance'].queryset = Class.objects.filter(is_active=True)


class BulkClassSubjectForm(forms.Form):
    """Form for bulk assigning subjects to a class"""
    class_instance = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full'
        })
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox checkbox-primary checkbox-sm'
        })
    )


class PromotionForm(forms.Form):
    """Form for promoting/demoting students between classes"""
    PROMOTION_TYPE_CHOICES = [
        ('promote', 'Promote to next level'),
        ('graduate', 'Graduate (final year students)'),
        ('demote', 'Demote to previous level'),
        ('transfer', 'Transfer to another class (same level)'),
        ('repeat', 'Repeat current class'),
    ]

    source_academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full',
            'id': 'source_academic_year'
        }),
        label='From Academic Year'
    )
    source_class = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full',
            'id': 'source_class'
        }),
        label='From Class'
    )
    target_academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full',
            'id': 'target_academic_year'
        }),
        label='To Academic Year',
        required=False  # Not required for graduation
    )
    target_class = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full',
            'id': 'target_class'
        }),
        label='To Class',
        required=False  # Not required for graduation
    )
    promotion_type = forms.ChoiceField(
        choices=PROMOTION_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full',
            'id': 'promotion_type'
        }),
        initial='promote'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order academic years by most recent first
        self.fields['source_academic_year'].queryset = AcademicYear.objects.filter(
            is_active=True
        ).order_by('-start_date')
        self.fields['target_academic_year'].queryset = AcademicYear.objects.filter(
            is_active=True
        ).order_by('-start_date')
        # Order classes by grade level
        self.fields['source_class'].queryset = Class.objects.filter(
            is_active=True
        ).select_related('grade_level', 'programme').order_by('grade_level__order', 'section')
        self.fields['target_class'].queryset = Class.objects.filter(
            is_active=True
        ).select_related('grade_level', 'programme').order_by('grade_level__order', 'section')

    def clean(self):
        cleaned_data = super().clean()
        source_year = cleaned_data.get('source_academic_year')
        target_year = cleaned_data.get('target_academic_year')
        source_class = cleaned_data.get('source_class')
        target_class = cleaned_data.get('target_class')
        promotion_type = cleaned_data.get('promotion_type')

        # For graduation, target class/year not required
        if promotion_type == 'graduate':
            return cleaned_data

        # For other actions, target class and year are required
        if not target_year:
            self.add_error('target_academic_year', 'Target academic year is required.')
        if not target_class:
            self.add_error('target_class', 'Target class is required.')

        if source_year and target_year and source_year == target_year:
            if source_class and target_class and source_class == target_class:
                raise forms.ValidationError(
                    "Source and target must be different when using the same academic year."
                )

        return cleaned_data
