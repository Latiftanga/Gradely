from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.utils.text import slugify


class School(TenantMixin):
    """
    Each school is a separate tenant with its own database schema
    """
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, unique=True)
    
    # School details
    school_code = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    # Auto-create schema when school is saved
    auto_create_schema = True
    auto_drop_schema = False  # Keep data when school is deleted

    def save(self, *args, **kwargs):
        if not self.pk: # Only on creation
            # Sanitize short_name to be a valid schema name
            # PostgreSQL schema names can't start with 'pg_' and must be lowercase
            # It's safer to use slugify and replace hyphens
            self.schema_name = slugify(self.short_name).replace('-', '_')
        super(School, self).save(*args, **kwargs)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Domain mapping for each school
    Examples: 
    - school1.gradely.com
    - school2.gradely.com
    - custom-domain.edu
    """
    pass