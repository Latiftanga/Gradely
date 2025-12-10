from django.db import models


class SchoolSettings(models.Model):
    """
    Tenant-specific school settings. Each school has their own isolated settings.
    Uses singleton pattern - only one instance per tenant.
    """
    # Basic Info
    logo = models.ImageField(
        upload_to='school_logos/',
        blank=True,
        null=True,
        help_text='School logo (recommended size: 200x200px)'
    )
    favicon = models.ImageField(
        upload_to='school_favicons/',
        blank=True,
        null=True,
        help_text='Browser favicon (recommended size: 32x32px)'
    )
    motto = models.CharField(max_length=255, blank=True)

    # Contact Info
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Ghana')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Additional Info
    principal_name = models.CharField(max_length=100, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    school_type = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
            ('mission', 'Mission/Religious'),
            ('international', 'International'),
        ],
        blank=True
    )

    # Branding
    primary_color = models.CharField(
        max_length=7,
        default='#570DF8',
        help_text='Primary brand color (hex format, e.g., #570DF8)'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#F000B8',
        help_text='Secondary brand color (hex format)'
    )

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Settings'
        verbose_name_plural = 'School Settings'
        db_table = 'school_settings'

    def __str__(self):
        return 'School Settings'

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance for the current tenant."""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        # Ensure singleton - always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion of settings
        pass
