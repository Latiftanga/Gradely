from django.contrib import admin
from .models import Student, Parent


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'student_id', 'get_full_name', 'gender', 'current_class',
        'residential_status', 'admission_date', 'is_active'
    ]
    list_filter = [
        'gender', 'current_class__grade_level', 'residential_status',
        'is_active', 'current_class__academic_year'
    ]
    search_fields = [
        'student_id', 'first_name', 'last_name',
        'admission_number', 'user__email'
    ]
    raw_id_fields = ['user', 'current_class']
    ordering = ['last_name', 'first_name']
    date_hierarchy = 'admission_date'

    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 'middle_name', 'last_name',
                'date_of_birth', 'gender'
            )
        }),
        ('Identification', {
            'fields': (
                'student_id', 'index_number', 'admission_number', 'ghana_card_number'
            )
        }),
        ('Academic Information', {
            'fields': (
                'current_class', 'admission_date', 'previous_school'
            )
        }),
        ('Location', {
            'fields': (
                'hometown', 'region', 'nationality', 'residential_address'
            )
        }),
        ('Residential Status', {
            'fields': ('residential_status', 'house')
        }),
        ('Health Information', {
            'fields': ('medical_conditions', 'allergies', 'blood_group'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'withdrawal_date', 'withdrawal_reason')
        }),
    )


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name', 'relationship', 'phone_number',
        'is_primary_contact', 'is_emergency_contact', 'is_active'
    ]
    list_filter = ['relationship', 'is_primary_contact', 'is_emergency_contact', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone_number', 'user__email']
    raw_id_fields = ['user']
    filter_horizontal = ['students']
    ordering = ['last_name', 'first_name']

    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': (
                'title', 'first_name', 'middle_name', 'last_name',
                'phone_number', 'alternate_phone'
            )
        }),
        ('Relationship', {
            'fields': ('relationship', 'students')
        }),
        ('Professional Information', {
            'fields': ('occupation', 'employer', 'work_phone', 'work_address'),
            'classes': ('collapse',)
        }),
        ('Address', {
            'fields': ('residential_address', 'hometown', 'region'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('is_primary_contact', 'is_emergency_contact', 'can_pickup_student')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
