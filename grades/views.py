"""
Views for grades/assessments management
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count, Avg, Q
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal

from .models import Assessment, AssessmentType, Grade, GradeScale, GradeLevel
from .forms import AssessmentForm, GradeForm, BulkGradeForm, AssessmentTypeForm, GradeScaleForm, GradeLevelFormSet
from academics.models import Term, ClassSubject, ClassEnrollment, AcademicYear
from teachers.models import Teacher


def _get_teacher_for_user(user):
    """Get teacher instance for the current user"""
    if hasattr(user, 'teacher_profile'):
        return user.teacher_profile
    return None


def _get_filtered_assessments(request, teacher=None):
    """Helper to get filtered assessments queryset and context"""
    assessments = Assessment.objects.select_related(
        'class_subject__class_instance__grade_level',
        'class_subject__subject',
        'term__academic_year',
        'assessment_type',
        'created_by'
    ).annotate(
        grades_count=Count('grades'),
        average=Avg('grades__score')
    )

    # If teacher is provided, filter to their subjects only
    if teacher:
        assessments = assessments.filter(class_subject__teacher=teacher)

    # Get filter options
    terms = Term.objects.filter(is_active=True).select_related('academic_year').order_by(
        '-academic_year__start_date', 'term_number'
    )
    assessment_types = AssessmentType.objects.filter(is_active=True).order_by('order', 'name')

    if teacher:
        class_subjects = ClassSubject.objects.filter(
            teacher=teacher, is_active=True
        ).select_related('class_instance__grade_level', 'subject')
    else:
        class_subjects = ClassSubject.objects.filter(is_active=True).select_related(
            'class_instance__grade_level', 'subject'
        )

    # Apply filters
    selected_term = request.GET.get('term')
    selected_type = request.GET.get('type')
    selected_class_subject = request.GET.get('class_subject')
    selected_status = request.GET.get('status')
    search = request.GET.get('q', '').strip()

    if selected_term:
        assessments = assessments.filter(term_id=selected_term)
    if selected_type:
        assessments = assessments.filter(assessment_type_id=selected_type)
    if selected_class_subject:
        assessments = assessments.filter(class_subject_id=selected_class_subject)
    if selected_status == 'published':
        assessments = assessments.filter(is_published=True)
    elif selected_status == 'unpublished':
        assessments = assessments.filter(is_published=False)
    if search:
        assessments = assessments.filter(
            Q(title__icontains=search) |
            Q(class_subject__subject__name__icontains=search) |
            Q(class_subject__class_instance__grade_level__name__icontains=search)
        )

    # Get counts
    total_count = assessments.count()
    published_count = assessments.filter(is_published=True).count()

    return {
        'assessments': assessments.order_by('-created_at'),
        'terms': terms,
        'assessment_types': assessment_types,
        'class_subjects': class_subjects,
        'total_count': total_count,
        'published_count': published_count,
        'selected_term': selected_term or '',
        'selected_type': selected_type or '',
        'selected_class_subject': selected_class_subject or '',
        'selected_status': selected_status or '',
        'search_query': search,
    }


@login_required
def assessment_list_view(request):
    """List all assessments for the teacher"""
    teacher = _get_teacher_for_user(request.user)
    context = _get_filtered_assessments(request, teacher=teacher)
    context['teacher'] = teacher

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Assessments', 'url': ''},
    ]
    context['breadcrumbs'] = breadcrumbs

    if request.htmx:
        return render(request, 'grades/assessment_list.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('grades:assessment_list'),
        'active_sidebar_link': 'grades:assessment_list',
        'page_title': 'Assessments',
    })


@login_required
def assessment_list_partial_view(request):
    """Return just the assessment list partial for filtering"""
    teacher = _get_teacher_for_user(request.user)
    context = _get_filtered_assessments(request, teacher=teacher)
    return render(request, 'grades/partials/assessment_table.html', context)


@login_required
def assessment_add_view(request):
    """Create a new assessment"""
    teacher = _get_teacher_for_user(request.user)

    if request.method == 'POST':
        form = AssessmentForm(request.POST, teacher=teacher)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.created_by = teacher
            assessment.save()
            messages.success(request, f'Assessment "{assessment.title}" created successfully.')
            if request.htmx:
                response = render(request, 'grades/partials/assessment_add_success.html', {'assessment': assessment})
                response['HX-Trigger'] = 'assessmentAdded'
                return response
            return redirect('grades:assessment_detail', pk=assessment.pk)
    else:
        form = AssessmentForm(teacher=teacher)

    context = {
        'form': form,
        'modal_title': 'Create Assessment',
    }

    if request.htmx:
        return render(request, 'grades/partials/assessment_form_modal.html', context)

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Assessments', 'url': reverse('grades:assessment_list')},
        {'name': 'Create', 'url': ''},
    ]
    context['breadcrumbs'] = breadcrumbs
    return render(request, 'grades/assessment_form.html', context)


@login_required
def assessment_detail_view(request, pk):
    """View assessment details and grades"""
    teacher = _get_teacher_for_user(request.user)
    assessment = get_object_or_404(
        Assessment.objects.select_related(
            'class_subject__class_instance__grade_level',
            'class_subject__subject',
            'class_subject__teacher',
            'term__academic_year',
            'assessment_type',
            'created_by'
        ),
        pk=pk
    )

    # Check if teacher has access to this assessment
    if teacher and assessment.class_subject.teacher != teacher:
        messages.error(request, 'You do not have permission to view this assessment.')
        return redirect('grades:assessment_list')

    # Get students enrolled in this class for the assessment's term
    class_instance = assessment.class_subject.class_instance
    academic_year = assessment.term.academic_year

    enrollments = ClassEnrollment.objects.filter(
        class_instance=class_instance,
        academic_year=academic_year,
        is_active=True
    ).select_related('student__user').order_by('student__last_name', 'student__first_name')

    # Get existing grades for this assessment
    grades = {g.student_id: g for g in assessment.grades.select_related('student')}

    # Build student list with their grades
    student_grades = []
    for enrollment in enrollments:
        student = enrollment.student
        grade = grades.get(student.pk)
        student_grades.append({
            'student': student,
            'grade': grade,
            'score': grade.score if grade else None,
            'percentage': grade.percentage if grade else None,
            'letter_grade': grade.letter_grade if grade else None,
            'is_absent': grade.is_absent if grade else False,
            'remarks': grade.remarks if grade else '',
        })

    # Calculate statistics
    graded_count = len([sg for sg in student_grades if sg['score'] is not None])
    total_students = len(student_grades)
    average_score = assessment.average_score

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Assessments', 'url': reverse('grades:assessment_list')},
        {'name': assessment.title, 'url': ''},
    ]

    context = {
        'assessment': assessment,
        'student_grades': student_grades,
        'graded_count': graded_count,
        'total_students': total_students,
        'average_score': average_score,
        'breadcrumbs': breadcrumbs,
    }

    if request.htmx:
        return render(request, 'grades/assessment_detail.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('grades:assessment_detail', kwargs={'pk': pk}),
        'active_sidebar_link': 'grades:assessment_list',
        'page_title': f'Assessment - {assessment.title}',
    })


@login_required
def assessment_update_view(request, pk):
    """Update assessment details"""
    teacher = _get_teacher_for_user(request.user)
    assessment = get_object_or_404(Assessment, pk=pk)

    # Check permission
    if teacher and assessment.class_subject.teacher != teacher:
        messages.error(request, 'You do not have permission to edit this assessment.')
        return redirect('grades:assessment_list')

    if request.method == 'POST':
        form = AssessmentForm(request.POST, instance=assessment, teacher=teacher)
        if form.is_valid():
            assessment = form.save()
            messages.success(request, f'Assessment "{assessment.title}" updated successfully.')
            if request.htmx:
                response = render(request, 'grades/partials/assessment_update_success.html', {'assessment': assessment})
                response['HX-Trigger'] = 'assessmentUpdated'
                return response
            return redirect('grades:assessment_detail', pk=assessment.pk)
    else:
        form = AssessmentForm(instance=assessment, teacher=teacher)

    context = {
        'form': form,
        'assessment': assessment,
        'modal_title': f'Edit {assessment.title}',
    }

    if request.htmx:
        return render(request, 'grades/partials/assessment_form_modal.html', context)

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Assessments', 'url': reverse('grades:assessment_list')},
        {'name': assessment.title, 'url': reverse('grades:assessment_detail', kwargs={'pk': pk})},
        {'name': 'Edit', 'url': ''},
    ]
    context['breadcrumbs'] = breadcrumbs
    return render(request, 'grades/assessment_form.html', context)


@login_required
def assessment_delete_view(request, pk):
    """Delete an assessment"""
    teacher = _get_teacher_for_user(request.user)
    assessment = get_object_or_404(Assessment, pk=pk)

    # Check permission
    if teacher and assessment.class_subject.teacher != teacher:
        messages.error(request, 'You do not have permission to delete this assessment.')
        return redirect('grades:assessment_list')

    if request.method == 'POST':
        title = assessment.title
        assessment.delete()
        messages.success(request, f'Assessment "{title}" deleted successfully.')

        if request.htmx:
            response = render(request, 'grades/partials/assessment_delete_success.html')
            response['HX-Trigger'] = 'assessmentDeleted'
            return response
        return redirect('grades:assessment_list')

    context = {
        'assessment': assessment,
    }

    if request.htmx:
        return render(request, 'grades/partials/assessment_delete_modal.html', context)

    return redirect('grades:assessment_list')


@login_required
def grade_entry_view(request, assessment_pk):
    """Enter/edit grades for all students in an assessment"""
    teacher = _get_teacher_for_user(request.user)
    assessment = get_object_or_404(
        Assessment.objects.select_related(
            'class_subject__class_instance__grade_level',
            'class_subject__subject',
            'term__academic_year'
        ),
        pk=assessment_pk
    )

    # Check permission
    if teacher and assessment.class_subject.teacher != teacher:
        messages.error(request, 'You do not have permission to enter grades for this assessment.')
        return redirect('grades:assessment_list')

    # Get students enrolled in this class
    class_instance = assessment.class_subject.class_instance
    academic_year = assessment.term.academic_year

    enrollments = ClassEnrollment.objects.filter(
        class_instance=class_instance,
        academic_year=academic_year,
        is_active=True
    ).select_related('student__user').order_by('student__last_name', 'student__first_name')

    # Get existing grades
    existing_grades = {g.student_id: g for g in assessment.grades.all()}

    if request.method == 'POST':
        # Process grade submissions
        saved_count = 0
        for enrollment in enrollments:
            student = enrollment.student
            prefix = f'student_{student.pk}'

            score_str = request.POST.get(f'{prefix}_score', '').strip()
            is_absent = request.POST.get(f'{prefix}_absent') == 'on'
            remarks = request.POST.get(f'{prefix}_remarks', '').strip()

            # Parse score
            score = None
            if score_str and not is_absent:
                try:
                    score = Decimal(score_str)
                    if score < 0 or score > assessment.max_score:
                        continue  # Skip invalid scores
                except (ValueError, TypeError):
                    continue

            # Get or create grade
            grade, created = Grade.objects.get_or_create(
                assessment=assessment,
                student=student,
                defaults={
                    'score': score,
                    'is_absent': is_absent,
                    'remarks': remarks,
                    'graded_by': teacher,
                }
            )

            if not created:
                grade.score = score
                grade.is_absent = is_absent
                grade.remarks = remarks
                grade.graded_by = teacher
                grade.save()

            saved_count += 1

        messages.success(request, f'Grades saved for {saved_count} students.')

        if request.htmx:
            response = render(request, 'grades/partials/grade_entry_success.html', {
                'assessment': assessment,
                'saved_count': saved_count,
            })
            response['HX-Trigger'] = 'gradesSaved'
            return response
        return redirect('grades:assessment_detail', pk=assessment_pk)

    # Build student data for template
    student_data = []
    for enrollment in enrollments:
        student = enrollment.student
        existing_grade = existing_grades.get(student.pk)
        student_data.append({
            'student': student,
            'score': existing_grade.score if existing_grade else '',
            'is_absent': existing_grade.is_absent if existing_grade else False,
            'remarks': existing_grade.remarks if existing_grade else '',
        })

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Assessments', 'url': reverse('grades:assessment_list')},
        {'name': assessment.title, 'url': reverse('grades:assessment_detail', kwargs={'pk': assessment_pk})},
        {'name': 'Enter Grades', 'url': ''},
    ]

    context = {
        'assessment': assessment,
        'student_data': student_data,
        'max_score': assessment.max_score,
        'breadcrumbs': breadcrumbs,
    }

    if request.htmx:
        return render(request, 'grades/grade_entry.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('grades:grade_entry', kwargs={'assessment_pk': assessment_pk}),
        'active_sidebar_link': 'grades:assessment_list',
        'page_title': f'Enter Grades - {assessment.title}',
    })


@login_required
def toggle_publish_view(request, pk):
    """Toggle assessment publish status"""
    teacher = _get_teacher_for_user(request.user)
    assessment = get_object_or_404(Assessment, pk=pk)

    # Check permission
    if teacher and assessment.class_subject.teacher != teacher:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    assessment.is_published = not assessment.is_published
    assessment.save(update_fields=['is_published'])

    if request.htmx:
        return render(request, 'grades/partials/publish_toggle.html', {'assessment': assessment})

    return JsonResponse({'is_published': assessment.is_published})


# Admin views for assessment types and grade scales

@login_required
def assessment_type_list_view(request):
    """List assessment types (admin only)"""
    assessment_types = AssessmentType.objects.all().order_by('order', 'name')

    context = {
        'assessment_types': assessment_types,
    }

    if request.htmx:
        return render(request, 'grades/partials/assessment_type_list.html', context)

    return render(request, 'grades/assessment_type_list.html', context)


@login_required
def assessment_type_add_view(request):
    """Add new assessment type"""
    if request.method == 'POST':
        form = AssessmentTypeForm(request.POST)
        if form.is_valid():
            assessment_type = form.save()
            messages.success(request, f'Assessment type "{assessment_type.name}" created.')
            if request.htmx:
                response = render(request, 'grades/partials/assessment_type_row.html', {'type': assessment_type})
                response['HX-Trigger'] = 'assessmentTypeAdded'
                return response
            return redirect('grades:assessment_type_list')
    else:
        form = AssessmentTypeForm()

    context = {
        'form': form,
        'modal_title': 'Add Assessment Type',
    }

    return render(request, 'grades/partials/assessment_type_form_modal.html', context)


@login_required
def assessment_type_update_view(request, pk):
    """Update assessment type"""
    assessment_type = get_object_or_404(AssessmentType, pk=pk)

    if request.method == 'POST':
        form = AssessmentTypeForm(request.POST, instance=assessment_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Assessment type "{assessment_type.name}" updated.')
            if request.htmx:
                response = render(request, 'grades/partials/assessment_type_row.html', {'type': assessment_type})
                response['HX-Trigger'] = 'assessmentTypeUpdated'
                return response
            return redirect('grades:assessment_type_list')
    else:
        form = AssessmentTypeForm(instance=assessment_type)

    context = {
        'form': form,
        'assessment_type': assessment_type,
        'modal_title': f'Edit {assessment_type.name}',
    }

    return render(request, 'grades/partials/assessment_type_form_modal.html', context)


@login_required
def assessment_type_delete_view(request, pk):
    """Delete assessment type"""
    assessment_type = get_object_or_404(AssessmentType, pk=pk)

    if request.method == 'POST':
        name = assessment_type.name
        assessment_type.delete()
        messages.success(request, f'Assessment type "{name}" deleted.')
        if request.htmx:
            return render(request, 'grades/partials/assessment_type_deleted.html')
        return redirect('grades:assessment_type_list')

    context = {
        'assessment_type': assessment_type,
    }

    return render(request, 'grades/partials/assessment_type_delete_modal.html', context)


@login_required
def grade_scale_list_view(request):
    """List grade scales"""
    scales = GradeScale.objects.prefetch_related('levels').filter(is_active=True)

    context = {
        'scales': scales,
    }

    if request.htmx:
        return render(request, 'grades/partials/grade_scale_list.html', context)

    return render(request, 'grades/grade_scale_list.html', context)
