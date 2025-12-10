import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib import messages

from students.models import Student
from teachers.models import Teacher
from academics.models import Class, AcademicYear, GradeLevel, Programme, Term
from academics.forms import AcademicYearForm, GradeLevelForm, ProgrammeForm, TermForm
from grades.models import GradeScale, GradeLevel as GradeScaleLevel, AssessmentType
from grades.forms import GradeScaleForm, GradeLevelForm as GradeScaleLevelForm, AssessmentTypeForm, GradeLevelFormSet
from .models import SchoolSettings
from .forms import SchoolSettingsForm

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """
    Renders the main dashboard layout for a logged-in tenant user.
    The actual content is loaded via HTMX.
    """
    return render(request, 'dashboard/dashboard.html')


@login_required
def main_partial_view(request):
    """
    Renders the main dashboard content (widgets) for HTMX requests.
    Fetches real statistics from the database for the current tenant.
    """
    try:
        breadcrumbs = [
            {'name': 'Dashboard', 'url': ''},
        ]

        # Get current academic year
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()

        # Calculate real statistics
        total_students = Student.objects.filter(is_active=True).count()
        total_teachers = Teacher.objects.filter(is_active=True).count()

        # Get total active classes
        total_classes = Class.objects.filter(is_active=True).count()

        # Calculate student distribution by gender
        student_distribution = Student.objects.filter(is_active=True).aggregate(
            male_count=Count('user_id', filter=Q(gender='M')),
            female_count=Count('user_id', filter=Q(gender='F')),
            total=Count('user_id')
        )

        # Calculate percentages
        total = student_distribution['total']
        if total > 0:
            male_percentage = round((student_distribution['male_count'] / total) * 100, 1)
            female_percentage = round((student_distribution['female_count'] / total) * 100, 1)
        else:
            male_percentage = 0
            female_percentage = 0

        # Get recent students (as placeholder for recent activity)
        # TODO: Replace with actual activity tracking when implemented
        recent_students = Student.objects.filter(
            is_active=True
        ).select_related('user', 'current_class__grade_level').order_by('-date_enrolled')[:5]

        # Get student distribution by level type
        from academics.models import GradeLevel
        from django.db.models import OuterRef, Subquery

        level_distribution = []
        for level_type, level_name in GradeLevel.LEVEL_TYPE_CHOICES:
            count = Student.objects.filter(
                is_active=True,
                current_class__grade_level__level_type=level_type
            ).count()

            if total > 0:
                percentage = round((count / total) * 100, 1)
            else:
                percentage = 0

            level_distribution.append({
                'name': level_name,
                'count': count,
                'percentage': percentage
            })

        context = {
            'breadcrumbs': breadcrumbs,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'male_percentage': male_percentage,
            'female_percentage': female_percentage,
            'male_count': student_distribution['male_count'],
            'female_count': student_distribution['female_count'],
            'recent_students': recent_students,
            'current_academic_year': current_academic_year,
            'level_distribution': level_distribution,
        }

        logger.info(
            f"Dashboard stats loaded for user {request.user.email}: "
            f"{total_students} students, {total_teachers} teachers, {total_classes} classes"
        )

        return render(request, 'dashboard/partials/dashboard_main.html', context)

    except Exception as e:
        logger.error(f"Error loading dashboard stats for user {request.user.email}: {str(e)}", exc_info=True)
        # Return a simplified error view
        context = {
            'breadcrumbs': [{'name': 'Dashboard', 'url': ''}],
            'error': 'Unable to load dashboard statistics. Please try again later.',
        }
        return render(request, 'dashboard/partials/dashboard_main.html', context)


# ==================== Settings Views ====================

@login_required
def settings_view(request):
    """
    Unified settings page with tabs for all school settings.
    """
    # Get the active tab from query params (default to school-info)
    active_tab = request.GET.get('tab', 'school-info')

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Settings', 'url': ''},
    ]

    # Get all data needed for the settings page
    school_settings = SchoolSettings.get_settings()
    school_form = SchoolSettingsForm(instance=school_settings)

    academic_years = AcademicYear.objects.annotate(
        term_count=Count('terms'),
        enrollment_count=Count('enrollments')
    )
    terms = Term.objects.select_related('academic_year').order_by('-academic_year__start_date', 'term_number')
    grade_levels = GradeLevel.objects.annotate(class_count=Count('classes'))
    programmes = Programme.objects.annotate(
        class_count=Count('classes'),
        subject_count=Count('subjects')
    )
    grading_scales = GradeScale.objects.prefetch_related('levels').order_by('level_type', 'name')
    assessment_types = AssessmentType.objects.order_by('order', 'name')

    context = {
        'breadcrumbs': breadcrumbs,
        'active_tab': active_tab,
        'school_settings': school_settings,
        'school_form': school_form,
        'academic_years': academic_years,
        'terms': terms,
        'grade_levels': grade_levels,
        'programmes': programmes,
        'grading_scales': grading_scales,
        'assessment_types': assessment_types,
    }

    if request.htmx:
        return render(request, 'dashboard/settings.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('dashboard:settings'),
        'active_sidebar_link': 'dashboard:settings',
        'page_title': 'Settings',
    })


