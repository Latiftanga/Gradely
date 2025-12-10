from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db import models
from django.http import HttpResponse
from django.contrib import messages
from .models import Student, Parent
from .forms import (
    StudentCreateForm, StudentUpdateForm, StudentBulkImportForm,
    ParentCreateForm, LinkExistingParentForm
)
from .imports import (
    generate_template_csv,
    generate_template_xlsx,
    validate_import_file,
    process_import_file,
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
)


@login_required
def student_list_view(request):
    """
    View to list all students with search and filter functionality.
    Handles HTMX requests for searching and filtering.
    """
    students = Student.objects.select_related('user', 'current_class').all()

    # Get stats for display
    total_count = students.count()
    active_count = students.filter(is_active=True).count()
    boarder_count = students.filter(residential_status='boarder').count()
    day_count = students.filter(residential_status='day').count()

    # Apply search query
    query = request.GET.get('q', '')
    if query:
        students = students.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(student_id__icontains=query) |
            models.Q(admission_number__icontains=query) |
            models.Q(user__email__icontains=query)
        )

    # Apply class filter
    class_filter = request.GET.get('class_filter', '')
    if class_filter:
        students = students.filter(current_class_id=class_filter)

    # Apply residential status filter
    residential_filter = request.GET.get('residential_filter', '')
    if residential_filter:
        students = students.filter(residential_status=residential_filter)

    # Apply status filter
    status_filter = request.GET.get('status_filter', '')
    if status_filter == 'active':
        students = students.filter(is_active=True)
    elif status_filter == 'inactive':
        students = students.filter(is_active=False)

    # Apply gender filter
    gender_filter = request.GET.get('gender_filter', '')
    if gender_filter:
        students = students.filter(gender=gender_filter)

    # Get available classes for the filter dropdown
    try:
        from academics.models import Class
        classes = Class.objects.filter(is_active=True).select_related('grade_level', 'programme')
    except ImportError:
        classes = []

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Students', 'url': ''},
    ]

    context = {
        'students': students,
        'breadcrumbs': breadcrumbs,
        'search_query': query,
        'class_filter': class_filter,
        'residential_filter': residential_filter,
        'status_filter': status_filter,
        'gender_filter': gender_filter,
        'classes': classes,
        # Stats
        'total_count': total_count,
        'active_count': active_count,
        'boarder_count': boarder_count,
        'day_count': day_count,
    }

    # If it's an HTMX request for just the table body (e.g., from search/filter)
    if request.htmx and request.htmx.target == 'student-table-body':
        return render(request, 'students/partials/student_table.html', context)

    # If it's an HTMX request for the full content of the main area (e.g., sidebar click)
    if request.htmx:
        return render(request, 'students/student_list.html', context)

    # If it's a non-HTMX request (e.g., direct URL access), render the dashboard base template
    # and tell it to load the student list partial.
    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('students:list'),
        'active_sidebar_link': 'students:list',
        'page_title': 'Students',
        'partial_context': context,
    })


@login_required
def student_detail_view(request, pk):
    """
    View to display a single student's details.
    """
    student = get_object_or_404(
        Student.objects.select_related('user', 'current_class').prefetch_related('parents'),
        pk=pk
    )

    # Fetch enrollment history
    try:
        from academics.models import ClassEnrollment
        enrollment_history = ClassEnrollment.objects.filter(
            student=student
        ).select_related(
            'class_instance__grade_level',
            'class_instance__programme',
            'academic_year',
            'promoted_from__class_instance',
            'promoted_from__academic_year'
        ).order_by('-academic_year__start_date')
    except ImportError:
        enrollment_history = []

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Students', 'url': reverse('students:list')},
        {'name': student.get_full_name(), 'url': ''},
    ]

    context = {
        'student': student,
        'breadcrumbs': breadcrumbs,
        'enrollment_history': enrollment_history,
    }

    if request.htmx:
        return render(request, 'students/partials/student_detail.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('students:detail', kwargs={'pk': pk}),
        'active_sidebar_link': 'students:list',
        'page_title': student.get_full_name(),
        'partial_context': context,
    })


@login_required
def student_add_view(request):
    """
    View to handle adding a new student.
    Renders a full-page form on GET and processes it on POST.
    """
    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Students', 'url': reverse('students:list')},
        {'name': 'Add New', 'url': ''},
    ]

    if request.method == 'POST':
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            form.save()
            # On success, redirect to the student list page
            return redirect(reverse('students:list'))
        # If form is invalid, it will fall through to render the form with errors
    else:
        form = StudentCreateForm()

    context = {
        'form': form,
        'breadcrumbs': breadcrumbs,
    }

    if request.htmx:
        return render(request, 'students/partials/student_form_content.html', context)

    return render(request, 'students/student_form.html', context)


