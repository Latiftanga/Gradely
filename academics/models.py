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
    is_final_level = models.BooleanField(
        default=False,
        help_text="Mark as final level (e.g., Form 3, JHS 3). Students completing this level will graduate."
    )
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
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'terms'
        ordering = ['academic_year', 'term_number']
        unique_together = [['academic_year', 'term_number']]

    def __str__(self):
        return f"{self.academic_year.name} - {self.get_term_number_display()}"

    @property
    def name(self):
        """Return term name from choices for backwards compatibility"""
        return self.get_term_number_display()

    def save(self, *args, **kwargs):
        # Ensure only one term is current
        if self.is_current:
            Term.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Class(models.Model):
    """
    Represents a permanent class section within a grade level.
    Classes are year-independent; student enrollment is tracked via ClassEnrollment.
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

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'classes'
        verbose_name_plural = 'classes'
        ordering = ['grade_level__order', 'section']
        unique_together = [['grade_level', 'section', 'programme']]
        indexes = [
            models.Index(fields=['grade_level', 'is_active']),
        ]

    def __str__(self):
        if self.programme:
            return f"{self.grade_level.numeric_level} {self.programme.code}-{self.section}"
        if self.section:
            return f"{self.grade_level.numeric_level} {self.section}"
        return self.grade_level.name

    def get_current_enrollment(self, academic_year=None):
        """Get enrollment count for a specific academic year (defaults to current)"""
        if academic_year is None:
            academic_year = AcademicYear.objects.filter(is_current=True).first()
        if academic_year:
            return self.enrollments.filter(
                academic_year=academic_year,
                is_active=True
            ).count()
        return 0

    @property
    def current_enrollment(self):
        """Get enrollment for current academic year"""
        return self.get_current_enrollment()

    @property
    def has_space(self):
        return self.current_enrollment < self.capacity

    @property
    def enrollment_percentage(self):
        if self.capacity == 0:
            return 0
        return round((self.current_enrollment / self.capacity) * 100, 1)


class ClassEnrollment(models.Model):
    """
    Tracks student enrollment in classes per academic year.
    This allows the same class to have different students each year.
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='class_enrollments'
    )
    class_instance = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    # Enrollment details
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # For tracking promotions/transfers
    promoted_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promoted_to',
        help_text="Previous enrollment if student was promoted"
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'class_enrollments'
        verbose_name = 'Class Enrollment'
        verbose_name_plural = 'Class Enrollments'
        unique_together = [['student', 'academic_year']]  # One class per student per year
        ordering = ['-academic_year__start_date', 'class_instance__grade_level__order']
        indexes = [
            models.Index(fields=['academic_year', 'is_active']),
            models.Index(fields=['class_instance', 'academic_year']),
            models.Index(fields=['student', 'is_active']),
        ]

    def __str__(self):
        return f"{self.student} - {self.class_instance} ({self.academic_year.name})"

    def save(self, *args, **kwargs):
        # Update student's current_class if this is for the current academic year
        super().save(*args, **kwargs)
        if self.academic_year.is_current and self.is_active:
            self.student.current_class = self.class_instance
            self.student.save(update_fields=['current_class'])


class Subject(models.Model):
    """
    Represents a subject that can be taught in the school
    """
    SUBJECT_TYPE_CHOICES = (
        ('core', 'Core Subject'),
        ('elective', 'Elective Subject'),
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    subject_type = models.CharField(
        max_length=10,
        choices=SUBJECT_TYPE_CHOICES,
        default='core'
    )

    # Which level types can take this subject
    applicable_levels = models.ManyToManyField(
        GradeLevel,
        related_name='available_subjects',
        blank=True,
        help_text="Grade levels where this subject is offered"
    )

    # For SHS elective subjects
    programmes = models.ManyToManyField(
        Programme,
        related_name='subjects',
        blank=True,
        help_text="Programmes that offer this subject (for electives)"
    )

    # Credits/weight for grading
    credit_hours = models.DecimalField(
        max_digits=3, decimal_places=1, default=1.0,
        help_text="Weight of subject in GPA calculation"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['name']
        indexes = [
            models.Index(fields=['subject_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ClassSubject(models.Model):
    """
    Represents the assignment of a subject to a class with an assigned teacher
    """
    class_instance = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_subjects'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='class_assignments'
    )
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_assignments'
    )

    # Schedule information
    periods_per_week = models.IntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'class_subjects'
        verbose_name = 'Class Subject Assignment'
        verbose_name_plural = 'Class Subject Assignments'
        unique_together = [['class_instance', 'subject']]
        ordering = ['subject__name']
        indexes = [
            models.Index(fields=['class_instance', 'is_active']),
            models.Index(fields=['teacher', 'is_active']),
        ]

    def __str__(self):
        teacher_name = self.teacher.get_full_name() if self.teacher else "Unassigned"
        return f"{self.subject.name} - {self.class_instance} ({teacher_name})"
