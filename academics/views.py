from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.urls import reverse

from .models import (
    Programme, GradeLevel, AcademicYear, Term, Class, Subject, ClassSubject,
    ClassEnrollment
)
from .forms import (
    ProgrammeForm, GradeLevelForm, AcademicYearForm, TermForm,
    ClassForm, SubjectForm, ClassSubjectForm, BulkClassSubjectForm,
    ClassEnrollmentForm, BulkEnrollmentForm
)


# ==================== Academic Year Views ====================

@login_required
def academic_year_list_view(request):
    """List all academic years"""
    years = AcademicYear.objects.annotate(
        term_count=Count('terms'),
        enrollment_count=Count('enrollments')
    )

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Academic Years', 'url': ''},
    ]

    context = {'years': years, 'breadcrumbs': breadcrumbs}

    if request.htmx:
        return render(request, 'academics/academic_year_list.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('academics:academic_years'),
        'active_sidebar_link': 'academics:academic_years',
        'page_title': 'Academic Years',
    })


@login_required
def academic_year_add_view(request):
    """Add a new academic year"""
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic year created successfully.')
            if request.htmx:
                years = AcademicYear.objects.annotate(
                    term_count=Count('terms'),
                    enrollment_count=Count('enrollments')
                )
                response = render(request, 'academics/partials/academic_year_list.html', {'years': years})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:academic_years')
    else:
        form = AcademicYearForm()

    context = {'form': form, 'modal_title': 'Add Academic Year'}
    if request.htmx:
        return render(request, 'academics/partials/academic_year_form_modal.html', context)
    return render(request, 'academics/academic_year_form.html', context)


@login_required
def academic_year_edit_view(request, pk):
    """Edit an academic year"""
    year = get_object_or_404(AcademicYear, pk=pk)

    if request.method == 'POST':
        form = AcademicYearForm(request.POST, instance=year)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic year updated successfully.')
            if request.htmx:
                years = AcademicYear.objects.annotate(
                    term_count=Count('terms'),
                    enrollment_count=Count('enrollments')
                )
                response = render(request, 'academics/partials/academic_year_list.html', {'years': years})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:academic_years')
    else:
        form = AcademicYearForm(instance=year)

    context = {'form': form, 'year': year, 'modal_title': 'Edit Academic Year'}
    if request.htmx:
        return render(request, 'academics/partials/academic_year_form_modal.html', context)
    return render(request, 'academics/academic_year_form.html', context)


@login_required
def academic_year_delete_view(request, pk):
    """Delete an academic year"""
    year = get_object_or_404(AcademicYear, pk=pk)

    if request.method == 'POST':
        year.delete()
        messages.success(request, 'Academic year deleted successfully.')
        if request.htmx:
            years = AcademicYear.objects.annotate(
                term_count=Count('terms'),
                class_count=Count('classes')
            )
            response = render(request, 'academics/partials/academic_year_list.html', {'years': years})
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('academics:academic_years')

    if request.htmx:
        return render(request, 'academics/partials/academic_year_delete_modal.html', {'year': year})
    return render(request, 'academics/academic_year_confirm_delete.html', {'year': year})


# ==================== Term Views ====================

@login_required
def term_add_view(request):
    """Add a new term"""
    if request.method == 'POST':
        form = TermForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Term created successfully.')
            if request.htmx:
                terms = Term.objects.select_related('academic_year').order_by('-academic_year__start_date', 'term_number')
                response = render(request, 'dashboard/partials/settings_terms.html', {'terms': terms})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('dashboard:settings')
    else:
        form = TermForm()

    context = {'form': form, 'modal_title': 'Add Term'}
    if request.htmx:
        return render(request, 'academics/partials/term_form_modal.html', context)
    return render(request, 'academics/term_form.html', context)


@login_required
def term_edit_view(request, pk):
    """Edit a term"""
    term = get_object_or_404(Term, pk=pk)

    if request.method == 'POST':
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            messages.success(request, 'Term updated successfully.')
            if request.htmx:
                terms = Term.objects.select_related('academic_year').order_by('-academic_year__start_date', 'term_number')
                response = render(request, 'dashboard/partials/settings_terms.html', {'terms': terms})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('dashboard:settings')
    else:
        form = TermForm(instance=term)

    context = {'form': form, 'term': term, 'modal_title': 'Edit Term'}
    if request.htmx:
        return render(request, 'academics/partials/term_form_modal.html', context)
    return render(request, 'academics/term_form.html', context)


@login_required
def term_delete_view(request, pk):
    """Delete a term"""
    term = get_object_or_404(Term, pk=pk)

    if request.method == 'POST':
        term.delete()
        messages.success(request, 'Term deleted successfully.')
        if request.htmx:
            terms = Term.objects.select_related('academic_year').order_by('-academic_year__start_date', 'term_number')
            response = render(request, 'dashboard/partials/settings_terms.html', {'terms': terms})
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('dashboard:settings')

    if request.htmx:
        return render(request, 'academics/partials/term_delete_modal.html', {'term': term})
    return render(request, 'academics/term_confirm_delete.html', {'term': term})


# ==================== Grade Level Views ====================