@login_required
def student_update_view(request, pk):
    """
    View to handle updating an existing student.
    Renders a pre-filled form on GET and processes updates on POST.
    """
    student = get_object_or_404(Student, pk=pk)

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Students', 'url': reverse('students:list')},
        {'name': student.get_full_name(), 'url': reverse('students:detail', kwargs={'pk': student.pk})},
        {'name': 'Edit', 'url': ''},
    ]

    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            # On success, redirect to the student detail page
            return redirect(reverse('students:detail', kwargs={'pk': student.pk}))
        # If form is invalid, it will fall through to render the form with errors
    else:
        form = StudentUpdateForm(instance=student)

    context = {
        'form': form,
        'breadcrumbs': breadcrumbs,
        'student': student,
    }

    if request.htmx:
        return render(request, 'students/partials/student_form_content.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('students:update', kwargs={'pk': student.pk}),
        'active_sidebar_link': 'students:list',
        'page_title': f'Edit {student.get_full_name()}',
        'partial_context': context,
    })


@login_required
def student_delete_view(request, pk):
    """
    View to handle deleting a student.
    Displays a confirmation modal on GET and performs deletion on POST.
    """
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        student.user.delete()  # Deletes the associated User and cascades to Student

        # If HTMX request, return the student list
        if request.htmx:
            students = Student.objects.select_related('user', 'current_class').all()
            breadcrumbs = [
                {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
                {'name': 'Students', 'url': ''},
            ]
            return render(request, 'students/student_list.html', {
                'students': students,
                'breadcrumbs': breadcrumbs,
                'total_count': students.count(),
                'active_count': students.filter(is_active=True).count(),
                'boarder_count': students.filter(residential_status='boarder').count(),
                'day_count': students.filter(residential_status='day').count(),
            })
        return redirect(reverse('students:list'))

    context = {
        'student': student,
    }

    # Always return the modal partial for HTMX GET requests
    if request.htmx:
        return render(request, 'students/partials/student_confirm_delete.html', context)

    # For non-HTMX requests, redirect to the student list with a message
    return redirect(reverse('students:list'))


@login_required
def student_bulk_import_view(request):
    """
    View to handle bulk import of students from CSV/XLSX files.
    """
    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Students', 'url': reverse('students:list')},
        {'name': 'Bulk Import', 'url': ''},
    ]

    result = None
    preview_data = None
    validation_errors = None
    validation_stats = None

    if request.method == 'POST':
        form = StudentBulkImportForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data['file']
            create_user_accounts = form.cleaned_data['create_user_accounts']

            action = request.POST.get('action', 'validate')

            if action == 'validate':
                # Just validate and show preview
                file.seek(0)
                is_valid, errors, preview, total_rows, stats = validate_import_file(file)
                preview_data = preview
                validation_errors = errors if not is_valid else None
                validation_stats = stats

                if is_valid:
                    # Build message with email stats
                    msg = f'File validated successfully. {total_rows} records ready to import.'
                    if stats.get('without_email', 0) > 0:
                        msg += f" ({stats['with_email']} with email, {stats['without_email']} without)"

                    result = {
                        'status': 'validated',
                        'total_rows': total_rows,
                        'stats': stats,
                        'message': msg
                    }
                else:
                    result = {
                        'status': 'error',
                        'errors': errors,
                        'message': f'Validation failed with {len(errors)} error(s).'
                    }

            elif action == 'import':
                # Process the import
                file.seek(0)
                success_count, error_count, errors, stats = process_import_file(file, create_accounts=create_user_accounts)

                # Build detailed message
                msg_parts = [f'Successfully imported {success_count} student(s).']
                if stats.get('accounts_created', 0) > 0:
                    msg_parts.append(f"{stats['accounts_created']} with login accounts.")
                if stats.get('placeholders_created', 0) > 0:
                    msg_parts.append(f"{stats['placeholders_created']} without accounts (can be added later).")
                if error_count > 0:
                    msg_parts.append(f'{error_count} error(s) occurred.')

                result = {
                    'status': 'success' if error_count == 0 else 'partial',
                    'success_count': success_count,
                    'error_count': error_count,
                    'errors': errors,
                    'stats': stats,
                    'message': ' '.join(msg_parts)
                }

                # Clear session
                request.session.pop('import_file_content', None)
                request.session.pop('import_file_name', None)
                request.session.pop('import_password', None)
    else:
        form = StudentBulkImportForm()

    context = {
        'form': form,
        'breadcrumbs': breadcrumbs,
        'result': result,
        'preview_data': preview_data,
        'validation_errors': validation_errors,
        'validation_stats': validation_stats,
        'required_columns': REQUIRED_COLUMNS,
        'optional_columns': OPTIONAL_COLUMNS,
    }

    if request.htmx:
        return render(request, 'students/partials/bulk_import_content.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('students:bulk_import'),
        'active_sidebar_link': 'students:list',
        'page_title': 'Bulk Import Students',
        'partial_context': context,
    })


