from django.contrib import admin, messages
from django import forms
from django.db import transaction
from django_tenants.utils import schema_context

from .models import School, Domain
from accounts.models import User


class SchoolAdminForm(forms.ModelForm):
    """Custom form for the School admin"""
    admin_email = forms.EmailField(
        label="School Administrator Email",
        help_text="Email for the first administrator of this school."
    )
    admin_password = forms.CharField(
        label="Administrator Password",
        widget=forms.PasswordInput,
        help_text="Initial password for the school administrator."
    )

    class Meta:
        model = School
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an existing school, don't require admin fields
        if self.instance.pk:
            self.fields['admin_email'].required = False
            self.fields['admin_password'].required = False
        else:
            self.fields['admin_email'].required = True
            self.fields['admin_password'].required = True


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
            'fields': ('admin_email', 'admin_password'),
            'description': 'Create the first administrator for this school. This only applies when creating a new school.'
        }),
        ('Timestamps', {'fields': ('created_on', 'updated_on')}),
    )

    def save_model(self, request, obj, form, change):
        """
        Override save_model to create the first school admin user
        when a new school is created.
        """
        is_new = not obj.pk

        # Use a transaction to ensure atomicity
        try:
            with transaction.atomic():
                # Save the school object first to create the schema
                super().save_model(request, obj, form, change)

                if is_new:
                    # New school, create the admin user
                    admin_email = form.cleaned_data.get('admin_email')
                    admin_password = form.cleaned_data.get('admin_password')

                    if not admin_email or not admin_password:
                        # This should be caught by form validation, but as a safeguard:
                        self.message_user(
                            request,
                            "School was created, but the admin user was not, due to missing email or password.",
                            messages.WARNING
                        )
                        return

                    # Switch to the new tenant's schema to create the user
                    with schema_context(obj):
                        if User.objects.filter(email=admin_email).exists():
                            self.message_user(
                                request,
                                f"An admin user with the email {admin_email} already exists in this schema.",
                                messages.ERROR
                            )
                            # This will cause the transaction to roll back
                            raise transaction.TransactionManagementError("User already exists.")

                        User.objects.create_school_adminuser(
                            email=admin_email,
                            password=admin_password
                        )
                    
                    self.message_user(
                        request,
                        f"School '{obj.name}' and administrator '{admin_email}' created successfully.",
                        messages.SUCCESS
                    )

        except Exception as e:
            self.message_user(
                request,
                f"An error occurred: {e}",
                messages.ERROR
            )
        
        # Note: If it's not a new school, the default save_model behavior is sufficient.
        if not is_new:
             super().save_model(request, obj, form, change)