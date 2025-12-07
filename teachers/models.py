from django.db import models
from django.utils import timezone
from accounts.models import User


class Teacher(models.Model):
    """
    Teacher profile linked to User model
    """
    EMPLOYMENT_STATUS_CHOICES = (
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('volunteer', 'Volunteer'),
    )

    QUALIFICATION_CHOICES = (
        ('diploma', 'Diploma'),
        ('bachelors', "Bachelor's Degree"),
        ('masters', "Master's Degree"),
        ('phd', 'PhD'),
        ('other', 'Other'),
    )

    # User relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='teacher_profile'
    )

    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=(('M', 'Male'), ('F', 'Female')),
        blank=True
    )

    # Professional information
    staff_id = models.CharField(max_length=20, unique=True, db_index=True)
    ghana_card_number = models.CharField(
        max_length=20, blank=True, help_text="Ghana Card ID"
    )
    ssnit_number = models.CharField(max_length=20, blank=True)
    tin_number = models.CharField(max_length=20, blank=True)

    # Employment details
    employment_status = models.CharField(
        max_length=15,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='full_time'
    )
    date_employed = models.DateField()
    qualification = models.CharField(
        max_length=20,
        choices=QUALIFICATION_CHOICES,
        default='bachelors'
    )
    specialization = models.CharField(
        max_length=100, blank=True,
        help_text="Area of specialization (e.g., Mathematics, English)"
    )

    # Contact information
    phone_number = models.CharField(max_length=15, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    residential_address = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teachers'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['staff_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['employment_status', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} - {self.staff_id}"

    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def years_of_service(self):
        today = timezone.now().date()
        return today.year - self.date_employed.year - (
            (today.month, today.day) < (self.date_employed.month, self.date_employed.day)
        )