@login_required
def download_import_template(request, format='csv'):
    """
    Download a template file for bulk import.
    """
    if format == 'xlsx':
        content = generate_template_xlsx()
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = 'student_import_template.xlsx'
    else:
        content = generate_template_csv()
        content_type = 'text/csv'
        filename = 'student_import_template.csv'

    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def student_export_pdf_view(request, pk):
    """
    Render a print-friendly student profile page.
    Users can use browser's Print > Save as PDF functionality.
    """
    from django.db import connection
    from schools.models import School

    student = get_object_or_404(
        Student.objects.select_related('user', 'current_class').prefetch_related('parents'),
        pk=pk
    )

    # Get school info for header
    try:
        school = School.objects.get(schema_name=connection.schema_name)
    except School.DoesNotExist:
        school = None

    # Fetch enrollment history
    try:
        from academics.models import ClassEnrollment
        enrollment_history = ClassEnrollment.objects.filter(
            student=student
        ).select_related(
            'class_instance__grade_level',
            'class_instance__programme',
            'academic_year'
        ).order_by('-academic_year__start_date')
    except ImportError:
        enrollment_history = []

    context = {
        'student': student,
        'school': school,
        'enrollment_history': enrollment_history,
    }

    return render(request, 'students/pdf/student_profile.html', context)


@login_required
def add_parent_view(request, student_pk):
    """
    View to add a new parent and link to a student.
    Renders as a modal.
    """
    student = get_object_or_404(Student, pk=student_pk)

    if request.method == 'POST':
        form = ParentCreateForm(request.POST, student=student)
        if form.is_valid():
            parent = form.save()
            messages.success(request, f'Parent {parent.get_full_name()} added successfully.')

            # Return updated parents section for HTMX with modal close trigger
            if request.htmx:
                response = render(request, 'students/partials/parent_list.html', {
                    'student': student,
                })
                response['HX-Trigger'] = 'closeModal'
                return response

            return redirect('students:detail', pk=student_pk)
    else:
        form = ParentCreateForm(student=student)

    context = {
        'form': form,
        'student': student,
        'modal_title': f'Add Parent for {student.get_full_name()}',
    }

    return render(request, 'students/partials/parent_form_modal.html', context)


@login_required
def link_parent_view(request, student_pk):
    """
    View to link an existing parent to a student.
    Renders as a modal.
    """
    student = get_object_or_404(Student, pk=student_pk)

    # Get all parents not already linked to this student
    linked_parent_pks = student.parents.values_list('pk', flat=True)
    available_parents = Parent.objects.exclude(pk__in=linked_parent_pks)

    if request.method == 'POST':
        form = LinkExistingParentForm(request.POST, student=student)
        # Set queryset for validation
        form.fields['parent'].queryset = available_parents
        if form.is_valid():
            parent = form.save()
            messages.success(request, f'Parent {parent.get_full_name()} linked successfully.')

            # Return updated parents section for HTMX with modal close trigger
            if request.htmx:
                response = render(request, 'students/partials/parent_list.html', {
                    'student': student,
                })
                response['HX-Trigger'] = 'closeModal'
                return response

            return redirect('students:detail', pk=student_pk)
    else:
        form = LinkExistingParentForm(student=student)
        form.fields['parent'].queryset = available_parents

    context = {
        'form': form,
        'student': student,
        'modal_title': f'Link Existing Parent to {student.get_full_name()}',
        'is_link_form': True,
        'has_available_parents': available_parents.exists(),
    }

    return render(request, 'students/partials/parent_form_modal.html', context)


@login_required
def unlink_parent_view(request, student_pk, parent_pk):
    """
    View to unlink a parent from a student.
    """
    student = get_object_or_404(Student, pk=student_pk)
    parent = get_object_or_404(Parent, pk=parent_pk)

    if request.method == 'POST':
        parent.students.remove(student)
        messages.success(request, f'Parent {parent.get_full_name()} unlinked from student.')

        # Return updated parents section for HTMX with modal close trigger
        if request.htmx:
            response = render(request, 'students/partials/parent_list.html', {
                'student': student,
            })
            response['HX-Trigger'] = 'closeModal'
            return response

        return redirect('students:detail', pk=student_pk)

    # Show confirmation modal
    context = {
        'student': student,
        'parent': parent,
    }
    return render(request, 'students/partials/unlink_parent_modal.html', context)
