"""
Forms for grades app
"""
from django import forms
from django.forms import inlineformset_factory
from .models import GradeScale, GradeLevel, AssessmentType, Assessment, Grade


class GradeScaleForm(forms.ModelForm):
    """Form for creating/editing grade scales"""

    class Meta:
        model = GradeScale
        fields = ['name', 'level_type', 'description', 'is_default', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., WASSCE Scale, BECE Scale'
            }),
            'level_type': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Optional description'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }


class GradeLevelForm(forms.ModelForm):
    """Form for grade levels within a scale"""

    class Meta:
        model = GradeLevel
        fields = ['grade', 'description', 'min_score', 'max_score', 'grade_point', 'order']
        widgets = {
            'grade': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-16',
                'placeholder': 'A1'
            }),
            'description': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-32',
                'placeholder': 'Excellent'
            }),
            'min_score': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-20',
                'step': '0.01'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-20',
                'step': '0.01'
            }),
            'grade_point': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-16',
                'step': '0.01'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-16'
            }),
        }


# Formset for managing grade levels inline with a scale
GradeLevelFormSet = inlineformset_factory(
    GradeScale,
    GradeLevel,
    form=GradeLevelForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class AssessmentTypeForm(forms.ModelForm):
    """Form for creating/editing assessment types"""

    class Meta:
        model = AssessmentType
        fields = ['name', 'code', 'description', 'weight', 'is_exam', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., End of Term Exam'
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., EXAM'
            }),
            'description': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Optional description'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'is_exam': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': '0'
            }),
        }


class AssessmentForm(forms.ModelForm):
    """Form for creating/editing assessments"""

    class Meta:
        model = Assessment
        fields = [
            'class_subject', 'term', 'assessment_type', 'title',
            'description', 'max_score', 'weight', 'date', 'due_date',
            'is_published', 'is_active'
        ]
        widgets = {
            'class_subject': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'term': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'assessment_type': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., Mid-Term Examination'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Optional description or instructions'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',
                'min': '0'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',
                'min': '0'
            }),
            'date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter class_subject to only show subjects assigned to this teacher
        if teacher:
            from academics.models import ClassSubject
            self.fields['class_subject'].queryset = ClassSubject.objects.filter(
                teacher=teacher,
                is_active=True
            ).select_related('class_instance', 'subject')

        # Filter to show only active terms
        from academics.models import Term
        self.fields['term'].queryset = Term.objects.filter(
            is_active=True
        ).select_related('academic_year').order_by('-academic_year__start_date', 'term_number')

        # Filter to show only active assessment types
        self.fields['assessment_type'].queryset = AssessmentType.objects.filter(
            is_active=True
        ).order_by('order', 'name')


class GradeForm(forms.ModelForm):
    """Form for individual grade entry"""

    class Meta:
        model = Grade
        fields = ['score', 'remarks', 'is_absent', 'is_excused']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-20',
                'step': '0.01',
                'min': '0'
            }),
            'remarks': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Optional remarks'
            }),
            'is_absent': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-sm'
            }),
            'is_excused': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-sm'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        score = cleaned_data.get('score')
        is_absent = cleaned_data.get('is_absent')
        is_excused = cleaned_data.get('is_excused')

        # If student was absent, score should be null
        if is_absent and score is not None:
            cleaned_data['score'] = None

        # is_excused only makes sense if is_absent
        if is_excused and not is_absent:
            cleaned_data['is_excused'] = False

        return cleaned_data


class BulkGradeForm(forms.Form):
    """Form for bulk grade entry - one form per student"""
    student_id = forms.IntegerField(widget=forms.HiddenInput())
    student_name = forms.CharField(widget=forms.HiddenInput())  # For display
    score = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered input-sm w-24',
            'step': '0.01',
            'min': '0'
        })
    )
    remarks = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered input-sm',
            'placeholder': 'Remarks'
        })
    )
    is_absent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-sm'
        })
    )

    def __init__(self, *args, max_score=100, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['score'].widget.attrs['max'] = str(max_score)
        self.max_score = max_score

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None and score > self.max_score:
            raise forms.ValidationError(f'Score cannot exceed {self.max_score}')
        return score