@login_required
def settings_school_info_view(request):
    """Handle school info form submission"""
    school_settings = SchoolSettings.get_settings()

    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, request.FILES, instance=school_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'School settings updated successfully.')
            if request.htmx:
                # Return the updated school info tab
                context = {
                    'school_settings': school_settings,
                    'school_form': SchoolSettingsForm(instance=school_settings),
                }
                response = render(request, 'dashboard/partials/settings_school_info.html', context)
                response['HX-Trigger'] = 'settingsSaved'
                return response
            return redirect('dashboard:settings')
        else:
            if request.htmx:
                context = {
                    'school_settings': school_settings,
                    'school_form': form,
                }
                return render(request, 'dashboard/partials/settings_school_info.html', context)
    else:
        form = SchoolSettingsForm(instance=school_settings)

    context = {
        'school_settings': school_settings,
        'school_form': form,
    }

    if request.htmx:
        return render(request, 'dashboard/partials/settings_school_info.html', context)

    return redirect('dashboard:settings')


@login_required
def settings_academic_years_view(request):
    """Return academic years tab content"""
    academic_years = AcademicYear.objects.annotate(
        term_count=Count('terms'),
        enrollment_count=Count('enrollments')
    )
    context = {'academic_years': academic_years}

    if request.htmx:
        return render(request, 'dashboard/partials/settings_academic_years.html', context)
    return redirect('dashboard:settings')


@login_required
def settings_terms_view(request):
    """Return terms tab content"""
    terms = Term.objects.select_related('academic_year').order_by('-academic_year__start_date', 'term_number')
    academic_years = AcademicYear.objects.filter(is_active=True)
    context = {
        'terms': terms,
        'academic_years': academic_years,
    }

    if request.htmx:
        return render(request, 'dashboard/partials/settings_terms.html', context)
    return redirect('dashboard:settings')


@login_required
def settings_grade_levels_view(request):
    """Return grade levels tab content"""
    grade_levels = GradeLevel.objects.annotate(class_count=Count('classes'))
    context = {'grade_levels': grade_levels}

    if request.htmx:
        return render(request, 'dashboard/partials/settings_grade_levels.html', context)
    return redirect('dashboard:settings')


@login_required
def settings_programmes_view(request):
    """Return programmes tab content"""
    programmes = Programme.objects.annotate(
        class_count=Count('classes'),
        subject_count=Count('subjects')
    )
    context = {'programmes': programmes}

    if request.htmx:
        return render(request, 'dashboard/partials/settings_programmes.html', context)
    return redirect('dashboard:settings')


@login_required
def settings_grading_scales_view(request):
    """Return grading scales tab content"""
    grading_scales = GradeScale.objects.prefetch_related('levels').order_by('level_type', 'name')
    context = {'grading_scales': grading_scales}

    if request.htmx:
        return render(request, 'dashboard/partials/settings_grading_scales.html', context)
    return redirect('dashboard:settings')


@login_required
def settings_assessment_types_view(request):
    """Return assessment types tab content"""
    assessment_types = AssessmentType.objects.order_by('order', 'name')
    context = {'assessment_types': assessment_types}

    if request.htmx:
        return render(request, 'dashboard/partials/settings_assessment_types.html', context)
    return redirect('dashboard:settings')


# ==================== Grading Scale CRUD ====================

@login_required
def grading_scale_add_view(request):
    """Add a new grading scale"""
    if request.method == 'POST':
        form = GradeScaleForm(request.POST)
        formset = GradeLevelFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            scale = form.save()
            formset.instance = scale
            formset.save()
            messages.success(request, f'Grading scale "{scale.name}" created successfully.')
            if request.htmx:
                response = render(request, 'dashboard/partials/settings_grading_scales.html', {
                    'grading_scales': GradeScale.objects.prefetch_related('levels').order_by('level_type', 'name')
                })
                response['HX-Trigger'] = 'closeModal, settingsSaved'
                return response
            return redirect('dashboard:settings')
    else:
        form = GradeScaleForm()
        formset = GradeLevelFormSet()

    context = {
        'form': form,
        'formset': formset,
        'modal_title': 'Add Grading Scale',
    }
    return render(request, 'dashboard/partials/grading_scale_form_modal.html', context)


