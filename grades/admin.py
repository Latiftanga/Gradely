from django.contrib import admin
from .models import GradeScale, GradeLevel, AssessmentType, Assessment, Grade, TermResult


class GradeLevelInline(admin.TabularInline):
    model = GradeLevel
    extra = 1


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_active', 'created_at']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name']
    inlines = [GradeLevelInline]


@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'weight', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['order', 'name']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'class_subject', 'term', 'assessment_type', 'max_score', 'is_published', 'created_at']
    list_filter = ['assessment_type', 'is_published', 'is_active', 'term']
    search_fields = ['title', 'class_subject__subject__name']
    raw_id_fields = ['class_subject', 'term', 'created_by']
    date_hierarchy = 'created_at'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'assessment', 'score', 'is_absent', 'graded_at']
    list_filter = ['is_absent', 'assessment__assessment_type']
    search_fields = ['student__first_name', 'student__last_name', 'assessment__title']
    raw_id_fields = ['assessment', 'student', 'graded_by']


@admin.register(TermResult)
class TermResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_subject', 'term', 'total_score', 'grade', 'position', 'is_published']
    list_filter = ['is_published', 'term', 'grade']
    search_fields = ['student__first_name', 'student__last_name']
    raw_id_fields = ['student', 'class_subject', 'term']
