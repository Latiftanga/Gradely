from django.contrib import admin
from .models import (
    Programme, GradeLevel, AcademicYear, Term, Class,
    ClassEnrollment, Subject, ClassSubject
)


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'level_type', 'numeric_level', 'order', 'is_active']
    list_filter = ['level_type', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['order', 'numeric_level']


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_current', 'is_active']
    list_filter = ['is_current', 'is_active']
    search_fields = ['name']
    ordering = ['-start_date']


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'term_number', 'start_date', 'end_date', 'is_current']
    list_filter = ['academic_year', 'term_number', 'is_current']
    search_fields = ['name', 'academic_year__name']
    ordering = ['academic_year', 'term_number']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'grade_level', 'section', 'programme', 'class_teacher', 'capacity', 'is_active']
    list_filter = ['grade_level', 'programme', 'is_active']
    search_fields = ['section', 'grade_level__name', 'class_teacher__first_name', 'class_teacher__last_name']
    raw_id_fields = ['class_teacher']
    ordering = ['grade_level__order', 'section']


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_instance', 'academic_year', 'enrollment_date', 'is_active']
    list_filter = ['academic_year', 'class_instance__grade_level', 'is_active']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_id']
    raw_id_fields = ['student', 'class_instance', 'promoted_from']
    ordering = ['-academic_year__start_date', 'class_instance__grade_level__order']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'subject_type', 'credit_hours', 'is_active']
    list_filter = ['subject_type', 'is_active']
    search_fields = ['name', 'code']
    filter_horizontal = ['applicable_levels', 'programmes']
    ordering = ['name']


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ['subject', 'class_instance', 'teacher', 'periods_per_week', 'is_active']
    list_filter = ['class_instance__grade_level', 'subject', 'is_active']
    search_fields = ['subject__name', 'class_instance__grade_level__name', 'teacher__first_name', 'teacher__last_name']
    raw_id_fields = ['teacher']
    ordering = ['class_instance__grade_level__order', 'subject__name']