@login_required
def grade_level_list_view(request):
    """List all grade levels"""
    levels = GradeLevel.objects.annotate(class_count=Count('classes'))

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Grade Levels', 'url': ''},
    ]

    context = {'levels': levels, 'breadcrumbs': breadcrumbs}

    if request.htmx:
        return render(request, 'academics/grade_level_list.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('academics:grade_levels'),
        'active_sidebar_link': 'academics:grade_levels',
        'page_title': 'Grade Levels',
    })


@login_required
def grade_level_add_view(request):
    """Add a new grade level"""
    if request.method == 'POST':
        form = GradeLevelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade level created successfully.')
            if request.htmx:
                levels = GradeLevel.objects.annotate(class_count=Count('classes'))
                response = render(request, 'academics/partials/grade_level_list.html', {'levels': levels})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:grade_levels')
    else:
        form = GradeLevelForm()

    context = {'form': form, 'modal_title': 'Add Grade Level'}
    if request.htmx:
        return render(request, 'academics/partials/grade_level_form_modal.html', context)
    return render(request, 'academics/grade_level_form.html', context)


@login_required
def grade_level_edit_view(request, pk):
    """Edit a grade level"""
    level = get_object_or_404(GradeLevel, pk=pk)

    if request.method == 'POST':
        form = GradeLevelForm(request.POST, instance=level)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade level updated successfully.')
            if request.htmx:
                levels = GradeLevel.objects.annotate(class_count=Count('classes'))
                response = render(request, 'academics/partials/grade_level_list.html', {'levels': levels})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:grade_levels')
    else:
        form = GradeLevelForm(instance=level)

    context = {'form': form, 'level': level, 'modal_title': 'Edit Grade Level'}
    if request.htmx:
        return render(request, 'academics/partials/grade_level_form_modal.html', context)
    return render(request, 'academics/grade_level_form.html', context)


@login_required
def grade_level_delete_view(request, pk):
    """Delete a grade level"""
    level = get_object_or_404(GradeLevel, pk=pk)

    if request.method == 'POST':
        level.delete()
        messages.success(request, 'Grade level deleted successfully.')
        if request.htmx:
            levels = GradeLevel.objects.annotate(class_count=Count('classes'))
            response = render(request, 'academics/partials/grade_level_list.html', {'levels': levels})
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('academics:grade_levels')

    if request.htmx:
        return render(request, 'academics/partials/grade_level_delete_modal.html', {'level': level})
    return render(request, 'academics/grade_level_confirm_delete.html', {'level': level})


# ==================== Class Views ====================

def _get_filtered_classes(request):
    """Helper to get filtered classes queryset and context"""
    # Get the selected or current academic year for enrollment count
    academic_year_id = request.GET.get('academic_year')
    if academic_year_id:
        selected_year = AcademicYear.objects.filter(pk=academic_year_id).first()
    else:
        selected_year = AcademicYear.objects.filter(is_current=True).first()

    # Annotate with enrollment count for the selected/current year
    classes = Class.objects.select_related(
        'grade_level', 'programme', 'class_teacher'
    )

    if selected_year:
        classes = classes.annotate(
            student_count=Count(
                'enrollments',
                filter=Q(enrollments__academic_year=selected_year, enrollments__is_active=True)
            )
        )
    else:
        classes = classes.annotate(student_count=Count('enrollments'))

    # Filtering
    grade_level = request.GET.get('grade_level')
    status = request.GET.get('status')

    if grade_level:
        classes = classes.filter(grade_level_id=grade_level)
    if status == 'active':
        classes = classes.filter(is_active=True)
    elif status == 'inactive':
        classes = classes.filter(is_active=False)

    # Pagination
    paginator = Paginator(classes, 20)
    page = request.GET.get('page', 1)
    classes = paginator.get_page(page)

    return {
        'classes': classes,
        'academic_years': AcademicYear.objects.all(),
        'grade_levels': GradeLevel.objects.all(),
        'selected_year': selected_year,
        'selected_grade_level': grade_level or '',
        'selected_status': status or '',
    }


@login_required
def class_list_view(request):
    """List all classes with filtering"""
    context = _get_filtered_classes(request)

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Classes', 'url': ''},
    ]
    context['breadcrumbs'] = breadcrumbs

    if request.htmx:
        return render(request, 'academics/class_list.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('academics:classes'),
        'active_sidebar_link': 'academics:classes',
        'page_title': 'Classes',
    })


@login_required
def class_list_partial_view(request):
    """Return just the class list partial for filtering"""
    context = _get_filtered_classes(request)
    return render(request, 'academics/partials/class_list.html', context)


@login_required
def class_add_view(request):
    """Add a new class"""
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class created successfully.')
            if request.htmx:
                current_year = AcademicYear.objects.filter(is_current=True).first()
                classes = Class.objects.select_related(
                    'grade_level', 'programme', 'class_teacher'
                )
                if current_year:
                    classes = classes.annotate(
                        student_count=Count(
                            'enrollments',
                            filter=Q(enrollments__academic_year=current_year, enrollments__is_active=True)
                        )
                    )
                else:
                    classes = classes.annotate(student_count=Count('enrollments'))
                response = render(request, 'academics/partials/class_list.html', {
                    'classes': classes,
                    'academic_years': AcademicYear.objects.all(),
                    'grade_levels': GradeLevel.objects.all(),
                })
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:classes')
    else:
        form = ClassForm()

    context = {'form': form, 'modal_title': 'Add Class'}
    if request.htmx:
        return render(request, 'academics/partials/class_form_modal.html', context)
    return render(request, 'academics/class_form.html', context)


