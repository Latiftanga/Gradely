from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Programme(models.Model):
    """
    Represents different academic programmes in Senior High School (SHS)
    e.g., General Arts, Science, Business, Visual Arts, Home Economics
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'programmes'
        ordering = ['name']

    def __str__(self):
        return self.name


class GradeLevel(models.Model):
    """
    Supports both Basic (Primary 1-6, JHS 1-3) and SHS (Form 1-3) levels
    """
    LEVEL_TYPE_CHOICES = (
        ('primary', 'Primary School'),
        ('jhs', 'Junior High School'),
        ('shs', 'Senior High School'),
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    level_type = models.CharField(max_length=10, choices=LEVEL_TYPE_CHOICES)
    numeric_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'grade_levels'
        ordering = ['order', 'numeric_level']
        unique_together = [['level_type', 'numeric_level']]

    def __str__(self):
        return self.name


class AcademicYear(models.Model):
    """
    Represents an academic year (e.g., 2024/2025)
    """
    name = models.CharField(
        max_length=9, unique=True,
        help_text="Academic year in format YYYY/YYYY (e.g., 2024/2025)"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one academic year is current
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Term(models.Model):
    """
    Represents a term within an academic year
    """
    TERM_CHOICES = (
        (1, 'First Term'),
        (2, 'Second Term'),
        (3, 'Third Term'),
    )

    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='terms'
    )
    term_number = models.IntegerField(choices=TERM_CHOICES)
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'terms'
        ordering = ['academic_year', 'term_number']
        unique_together = [['academic_year', 'term_number']]

    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"

    def save(self, *args, **kwargs):
        # Ensure only one term is current
        if self.is_current:
            Term.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Class(models.Model):
    """
    Represents a specific class section within a grade level
    """
    grade_level = models.ForeignKey(
        GradeLevel, on_delete=models.CASCADE, related_name='classes'
    )
    section = models.CharField(
        max_length=10, blank=True,
        help_text='e.g., A, B, C, Gold, Diamond, etc'
    )
    capacity = models.IntegerField(default=40, validators=[MinValueValidator(1)])
    programme = models.ForeignKey(
        Programme, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='classes'
    )

    class_teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_classes',
        verbose_name='Form Teacher/Class Teacher'
    )

    # Classroom details
    room_number = models.CharField(max_length=20, blank=True)
    building = models.CharField(max_length=50, blank=True)

    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='classes'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'classes'
        verbose_name_plural = 'classes'
        ordering = ['grade_level__order', 'section']
        unique_together = [['grade_level', 'section', 'academic_year']]
        indexes = [
            models.Index(fields=['academic_year', 'is_active']),
            models.Index(fields=['grade_level', 'is_active']),
        ]

    def __str__(self):
        if self.programme:
            return f"{self.grade_level.name} {self.programme.code}-{self.section}"
        if self.section:
            return f"{self.grade_level.name} {self.section}"
        return self.grade_level.name

    @property
    def full_name(self):
        """Returns the full class name with academic year"""
        return f"{self} ({self.academic_year.name})"

    @property
    def current_enrollment(self):
        return self.students.filter(is_active=True).count()

    @property
    def has_space(self):
        return self.current_enrollment < self.capacity

    @property
    def enrollment_percentage(self):
        if self.capacity == 0:
            return 0
        return round((self.current_enrollment / self.capacity) * 100, 1)
