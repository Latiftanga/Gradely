from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = [
        'staff_id', 'get_full_name', 'gender', 'employment_status',
        'qualification', 'date_employed', 'is_active'
    ]
    list_filter = ['employment_status', 'qualification', 'gender', 'is_active']
    search_fields = ['staff_id', 'first_name', 'last_name', 'user__email']
    raw_id_fields = ['user']
    ordering = ['last_name', 'first_name']
    date_hierarchy = 'date_employed'

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
        ('Professional Information', {
            'fields': (
                'staff_id', 'ghana_card_number', 'ssnit_number', 'tin_number'
            )
        }),
        ('Employment Details', {
            'fields': (
                'employment_status', 'date_employed',
                'qualification', 'specialization'
            )
        }),
        ('Contact Information', {
            'fields': (
                'phone_number', 'residential_address',
                'emergency_contact_name', 'emergency_contact_phone'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'termination_date', 'termination_reason')
        }),
    )
