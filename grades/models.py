from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class GradeScale(models.Model):
    """
    Defines grading scales for the school.
    e.g., WASSCE (A1-F9), BECE (1-9), Primary Scale
    """
    LEVEL_TYPE_CHOICES = (
        ('primary', 'Primary School'),
        ('jhs', 'Junior High School'),
        ('shs', 'Senior High School'),
        ('all', 'All Levels'),
    )

    name = models.CharField(max_length=50)  # e.g., "WASSCE Scale", "BECE Scale"
    level_type = models.CharField(
        max_length=10,
        choices=LEVEL_TYPE_CHOICES,
        default='all',
        help_text="Which school level this scale applies to"
    )
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'grade_scales'
        ordering = ['level_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_level_type_display()})"

    def save(self, *args, **kwargs):
        # Ensure only one default scale per level type
        if self.is_default:
            GradeScale.objects.filter(
                level_type=self.level_type, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class GradeLevel(models.Model):
    """
    Individual grade levels within a scale.
    e.g., A1 = 80-100, B2 = 70-79
    """
    scale = models.ForeignKey(
        GradeScale,
        on_delete=models.CASCADE,
        related_name='levels'
    )
    grade = models.CharField(max_length=5)  # e.g., "A1", "B2", "C4"
    description = models.CharField(max_length=50, blank=True)  # e.g., "Excellent"
    min_score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="Grade point value for GPA calculation"
    )
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'grade_scale_levels'
        ordering = ['scale', '-min_score']
        unique_together = [['scale', 'grade']]

    def __str__(self):
        return f"{self.grade} ({self.min_score}-{self.max_score})"


class AssessmentType(models.Model):
    """
    Types of assessments: Exam, Quiz, Assignment, Project, etc.
    """
    name = models.CharField(max_length=50)  # e.g., "End of Term Exam"
    code = models.CharField(max_length=10, unique=True)  # e.g., "EXAM", "QUIZ"
    description = models.CharField(max_length=255, blank=True)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Weight in final grade calculation"
    )
    is_exam = models.BooleanField(
        default=False,
        help_text="Is this an examination (vs continuous assessment)?"
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'assessment_types'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Assessment(models.Model):
    """
    A specific assessment event for a class/subject.
    e.g., "Form 1 Science - Mid-Term Exam - Term 1 2024"
    """
    # What is being assessed
    class_subject = models.ForeignKey(
        'academics.ClassSubject',
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    term = models.ForeignKey(
        'academics.Term',
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.PROTECT,
        related_name='assessments'
    )

    # Assessment details
    title = models.CharField(max_length=100)  # e.g., "Mid-Term Examination"
    description = models.TextField(blank=True)
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00')
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Weight of this assessment (overrides type weight if set)"
    )

    # Dates
    date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    # Status
    is_published = models.BooleanField(
        default=False,
        help_text="Students can see their grades when published"
    )
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assessments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assessments'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['class_subject', 'term']),
            models.Index(fields=['term', 'is_published']),
        ]

    def __str__(self):
        return f"{self.class_subject.class_instance} - {self.class_subject.subject.name} - {self.title}"

    @property
    def subject(self):
        return self.class_subject.subject

    @property
    def class_instance(self):
        return self.class_subject.class_instance

    @property
    def grades_count(self):
        return self.grades.count()

    @property
    def average_score(self):
        from django.db.models import Avg
        avg = self.grades.aggregate(avg=Avg('score'))['avg']
        return round(avg, 2) if avg else None


class Grade(models.Model):
    """
    Individual student grade for an assessment.
    """
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='grades'
    )

    # Score
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    # Remarks
    remarks = models.CharField(max_length=255, blank=True)

    # Status
    is_absent = models.BooleanField(default=False)
    is_excused = models.BooleanField(default=False)

    # Audit
    graded_by = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        related_name='graded_entries'
    )
    graded_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'grades'
        unique_together = [['assessment', 'student']]
        ordering = ['student__last_name', 'student__first_name']
        indexes = [
            models.Index(fields=['assessment', 'student']),
            models.Index(fields=['student', 'graded_at']),
        ]

    def __str__(self):
        return f"{self.student} - {self.assessment.title}: {self.score}"

    @property
    def percentage(self):
        if self.score is None or self.assessment.max_score == 0:
            return None
        return round((self.score / self.assessment.max_score) * 100, 2)

    @property
    def letter_grade(self):
        """Get letter grade based on default grade scale."""
        if self.percentage is None:
            return None

        scale = GradeScale.objects.filter(is_default=True).first()
        if not scale:
            return None

        level = scale.levels.filter(
            min_score__lte=self.percentage,
            max_score__gte=self.percentage
        ).first()

        return level.grade if level else None


class TermResult(models.Model):
    """
    Aggregated term results for a student in a subject.
    Calculated from individual assessments.
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='term_results'
    )
    class_subject = models.ForeignKey(
        'academics.ClassSubject',
        on_delete=models.CASCADE,
        related_name='term_results'
    )
    term = models.ForeignKey(
        'academics.Term',
        on_delete=models.CASCADE,
        related_name='term_results'
    )

    # Calculated scores
    class_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weighted score from class work, quizzes, assignments"
    )
    exam_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Score from end of term examination"
    )
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    grade = models.CharField(max_length=5, blank=True)
    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Position/Ranking
    position = models.IntegerField(null=True, blank=True)

    # Teacher's remarks
    remarks = models.CharField(max_length=255, blank=True)

    # Meta
    is_published = models.BooleanField(default=False)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'term_results'
        unique_together = [['student', 'class_subject', 'term']]
        ordering = ['term', 'class_subject__subject__name']
        indexes = [
            models.Index(fields=['student', 'term']),
            models.Index(fields=['class_subject', 'term']),
        ]

    def __str__(self):
        return f"{self.student} - {self.class_subject.subject.name} - {self.term}: {self.total_score}"
