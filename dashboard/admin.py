from django.contrib import admin
from .models import SchoolSettings


@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'email', 'phone', 'updated_at']
    fieldsets = (
        ('Branding', {
            'fields': ('logo', 'favicon', 'primary_color', 'secondary_color')
        }),
        ('Basic Information', {
            'fields': ('motto', 'principal_name', 'founded_year', 'school_type')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'alternate_phone', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'region', 'postal_code', 'country')
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        return not SchoolSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False
