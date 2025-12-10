from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count, Q
from django.contrib import messages
from django.http import HttpResponse

from .models import Teacher
from .forms import TeacherCreateForm, TeacherUpdateForm, TeacherBulkImportForm
from .imports import (
    validate_import_file, process_import_file,
    generate_template_csv, generate_template_xlsx,
    REQUIRED_COLUMNS, OPTIONAL_COLUMNS
)


def _get_filtered_teachers(request):
    """Helper to get filtered teachers queryset and context"""
    teachers = Teacher.objects.select_related('user').annotate(
        class_count=Count('managed_classes', filter=Q(managed_classes__is_active=True)),
        subject_count=Count('subject_assignments', filter=Q(subject_assignments__is_active=True))
    )

    # Filtering
    employment_status = request.GET.get('employment_status')
    qualification = request.GET.get('qualification')
    status = request.GET.get('status')
    search = request.GET.get('q', '').strip()

    if employment_status:
        teachers = teachers.filter(employment_status=employment_status)
    if qualification:
        teachers = teachers.filter(qualification=qualification)
    if status == 'active':
        teachers = teachers.filter(is_active=True)
    elif status == 'inactive':
        teachers = teachers.filter(is_active=False)
    if search:
        teachers = teachers.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(staff_id__icontains=search) |
            Q(specialization__icontains=search)
        )

    # Get counts for stats
    total_count = Teacher.objects.count()
    active_count = Teacher.objects.filter(is_active=True).count()
    full_time_count = Teacher.objects.filter(employment_status='full_time', is_active=True).count()
    part_time_count = Teacher.objects.filter(employment_status='part_time', is_active=True).count()

    return {
        'teachers': teachers,
        'total_count': total_count,
        'active_count': active_count,
        'full_time_count': full_time_count,
        'part_time_count': part_time_count,
        'selected_employment_status': employment_status or '',
        'selected_qualification': qualification or '',
        'selected_status': status or '',
        'search_query': search,
        'employment_status_choices': Teacher.EMPLOYMENT_STATUS_CHOICES,
        'qualification_choices': Teacher.QUALIFICATION_CHOICES,
    }


@login_required
def teacher_list_view(request):
    """List all teachers with filtering"""
    context = _get_filtered_teachers(request)

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Teachers', 'url': ''},
    ]
    context['breadcrumbs'] = breadcrumbs

    if request.htmx:
        return render(request, 'teachers/teacher_list.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('teachers:list'),
        'active_sidebar_link': 'teachers:list',
        'page_title': 'Teachers',
    })


@login_required
def teacher_list_partial_view(request):
    """Return just the teacher list partial for filtering"""
    context = _get_filtered_teachers(request)
    return render(request, 'teachers/partials/teacher_table.html', context)


@login_required
def teacher_add_view(request):
    """Add a new teacher"""
    if request.method == 'POST':
        form = TeacherCreateForm(request.POST)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f'Teacher {teacher.get_full_name()} created successfully.')
            if request.htmx:
                response = render(request, 'teachers/partials/teacher_add_success.html', {'teacher': teacher})
                response['HX-Trigger'] = 'teacherAdded'
                return response
            return redirect('teachers:detail', pk=teacher.pk)
    else:
        form = TeacherCreateForm()

    context = {
        'form': form,
        'modal_title': 'Add New Teacher',
    }

    if request.htmx:
        return render(request, 'teachers/partials/teacher_form_modal.html', context)

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Teachers', 'url': reverse('teachers:list')},
        {'name': 'Add Teacher', 'url': ''},
    ]
    context['breadcrumbs'] = breadcrumbs
    return render(request, 'teachers/teacher_form.html', context)


@login_required
def teacher_detail_view(request, pk):
    """View teacher details"""
    teacher = get_object_or_404(
        Teacher.objects.select_related('user').prefetch_related(
            'managed_classes__grade_level',
            'subject_assignments__subject',
            'subject_assignments__class_instance__grade_level'
        ),
        pk=pk
    )

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Teachers', 'url': reverse('teachers:list')},
        {'name': teacher.get_full_name(), 'url': ''},
    ]

    context = {
        'teacher': teacher,
        'breadcrumbs': breadcrumbs,
    }

    if request.htmx:
        return render(request, 'teachers/teacher_detail.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('teachers:detail', kwargs={'pk': pk}),
        'active_sidebar_link': 'teachers:list',
        'page_title': f'Teacher - {teacher.get_full_name()}',
    })


