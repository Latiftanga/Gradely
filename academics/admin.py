from django.contrib import admin
from .models import Programme, GradeLevel, AcademicYear, Term, Class


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
    list_display = ['__str__', 'grade_level', 'section', 'academic_year', 'class_teacher', 'capacity', 'is_active']
    list_filter = ['grade_level', 'academic_year', 'programme', 'is_active']
    search_fields = ['section', 'grade_level__name', 'class_teacher__first_name', 'class_teacher__last_name']
    raw_id_fields = ['class_teacher']
    ordering = ['grade_level__order', 'section']