@login_required
def class_detail_view(request, pk):
    """View class details"""
    class_obj = get_object_or_404(
        Class.objects.select_related(
            'grade_level', 'programme', 'class_teacher'
        ).prefetch_related('class_subjects__subject', 'class_subjects__teacher'),
        pk=pk
    )

    # Get selected or current academic year
    academic_year_id = request.GET.get('academic_year')
    if academic_year_id:
        selected_year = AcademicYear.objects.filter(pk=academic_year_id).first()
    else:
        selected_year = AcademicYear.objects.filter(is_current=True).first()

    # Get enrolled students for the selected year
    enrollments = []
    if selected_year:
        enrollments = ClassEnrollment.objects.filter(
            class_instance=class_obj,
            academic_year=selected_year,
            is_active=True
        ).select_related('student')

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Classes', 'url': reverse('academics:classes')},
        {'name': str(class_obj), 'url': ''},
    ]

    context = {
        'class': class_obj,
        'enrollments': enrollments,
        'selected_year': selected_year,
        'academic_years': AcademicYear.objects.all(),
        'subjects': class_obj.class_subjects.filter(is_active=True),
        'breadcrumbs': breadcrumbs,
    }

    if request.htmx:
        return render(request, 'academics/class_detail.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('academics:class_detail', kwargs={'pk': pk}),
        'active_sidebar_link': 'academics:classes',
        'page_title': str(class_obj),
    })


@login_required
def class_edit_view(request, pk):
    """Edit a class"""
    class_obj = get_object_or_404(Class, pk=pk)

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class updated successfully.')
            if request.htmx:
                current_year = AcademicYear.objects.filter(is_current=True).first()
                classes = Class.objects.select_related(
                    'grade_level', 'programme', 'class_teacher'
                )
                if current_year:
                    classes = classes.annotate(
                        student_count=Count(
                            'enrollments',
                            filter=Q(enrollments__academic_year=current_year, enrollments__is_active=True)
                        )
                    )
                else:
                    classes = classes.annotate(student_count=Count('enrollments'))
                response = render(request, 'academics/partials/class_list.html', {
                    'classes': classes,
                    'academic_years': AcademicYear.objects.all(),
                    'grade_levels': GradeLevel.objects.all(),
                })
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:classes')
    else:
        form = ClassForm(instance=class_obj)

    context = {'form': form, 'class': class_obj, 'modal_title': 'Edit Class'}
    if request.htmx:
        return render(request, 'academics/partials/class_form_modal.html', context)
    return render(request, 'academics/class_form.html', context)


@login_required
def class_delete_view(request, pk):
    """Delete a class"""
    class_obj = get_object_or_404(Class, pk=pk)

    if request.method == 'POST':
        class_obj.delete()
        messages.success(request, 'Class deleted successfully.')
        if request.htmx:
            current_year = AcademicYear.objects.filter(is_current=True).first()
            classes = Class.objects.select_related(
                'grade_level', 'programme', 'class_teacher'
            )
            if current_year:
                classes = classes.annotate(
                    student_count=Count(
                        'enrollments',
                        filter=Q(enrollments__academic_year=current_year, enrollments__is_active=True)
                    )
                )
            else:
                classes = classes.annotate(student_count=Count('enrollments'))
            response = render(request, 'academics/partials/class_list.html', {
                'classes': classes,
                'academic_years': AcademicYear.objects.all(),
                'grade_levels': GradeLevel.objects.all(),
            })
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('academics:classes')

    if request.htmx:
        return render(request, 'academics/partials/class_delete_modal.html', {'class': class_obj})
    return render(request, 'academics/class_confirm_delete.html', {'class': class_obj})


# ==================== Subject Views ====================

def _get_filtered_subjects(request):
    """Helper to get filtered subjects queryset and context"""
    subjects = Subject.objects.annotate(
        class_count=Count('class_assignments')
    )

    # Filtering
    subject_type = request.GET.get('type')
    status = request.GET.get('status')

    if subject_type:
        subjects = subjects.filter(subject_type=subject_type)
    if status == 'active':
        subjects = subjects.filter(is_active=True)
    elif status == 'inactive':
        subjects = subjects.filter(is_active=False)

    return {
        'subjects': subjects,
        'selected_type': subject_type or '',
        'selected_status': status or '',
    }


@login_required
def subject_list_view(request):
    """List all subjects"""
    context = _get_filtered_subjects(request)

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Subjects', 'url': ''},
    ]
    context['breadcrumbs'] = breadcrumbs

    if request.htmx:
        return render(request, 'academics/subject_list.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('academics:subjects'),
        'active_sidebar_link': 'academics:subjects',
        'page_title': 'Subjects',
    })


@login_required
def subject_list_partial_view(request):
    """Return just the subject list partial for filtering"""
    context = _get_filtered_subjects(request)
    return render(request, 'academics/partials/subject_list.html', context)