@login_required
def teacher_update_view(request, pk):
    """Update teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == 'POST':
        form = TeacherUpdateForm(request.POST, instance=teacher)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f'Teacher {teacher.get_full_name()} updated successfully.')
            if request.htmx:
                response = render(request, 'teachers/partials/teacher_update_success.html', {'teacher': teacher})
                response['HX-Trigger'] = 'teacherUpdated'
                return response
            return redirect('teachers:detail', pk=teacher.pk)
    else:
        form = TeacherUpdateForm(instance=teacher)

    context = {
        'form': form,
        'teacher': teacher,
        'modal_title': f'Edit {teacher.get_full_name()}',
    }

    if request.htmx:
        return render(request, 'teachers/partials/teacher_form_modal.html', context)

    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Teachers', 'url': reverse('teachers:list')},
        {'name': teacher.get_full_name(), 'url': reverse('teachers:detail', kwargs={'pk': pk})},
        {'name': 'Edit', 'url': ''},
    ]
    context['breadcrumbs'] = breadcrumbs
    return render(request, 'teachers/teacher_form.html', context)


@login_required
def teacher_delete_view(request, pk):
    """Delete a teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)

    if request.method == 'POST':
        name = teacher.get_full_name()
        user = teacher.user
        teacher.delete()
        user.delete()
        messages.success(request, f'Teacher {name} deleted successfully.')

        if request.htmx:
            response = render(request, 'teachers/partials/teacher_delete_success.html')
            response['HX-Trigger'] = 'teacherDeleted'
            return response
        return redirect('teachers:list')

    context = {
        'teacher': teacher,
    }

    if request.htmx:
        return render(request, 'teachers/partials/teacher_delete_modal.html', context)

    return redirect('teachers:list')


@login_required
def teacher_bulk_import_view(request):
    """
    View to handle bulk import of teachers from CSV/XLSX files.
    """
    breadcrumbs = [
        {'name': 'Dashboard', 'url': reverse('dashboard:main_partial')},
        {'name': 'Teachers', 'url': reverse('teachers:list')},
        {'name': 'Bulk Import', 'url': ''},
    ]

    result = None
    preview_data = None
    validation_errors = None
    validation_stats = None

    if request.method == 'POST':
        form = TeacherBulkImportForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data['file']
            send_credentials = form.cleaned_data['send_credentials']

            action = request.POST.get('action', 'validate')

            if action == 'validate':
                # Just validate and show preview
                file.seek(0)
                is_valid, errors, preview, total_rows, stats = validate_import_file(file)
                preview_data = preview
                validation_errors = errors if not is_valid else None
                validation_stats = stats

                if is_valid:
                    result = {
                        'status': 'validated',
                        'total_rows': total_rows,
                        'stats': stats,
                        'message': f'File validated successfully. {total_rows} records ready to import.'
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
                success_count, error_count, errors, stats = process_import_file(file, send_emails=send_credentials)

                # Build detailed message
                msg_parts = [f'Successfully imported {success_count} teacher(s).']
                if stats.get('emails_sent', 0) > 0:
                    msg_parts.append(f"{stats['emails_sent']} credential emails sent.")
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
    else:
        form = TeacherBulkImportForm()

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
        return render(request, 'teachers/partials/bulk_import_content.html', context)

    return render(request, 'dashboard/dashboard.html', {
        'initial_main_content_url': reverse('teachers:bulk_import'),
        'active_sidebar_link': 'teachers:list',
        'page_title': 'Bulk Import Teachers',
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
        filename = 'teacher_import_template.xlsx'
    else:
        content = generate_template_csv()
        content_type = 'text/csv'
        filename = 'teacher_import_template.csv'

    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