@login_required
def grading_scale_edit_view(request, pk):
    """Edit a grading scale"""
    from django.shortcuts import get_object_or_404
    scale = get_object_or_404(GradeScale, pk=pk)

    if request.method == 'POST':
        form = GradeScaleForm(request.POST, instance=scale)
        formset = GradeLevelFormSet(request.POST, instance=scale)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Grading scale "{scale.name}" updated successfully.')
            if request.htmx:
                response = render(request, 'dashboard/partials/settings_grading_scales.html', {
                    'grading_scales': GradeScale.objects.prefetch_related('levels').order_by('level_type', 'name')
                })
                response['HX-Trigger'] = 'closeModal, settingsSaved'
                return response
            return redirect('dashboard:settings')
    else:
        form = GradeScaleForm(instance=scale)
        formset = GradeLevelFormSet(instance=scale)

    context = {
        'form': form,
        'formset': formset,
        'scale': scale,
        'modal_title': f'Edit {scale.name}',
    }
    return render(request, 'dashboard/partials/grading_scale_form_modal.html', context)


@login_required
def grading_scale_delete_view(request, pk):
    """Delete a grading scale"""
    from django.shortcuts import get_object_or_404
    scale = get_object_or_404(GradeScale, pk=pk)

    if request.method == 'POST':
        name = scale.name
        scale.delete()
        messages.success(request, f'Grading scale "{name}" deleted successfully.')
        if request.htmx:
            response = render(request, 'dashboard/partials/settings_grading_scales.html', {
                'grading_scales': GradeScale.objects.prefetch_related('levels').order_by('level_type', 'name')
            })
            response['HX-Trigger'] = 'closeModal, settingsSaved'
            return response
        return redirect('dashboard:settings')

    context = {
        'scale': scale,
    }
    return render(request, 'dashboard/partials/grading_scale_delete_modal.html', context)


# ==================== Assessment Type CRUD ====================

@login_required
def assessment_type_add_view(request):
    """Add a new assessment type"""
    if request.method == 'POST':
        form = AssessmentTypeForm(request.POST)
        if form.is_valid():
            assessment_type = form.save()
            messages.success(request, f'Assessment type "{assessment_type.name}" created successfully.')
            if request.htmx:
                response = render(request, 'dashboard/partials/settings_assessment_types.html', {
                    'assessment_types': AssessmentType.objects.order_by('order', 'name')
                })
                response['HX-Trigger'] = 'closeModal, settingsSaved'
                return response
            return redirect('dashboard:settings')
    else:
        form = AssessmentTypeForm()

    context = {
        'form': form,
        'modal_title': 'Add Assessment Type',
    }
    return render(request, 'dashboard/partials/assessment_type_form_modal.html', context)


@login_required
def assessment_type_edit_view(request, pk):
    """Edit an assessment type"""
    from django.shortcuts import get_object_or_404
    assessment_type = get_object_or_404(AssessmentType, pk=pk)

    if request.method == 'POST':
        form = AssessmentTypeForm(request.POST, instance=assessment_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Assessment type "{assessment_type.name}" updated successfully.')
            if request.htmx:
                response = render(request, 'dashboard/partials/settings_assessment_types.html', {
                    'assessment_types': AssessmentType.objects.order_by('order', 'name')
                })
                response['HX-Trigger'] = 'closeModal, settingsSaved'
                return response
            return redirect('dashboard:settings')
    else:
        form = AssessmentTypeForm(instance=assessment_type)

    context = {
        'form': form,
        'assessment_type': assessment_type,
        'modal_title': f'Edit {assessment_type.name}',
    }
    return render(request, 'dashboard/partials/assessment_type_form_modal.html', context)


@login_required
def assessment_type_delete_view(request, pk):
    """Delete an assessment type"""
    from django.shortcuts import get_object_or_404
    assessment_type = get_object_or_404(AssessmentType, pk=pk)

    if request.method == 'POST':
        name = assessment_type.name
        assessment_type.delete()
        messages.success(request, f'Assessment type "{name}" deleted successfully.')
        if request.htmx:
            response = render(request, 'dashboard/partials/settings_assessment_types.html', {
                'assessment_types': AssessmentType.objects.order_by('order', 'name')
            })
            response['HX-Trigger'] = 'closeModal, settingsSaved'
            return response
        return redirect('dashboard:settings')

    context = {
        'assessment_type': assessment_type,
    }
    return render(request, 'dashboard/partials/assessment_type_delete_modal.html', context)