@login_required
def subject_add_view(request):
    """Add a new subject"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject created successfully.')
            if request.htmx:
                subjects = Subject.objects.annotate(class_count=Count('class_assignments'))
                response = render(request, 'academics/partials/subject_list.html', {'subjects': subjects})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:subjects')
    else:
        form = SubjectForm()

    context = {'form': form, 'modal_title': 'Add Subject'}
    if request.htmx:
        return render(request, 'academics/partials/subject_form_modal.html', context)
    return render(request, 'academics/subject_form.html', context)


@login_required
def subject_detail_view(request, pk):
    """View subject details"""
    subject = get_object_or_404(
        Subject.objects.prefetch_related(
            'class_assignments__class_instance',
            'class_assignments__teacher',
            'applicable_levels',
            'programmes'
        ),
        pk=pk
    )

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Subjects', 'url': reverse('academics:subjects')},
        {'name': subject.name, 'url': ''},
    ]

    context = {
        'subject': subject,
        'assignments': subject.class_assignments.filter(is_active=True),
        'breadcrumbs': breadcrumbs,
    }

    if request.htmx:
        return render(request, 'academics/subject_detail.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('academics:subject_detail', kwargs={'pk': pk}),
        'active_sidebar_link': 'academics:subjects',
        'page_title': subject.name,
    })


@login_required
def subject_edit_view(request, pk):
    """Edit a subject"""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully.')
            if request.htmx:
                subjects = Subject.objects.annotate(class_count=Count('class_assignments'))
                response = render(request, 'academics/partials/subject_list.html', {'subjects': subjects})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:subjects')
    else:
        form = SubjectForm(instance=subject)

    context = {'form': form, 'subject': subject, 'modal_title': 'Edit Subject'}
    if request.htmx:
        return render(request, 'academics/partials/subject_form_modal.html', context)
    return render(request, 'academics/subject_form.html', context)


@login_required
def subject_delete_view(request, pk):
    """Delete a subject"""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully.')
        if request.htmx:
            subjects = Subject.objects.annotate(class_count=Count('class_assignments'))
            response = render(request, 'academics/partials/subject_list.html', {'subjects': subjects})
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('academics:subjects')

    if request.htmx:
        return render(request, 'academics/partials/subject_delete_modal.html', {'subject': subject})
    return render(request, 'academics/subject_confirm_delete.html', {'subject': subject})


# ==================== Class Subject Assignment Views ====================

@login_required
def class_subject_add_view(request, class_pk):
    """Add a subject to a class"""
    class_obj = get_object_or_404(Class, pk=class_pk)

    if request.method == 'POST':
        form = ClassSubjectForm(request.POST)
        if form.is_valid():
            class_subject = form.save(commit=False)
            class_subject.class_instance = class_obj
            class_subject.save()
            messages.success(request, 'Subject added to class successfully.')
            if request.htmx:
                context = {
                    'class': class_obj,
                    'subjects': class_obj.class_subjects.filter(is_active=True),
                }
                response = render(request, 'academics/partials/class_subjects_section.html', context)
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:class_detail', pk=class_pk)
    else:
        form = ClassSubjectForm(initial={'class_instance': class_obj})
        # Exclude already assigned subjects
        assigned_subjects = class_obj.class_subjects.values_list('subject_id', flat=True)
        form.fields['subject'].queryset = Subject.objects.filter(
            is_active=True
        ).exclude(pk__in=assigned_subjects)
        form.fields['class_instance'].widget = form.fields['class_instance'].hidden_widget()

    context = {
        'form': form,
        'class': class_obj,
        'modal_title': f'Add Subject to {class_obj}'
    }

    if request.htmx:
        return render(request, 'academics/partials/class_subject_form_modal.html', context)
    return render(request, 'academics/class_subject_form.html', context)


@login_required
def class_subject_edit_view(request, class_pk, pk):
    """Edit a class subject assignment"""
    class_obj = get_object_or_404(Class, pk=class_pk)
    class_subject = get_object_or_404(ClassSubject, pk=pk, class_instance=class_obj)

    if request.method == 'POST':
        form = ClassSubjectForm(request.POST, instance=class_subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject assignment updated successfully.')
            if request.htmx:
                context = {
                    'class': class_obj,
                    'subjects': class_obj.class_subjects.filter(is_active=True),
                }
                response = render(request, 'academics/partials/class_subjects_section.html', context)
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:class_detail', pk=class_pk)
    else:
        form = ClassSubjectForm(instance=class_subject)
        form.fields['class_instance'].widget = form.fields['class_instance'].hidden_widget()

    context = {
        'form': form,
        'class': class_obj,
        'class_subject': class_subject,
        'modal_title': f'Edit {class_subject.subject.name}'
    }

    if request.htmx:
        return render(request, 'academics/partials/class_subject_form_modal.html', context)
    return render(request, 'academics/class_subject_form.html', context)


@login_required
def class_subject_remove_view(request, class_pk, pk):
    """Remove a subject from a class"""
    class_obj = get_object_or_404(Class, pk=class_pk)
    class_subject = get_object_or_404(ClassSubject, pk=pk, class_instance=class_obj)

    if request.method == 'POST':
        class_subject.delete()
        messages.success(request, 'Subject removed from class.')
        if request.htmx:
            context = {
                'class': class_obj,
                'subjects': class_obj.class_subjects.filter(is_active=True),
            }
            response = render(request, 'academics/partials/class_subjects_section.html', context)
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('academics:class_detail', pk=class_pk)

    if request.htmx:
        return render(request, 'academics/partials/class_subject_remove_modal.html', {
            'class': class_obj,
            'class_subject': class_subject
        })
    return render(request, 'academics/class_subject_confirm_remove.html', {
        'class': class_obj,
        'class_subject': class_subject
    })


# ==================== Programme Views ====================

@login_required
def programme_list_view(request):
    """List all programmes"""
    programmes = Programme.objects.annotate(
        class_count=Count('classes'),
        subject_count=Count('subjects')
    )

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Programmes', 'url': ''},
    ]

    context = {'programmes': programmes, 'breadcrumbs': breadcrumbs}

    if request.htmx:
        return render(request, 'academics/programme_list.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('academics:programmes'),
        'active_sidebar_link': 'academics:programmes',
        'page_title': 'Programmes',
    })


@login_required
def programme_add_view(request):
    """Add a new programme"""
    if request.method == 'POST':
        form = ProgrammeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Programme created successfully.')
            if request.htmx:
                programmes = Programme.objects.annotate(
                    class_count=Count('classes'),
                    subject_count=Count('subjects')
                )
                response = render(request, 'academics/partials/programme_list.html', {'programmes': programmes})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:programmes')
    else:
        form = ProgrammeForm()

    context = {'form': form, 'modal_title': 'Add Programme'}
    if request.htmx:
        return render(request, 'academics/partials/programme_form_modal.html', context)
    return render(request, 'academics/programme_form.html', context)


@login_required
def programme_edit_view(request, pk):
    """Edit a programme"""
    programme = get_object_or_404(Programme, pk=pk)

    if request.method == 'POST':
        form = ProgrammeForm(request.POST, instance=programme)
        if form.is_valid():
            form.save()
            messages.success(request, 'Programme updated successfully.')
            if request.htmx:
                programmes = Programme.objects.annotate(
                    class_count=Count('classes'),
                    subject_count=Count('subjects')
                )
                response = render(request, 'academics/partials/programme_list.html', {'programmes': programmes})
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:programmes')
    else:
        form = ProgrammeForm(instance=programme)

    context = {'form': form, 'programme': programme, 'modal_title': 'Edit Programme'}
    if request.htmx:
        return render(request, 'academics/partials/programme_form_modal.html', context)
    return render(request, 'academics/programme_form.html', context)


@login_required
def programme_delete_view(request, pk):
    """Delete a programme"""
    programme = get_object_or_404(Programme, pk=pk)

    if request.method == 'POST':
        programme.delete()
        messages.success(request, 'Programme deleted successfully.')
        if request.htmx:
            programmes = Programme.objects.annotate(
                class_count=Count('classes'),
                subject_count=Count('subjects')
            )
            response = render(request, 'academics/partials/programme_list.html', {'programmes': programmes})
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('academics:programmes')

    if request.htmx:
        return render(request, 'academics/partials/programme_delete_modal.html', {'programme': programme})
    return render(request, 'academics/programme_confirm_delete.html', {'programme': programme})


# ==================== Class Enrollment Views ====================

@login_required
def class_enrollment_add_view(request, class_pk):
    """Enroll a student in a class"""
    from students.models import Student

    class_obj = get_object_or_404(Class, pk=class_pk)

    # Get current or selected academic year
    academic_year_id = request.GET.get('academic_year') or request.POST.get('academic_year')
    if academic_year_id:
        selected_year = AcademicYear.objects.filter(pk=academic_year_id).first()
    else:
        selected_year = AcademicYear.objects.filter(is_current=True).first()

    if request.method == 'POST':
        form = ClassEnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.class_instance = class_obj
            enrollment.save()
            messages.success(request, f'{enrollment.student} enrolled successfully.')
            if request.htmx:
                enrollments = ClassEnrollment.objects.filter(
                    class_instance=class_obj,
                    academic_year=enrollment.academic_year,
                    is_active=True
                ).select_related('student')
                subjects = class_obj.class_subjects.filter(is_active=True)
                context = {
                    'class': class_obj,
                    'enrollments': enrollments,
                    'selected_year': enrollment.academic_year,
                    'academic_years': AcademicYear.objects.all(),
                    'subjects': subjects,
                }
                # Render both sections - students and stats (OOB swap)
                students_html = render(request, 'academics/partials/class_students_section.html', context).content.decode()
                stats_html = render(request, 'academics/partials/class_stats_section.html', context).content.decode()
                # Add hx-swap-oob to stats section
                stats_html = stats_html.replace('id="class-stats-section"', 'id="class-stats-section" hx-swap-oob="true"')
                combined_html = students_html + stats_html
                response = HttpResponse(combined_html)
                response['HX-Trigger'] = 'closeModal'
                return response
            return redirect('academics:class_detail', pk=class_pk)
    else:
        initial = {'academic_year': selected_year, 'class_instance': class_obj}
        form = ClassEnrollmentForm(initial=initial)
        # Exclude already enrolled students for this year
        if selected_year:
            enrolled_students = ClassEnrollment.objects.filter(
                academic_year=selected_year,
                is_active=True
            ).values_list('student_id', flat=True)
            form.fields['student'].queryset = Student.objects.filter(
                is_active=True
            ).exclude(pk__in=enrolled_students)
        else:
            form.fields['student'].queryset = Student.objects.filter(is_active=True)
        form.fields['class_instance'].widget = form.fields['class_instance'].hidden_widget()

    context = {
        'form': form,
        'class': class_obj,
        'selected_year': selected_year,
        'modal_title': f'Enroll Student in {class_obj}'
    }

    if request.htmx:
        return render(request, 'academics/partials/class_enrollment_form_modal.html', context)
    return render(request, 'academics/class_enrollment_form.html', context)


@login_required
def class_enrollment_remove_view(request, class_pk, pk):
    """Remove a student enrollment from a class"""
    class_obj = get_object_or_404(Class, pk=class_pk)
    enrollment = get_object_or_404(ClassEnrollment, pk=pk, class_instance=class_obj)

    if request.method == 'POST':
        student_name = str(enrollment.student)
        academic_year = enrollment.academic_year
        enrollment.delete()
        messages.success(request, f'{student_name} removed from class.')
        if request.htmx:
            enrollments = ClassEnrollment.objects.filter(
                class_instance=class_obj,
                academic_year=academic_year,
                is_active=True
            ).select_related('student')
            subjects = class_obj.class_subjects.filter(is_active=True)
            context = {
                'class': class_obj,
                'enrollments': enrollments,
                'selected_year': academic_year,
                'academic_years': AcademicYear.objects.all(),
                'subjects': subjects,
            }
            # Render both sections - students and stats (OOB swap)
            students_html = render(request, 'academics/partials/class_students_section.html', context).content.decode()
            stats_html = render(request, 'academics/partials/class_stats_section.html', context).content.decode()
            # Add hx-swap-oob to stats section
            stats_html = stats_html.replace('id="class-stats-section"', 'id="class-stats-section" hx-swap-oob="true"')
            combined_html = students_html + stats_html
            response = HttpResponse(combined_html)
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('academics:class_detail', pk=class_pk)

    if request.htmx:
        return render(request, 'academics/partials/class_enrollment_remove_modal.html', {
            'class': class_obj,
            'enrollment': enrollment
        })
    return render(request, 'academics/class_enrollment_confirm_remove.html', {
        'class': class_obj,
        'enrollment': enrollment
    })


@login_required
def bulk_enrollment_view(request, class_pk):
    """Bulk enroll students in a class"""
    from students.models import Student

    class_obj = get_object_or_404(Class, pk=class_pk)

    # Get current or selected academic year
    academic_year_id = request.GET.get('academic_year')
    if academic_year_id:
        selected_year = AcademicYear.objects.filter(pk=academic_year_id).first()
    else:
        selected_year = AcademicYear.objects.filter(is_current=True).first()

    if request.method == 'POST':
        academic_year = get_object_or_404(AcademicYear, pk=request.POST.get('academic_year'))
        student_ids = request.POST.getlist('students')

        created_count = 0
        for student_id in student_ids:
            student = Student.objects.filter(pk=student_id, is_active=True).first()
            if student:
                enrollment, created = ClassEnrollment.objects.get_or_create(
                    student=student,
                    academic_year=academic_year,
                    defaults={
                        'class_instance': class_obj,
                        'is_active': True
                    }
                )
                if created:
                    created_count += 1

        messages.success(request, f'{created_count} student(s) enrolled successfully.')
        if request.htmx:
            enrollments = ClassEnrollment.objects.filter(
                class_instance=class_obj,
                academic_year=academic_year,
                is_active=True
            ).select_related('student')
            subjects = class_obj.class_subjects.filter(is_active=True)
            context = {
                'class': class_obj,
                'enrollments': enrollments,
                'selected_year': academic_year,
                'academic_years': AcademicYear.objects.all(),
                'subjects': subjects,
            }
            # Render both sections - students and stats (OOB swap)
            students_html = render(request, 'academics/partials/class_students_section.html', context).content.decode()
            stats_html = render(request, 'academics/partials/class_stats_section.html', context).content.decode()
            # Add hx-swap-oob to stats section
            stats_html = stats_html.replace('id="class-stats-section"', 'id="class-stats-section" hx-swap-oob="true"')
            combined_html = students_html + stats_html
            response = HttpResponse(combined_html)
            response['HX-Trigger'] = 'closeModal'
            return response
        return redirect('academics:class_detail', pk=class_pk)

    # Get students not enrolled in this academic year
    enrolled_students = []
    if selected_year:
        enrolled_students = ClassEnrollment.objects.filter(
            academic_year=selected_year,
            is_active=True
        ).values_list('student_id', flat=True)

    available_students = Student.objects.filter(
        is_active=True
    ).exclude(pk__in=enrolled_students).order_by('last_name', 'first_name')

    context = {
        'class': class_obj,
        'selected_year': selected_year,
        'academic_years': AcademicYear.objects.filter(is_active=True),
        'students': available_students,
        'modal_title': f'Bulk Enroll Students in {class_obj}'
    }

    if request.htmx:
        return render(request, 'academics/partials/bulk_enrollment_modal.html', context)
    return render(request, 'academics/bulk_enrollment.html', context)


# ============================================================================
# Promotion/Demotion Views
# ============================================================================

@login_required
def promotion_view(request):
    """
    Main promotion view - wizard to promote/demote students between classes.
    Step 1: Select source and target class/year
    Step 2: Select students to promote
    Step 3: Execute promotion
    """
    from .forms import PromotionForm

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Classes', 'url': reverse('academics:classes')},
        {'name': 'Student Promotion', 'url': ''},
    ]

    # Get initial values from query params (for auto-suggest)
    initial = {}
    if request.GET.get('source_year'):
        initial['source_academic_year'] = request.GET.get('source_year')
    if request.GET.get('source_class'):
        initial['source_class'] = request.GET.get('source_class')

    form = PromotionForm(initial=initial)

    context = {
        'form': form,
        'breadcrumbs': breadcrumbs,
        'step': 'setup',
    }

    if request.htmx:
        return render(request, 'academics/promotion.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('academics:promotion'),
        'active_sidebar_link': 'academics:classes',
        'page_title': 'Student Promotion',
    })


@login_required
def promotion_preview_view(request):
    """
    Preview students to be promoted - shows list with checkboxes.
    """
    from .forms import PromotionForm
    from students.models import Student

    if request.method != 'POST':
        return redirect('academics:promotion')

    form = PromotionForm(request.POST)
    if not form.is_valid():
        context = {
            'form': form,
            'step': 'setup',
            'errors': form.errors,
        }
        return render(request, 'academics/partials/promotion_form.html', context)

    source_year = form.cleaned_data['source_academic_year']
    source_class = form.cleaned_data['source_class']
    target_year = form.cleaned_data.get('target_academic_year')
    target_class = form.cleaned_data.get('target_class')
    promotion_type = form.cleaned_data['promotion_type']

    # Get students enrolled in source class for source year
    enrollments = ClassEnrollment.objects.filter(
        class_instance=source_class,
        academic_year=source_year,
        is_active=True
    ).select_related('student__user').order_by('student__last_name', 'student__first_name')

    # For graduation, check if students are already graduated
    # For other actions, check if already enrolled in target year
    if promotion_type == 'graduate':
        already_processed = set(Student.objects.filter(
            status='graduated'
        ).values_list('pk', flat=True))
    else:
        already_processed = set(ClassEnrollment.objects.filter(
            academic_year=target_year,
            is_active=True
        ).values_list('student_id', flat=True)) if target_year else set()

    students_data = []
    for enrollment in enrollments:
        student = enrollment.student
        is_already_processed = student.pk in already_processed
        students_data.append({
            'enrollment': enrollment,
            'student': student,
            'is_already_enrolled': is_already_processed,
            'can_promote': not is_already_processed and student.status == 'active',
        })

    promotable_count = sum(1 for s in students_data if s['can_promote'])
    already_enrolled_count = sum(1 for s in students_data if s['is_already_enrolled'])

    # Check if source class is final level (for graduation hint)
    is_final_level = source_class.grade_level.is_final_level if source_class else False

    context = {
        'form': form,
        'source_year': source_year,
        'source_class': source_class,
        'target_year': target_year,
        'target_class': target_class,
        'promotion_type': promotion_type,
        'promotion_type_display': dict(PromotionForm.PROMOTION_TYPE_CHOICES).get(promotion_type),
        'students_data': students_data,
        'promotable_count': promotable_count,
        'already_enrolled_count': already_enrolled_count,
        'total_count': len(students_data),
        'is_final_level': is_final_level,
        'is_graduation': promotion_type == 'graduate',
        'step': 'preview',
    }

    return render(request, 'academics/partials/promotion_preview.html', context)


@login_required
def promotion_execute_view(request):
    """
    Execute the promotion - create new enrollments in target class or graduate students.
    """
    from .forms import PromotionForm
    from students.models import Student
    from django.utils import timezone

    if request.method != 'POST':
        return redirect('academics:promotion')

    # Get form data
    source_year_id = request.POST.get('source_academic_year')
    source_class_id = request.POST.get('source_class')
    target_year_id = request.POST.get('target_academic_year')
    target_class_id = request.POST.get('target_class')
    promotion_type = request.POST.get('promotion_type')
    student_ids = request.POST.getlist('students')

    if not student_ids:
        messages.error(request, 'No students selected for promotion.')
        return redirect('academics:promotion')

    # Get objects
    source_year = get_object_or_404(AcademicYear, pk=source_year_id)
    source_class = get_object_or_404(Class, pk=source_class_id)

    # For graduation, target class/year are optional
    target_year = None
    target_class = None
    if promotion_type != 'graduate':
        target_year = get_object_or_404(AcademicYear, pk=target_year_id)
        target_class = get_object_or_404(Class, pk=target_class_id)

    # Process promotions/graduations
    promoted_count = 0
    graduated_count = 0
    skipped_count = 0
    errors = []

    for student_id in student_ids:
        try:
            # Get source enrollment
            source_enrollment = ClassEnrollment.objects.get(
                student_id=student_id,
                class_instance=source_class,
                academic_year=source_year,
                is_active=True
            )

            if promotion_type == 'graduate':
                # Graduate the student
                student = Student.objects.get(pk=student_id)
                if student.status == 'graduated':
                    skipped_count += 1
                    continue

                student.status = 'graduated'
                student.is_active = False
                student.graduation_date = timezone.now().date()
                student.graduation_year = source_year
                student.current_class = None
                student.save()

                # Mark enrollment as inactive
                source_enrollment.is_active = False
                source_enrollment.notes = f"Graduated from {source_class} ({source_year.name})"
                source_enrollment.save()

                graduated_count += 1
            else:
                # Regular promotion/transfer/repeat
                # Check if already enrolled in target year
                existing = ClassEnrollment.objects.filter(
                    student_id=student_id,
                    academic_year=target_year
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                # Create new enrollment
                new_enrollment = ClassEnrollment.objects.create(
                    student_id=student_id,
                    class_instance=target_class,
                    academic_year=target_year,
                    is_active=True,
                    promoted_from=source_enrollment,
                    notes=f"{promotion_type.title()} from {source_class} ({source_year.name})"
                )

                promoted_count += 1

        except ClassEnrollment.DoesNotExist:
            errors.append(f"Student {student_id} not found in source class")
        except Student.DoesNotExist:
            errors.append(f"Student {student_id} not found")
        except Exception as e:
            errors.append(f"Error processing student {student_id}: {str(e)}")

    # Build result message
    promotion_type_display = dict(PromotionForm.PROMOTION_TYPE_CHOICES).get(promotion_type, promotion_type)

    if promotion_type == 'graduate':
        if graduated_count > 0:
            messages.success(
                request,
                f'Successfully graduated {graduated_count} student(s) from {source_class} ({source_year.name}).'
            )
    else:
        if promoted_count > 0:
            messages.success(
                request,
                f'Successfully processed {promoted_count} student(s). '
                f'Action: {promotion_type_display} to {target_class} ({target_year.name}).'
            )

    if skipped_count > 0:
        if promotion_type == 'graduate':
            messages.warning(request, f'{skipped_count} student(s) skipped (already graduated).')
        else:
            messages.warning(request, f'{skipped_count} student(s) skipped (already enrolled in {target_year.name}).')

    if errors:
        messages.error(request, f'{len(errors)} error(s) occurred during processing.')

    context = {
        'promoted_count': promoted_count,
        'graduated_count': graduated_count,
        'skipped_count': skipped_count,
        'errors': errors,
        'source_class': source_class,
        'source_year': source_year,
        'target_class': target_class,
        'target_year': target_year,
        'promotion_type': promotion_type,
        'promotion_type_display': promotion_type_display,
        'is_graduation': promotion_type == 'graduate',
    }

    if request.htmx:
        return render(request, 'academics/partials/promotion_result.html', context)

    return redirect('academics:promotion')


@login_required
def get_class_students_json(request, class_pk):
    """
    API endpoint to get students in a class for a given academic year.
    Used for dynamic form updates.
    """
    from django.http import JsonResponse

    academic_year_id = request.GET.get('academic_year')
    if not academic_year_id:
        return JsonResponse({'students': [], 'count': 0})

    class_obj = get_object_or_404(Class, pk=class_pk)

    enrollments = ClassEnrollment.objects.filter(
        class_instance=class_obj,
        academic_year_id=academic_year_id,
        is_active=True
    ).select_related('student').order_by('student__last_name', 'student__first_name')

    students = [
        {
            'id': e.student.pk,
            'name': e.student.get_full_name(),
            'student_id': e.student.student_id,
            'gender': e.student.gender,
        }
        for e in enrollments
    ]

    return JsonResponse({'students': students, 'count': len(students)})


@login_required
def get_suggested_target_class(request):
    """
    API endpoint to suggest target class based on source class (next grade level).
    """
    from django.http import JsonResponse

    source_class_id = request.GET.get('source_class')
    if not source_class_id:
        return JsonResponse({'suggested_class': None})

    source_class = Class.objects.filter(pk=source_class_id).select_related('grade_level', 'programme').first()
    if not source_class:
        return JsonResponse({'suggested_class': None})

    # Find next grade level
    current_order = source_class.grade_level.order
    next_grade_level = GradeLevel.objects.filter(
        order=current_order + 1,
        is_active=True
    ).first()

    if not next_grade_level:
        return JsonResponse({'suggested_class': None, 'message': 'No next grade level found'})

    # Find class with same section/programme in next grade level
    suggested_class = Class.objects.filter(
        grade_level=next_grade_level,
        section=source_class.section,
        programme=source_class.programme,
        is_active=True
    ).first()

    # If no exact match, try without section
    if not suggested_class:
        suggested_class = Class.objects.filter(
            grade_level=next_grade_level,
            programme=source_class.programme,
            is_active=True
        ).first()

    # If still no match, just get any class in next grade level
    if not suggested_class:
        suggested_class = Class.objects.filter(
            grade_level=next_grade_level,
            is_active=True
        ).first()

    if suggested_class:
        return JsonResponse({
            'suggested_class': {
                'id': suggested_class.pk,
                'name': str(suggested_class),
            }
        })

    return JsonResponse({'suggested_class': None})
