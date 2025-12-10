from django.db import models
from django.utils import timezone
from accounts.models import User


class Student(models.Model):
    """
    Student profile linked to User model
    """
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    RESIDENTIAL_STATUS_CHOICES = (
        ('day', 'Day Student'),
        ('boarder', 'Boarder'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('withdrawn', 'Withdrawn'),
        ('transferred', 'Transferred'),
        ('suspended', 'Suspended'),
    )

    # User relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='student_profile'
    )

    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    # Core identification
    student_id = models.CharField(max_length=20, unique=True, db_index=True)
    index_number = models.CharField(
        max_length=20, blank=True, unique=True, null=True,
        help_text="BECE/WASSCE Index Number"
    )

    # Academic information
    current_class = models.ForeignKey(
        'academics.Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    admission_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    previous_school = models.CharField(max_length=200, blank=True)

    # Location information
    hometown = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=50, default='Ghanaian')
    ghana_card_number = models.CharField(
        max_length=20, blank=True, help_text="Ghana Card ID"
    )

    # Residential information
    residential_status = models.CharField(
        max_length=10, choices=RESIDENTIAL_STATUS_CHOICES, default='day'
    )
    house = models.CharField(
        max_length=50, blank=True, help_text="Boarding house name (if applicable)"
    )
    residential_address = models.TextField(blank=True)

    # Health information
    medical_conditions = models.CharField(max_length=255, blank=True)
    allergies = models.CharField(max_length=255, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='active'
    )
    withdrawal_date = models.DateField(null=True, blank=True)
    withdrawal_reason = models.TextField(blank=True)

    # Graduation info
    graduation_date = models.DateField(null=True, blank=True)
    graduation_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graduated_students',
        help_text="Academic year when student graduated"
    )

    date_enrolled = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['current_class', 'is_active']),
            models.Index(fields=['admission_date']),
            models.Index(fields=['residential_status', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} - {self.student_id}"

    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_boarder(self):
        return self.residential_status == 'boarder'


class Parent(models.Model):
    """
    Parent/Guardian profile linked to User model
    """
    RELATIONSHIP_CHOICES = (
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('grandparent', 'Grandparent'),
        ('sibling', 'Sibling'),
        ('other', 'Other Relative'),
    )

    # User relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='parent_profile'
    )

    # Personal information
    title = models.CharField(max_length=10, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)

    # Relationship to student(s)
    relationship = models.CharField(max_length=15, choices=RELATIONSHIP_CHOICES)
    students = models.ManyToManyField(Student, related_name='parents')

    # Professional information
    occupation = models.CharField(max_length=100, blank=True)
    employer = models.CharField(max_length=100, blank=True)
    work_phone = models.CharField(max_length=15, blank=True)
    work_address = models.TextField(blank=True)

    # Address information
    residential_address = models.TextField(blank=True)
    hometown = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=50, blank=True)

    # Communication preferences
    is_primary_contact = models.BooleanField(
        default=False, help_text="Primary contact for school communications"
    )
    is_emergency_contact = models.BooleanField(default=False)
    can_pickup_student = models.BooleanField(default=True)

    # Status
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'parents'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['is_primary_contact']),
            models.Index(fields=['relationship']),
            models.Index(fields=['is_emergency_contact']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_relationship_display()})"

    def get_full_name(self):
        name_parts = []
        if self.title:
            name_parts.append(self.title)
        name_parts.append(self.first_name)
        if self.middle_name:
            name_parts.append(self.middle_name)
        name_parts.append(self.last_name)
        return ' '.join(name_parts)

    def get_short_name(self):
        if self.title:
            return f"{self.title} {self.last_name}"
        return self.first_name
