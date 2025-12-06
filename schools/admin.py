from django.contrib import admin, messages
from django import forms
from django_tenants.utils import schema_context

from .models import School, Domain
from accounts.models import User


class SchoolAdminForm(forms.ModelForm):
    """Custom form for the School admin to add a school admin user."""
    admin_email = forms.EmailField(
        required=False,
        label="School Administrator Email",
        help_text="Required only when creating a new school. Creates the first admin user for the school."
    )
    admin_password = forms.CharField(
        required=False,
        label="Administrator Password",
        widget=forms.PasswordInput,
        help_text="Required only when creating a new school."
    )

    class Meta:
        model = School
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        is_new = not self.instance.pk
        if is_new:
            if not cleaned_data.get('admin_email'):
                self.add_error('admin_email', 'This field is required when creating a new school.')
            if not cleaned_data.get('admin_password'):
                self.add_error('admin_password', 'This field is required when creating a new school.')
        return cleaned_data


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1
    max_num = 3


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    form = SchoolAdminForm
    inlines = [DomainInline]
    list_display = ('name', 'short_name', 'school_code', 'is_active', 'created_on')
    list_filter = ('is_active',)
    search_fields = ('name', 'short_name', 'school_code')
    readonly_fields = ('created_on', 'updated_on')

    fieldsets = (
        (None, {'fields': ('name', 'short_name', 'school_code', 'is_active')}),
        ('Contact Information', {'fields': ('email', 'phone', 'address')}),
        ('New School Administrator', {
            'classes': ('collapse',),
            'fields': ('admin_email', 'admin_password'),
            'description': 'Create the first administrator for this school. This only applies when creating a new school.'
        }),
        ('Timestamps', {'fields': ('created_on', 'updated_on')}),
    )

    def save_model(self, request, obj, form, change):
        """
        Override save_model to temporarily store the admin user details
        on the school instance. The actual creation happens in response_add.
        """
        # Store details for later, but don't save them to the School model
        obj._admin_email = form.cleaned_data.get('admin_email')
        obj._admin_password = form.cleaned_data.get('admin_password')
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        """
        This method is called by the admin after a new object is successfully
        created and all its related objects (inlines) are saved.
        We use it to create the school admin user.
        """
        # We stored the admin details on the object instance in save_model
        admin_email = getattr(obj, '_admin_email', None)
        admin_password = getattr(obj, '_admin_password', None)

        if admin_email and admin_password:
            try:
                # Switch to the new tenant's schema to create the user
                with schema_context(obj.schema_name):
                    if User.objects.filter(email=admin_email).exists():
                        # This case is unlikely due to form validation but is a safeguard
                        messages.error(request, f"Admin user with email {admin_email} already exists in this schema.")
                    else:
                        User.objects.create_school_adminuser(
                            email=admin_email,
                            password=admin_password
                        )
                        messages.success(request, f"School '{obj.name}' created. Admin user '{admin_email}' also created successfully.")
            except Exception as e:
                messages.error(request, f"School '{obj.name}' was created, but failed to create admin user. Error: {e}")

        return super().response_add(request, obj, post_url_continue)

