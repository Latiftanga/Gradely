from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Academic Years
    path('academic-years/', views.academic_year_list_view, name='academic_years'),
    path('academic-years/add/', views.academic_year_add_view, name='academic_year_add'),
    path('academic-years/<int:pk>/edit/', views.academic_year_edit_view, name='academic_year_edit'),
    path('academic-years/<int:pk>/delete/', views.academic_year_delete_view, name='academic_year_delete'),

    # Terms
    path('terms/add/', views.term_add_view, name='term_add'),
    path('terms/<int:pk>/edit/', views.term_edit_view, name='term_edit'),
    path('terms/<int:pk>/delete/', views.term_delete_view, name='term_delete'),

    # Grade Levels
    path('grade-levels/', views.grade_level_list_view, name='grade_levels'),
    path('grade-levels/add/', views.grade_level_add_view, name='grade_level_add'),
    path('grade-levels/<int:pk>/edit/', views.grade_level_edit_view, name='grade_level_edit'),
    path('grade-levels/<int:pk>/delete/', views.grade_level_delete_view, name='grade_level_delete'),

    # Programmes
    path('programmes/', views.programme_list_view, name='programmes'),
    path('programmes/add/', views.programme_add_view, name='programme_add'),
    path('programmes/<int:pk>/edit/', views.programme_edit_view, name='programme_edit'),
    path('programmes/<int:pk>/delete/', views.programme_delete_view, name='programme_delete'),

    # Classes
    path('classes/', views.class_list_view, name='classes'),
    path('classes/partial/', views.class_list_partial_view, name='class_list_partial'),
    path('classes/add/', views.class_add_view, name='class_add'),
    path('classes/<int:pk>/', views.class_detail_view, name='class_detail'),
    path('classes/<int:pk>/edit/', views.class_edit_view, name='class_edit'),
    path('classes/<int:pk>/delete/', views.class_delete_view, name='class_delete'),

    # Class Subjects
    path('classes/<int:class_pk>/subjects/add/', views.class_subject_add_view, name='class_subject_add'),
    path('classes/<int:class_pk>/subjects/<int:pk>/edit/', views.class_subject_edit_view, name='class_subject_edit'),
    path('classes/<int:class_pk>/subjects/<int:pk>/remove/', views.class_subject_remove_view, name='class_subject_remove'),

    # Class Enrollments
    path('classes/<int:class_pk>/enroll/', views.class_enrollment_add_view, name='class_enrollment_add'),
    path('classes/<int:class_pk>/enroll/bulk/', views.bulk_enrollment_view, name='bulk_enrollment'),
    path('classes/<int:class_pk>/enrollments/<int:pk>/remove/', views.class_enrollment_remove_view, name='class_enrollment_remove'),

    # Subjects
    path('subjects/', views.subject_list_view, name='subjects'),
    path('subjects/partial/', views.subject_list_partial_view, name='subject_list_partial'),
    path('subjects/add/', views.subject_add_view, name='subject_add'),
    path('subjects/<int:pk>/', views.subject_detail_view, name='subject_detail'),
    path('subjects/<int:pk>/edit/', views.subject_edit_view, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete_view, name='subject_delete'),

    # Student Promotion
    path('promotion/', views.promotion_view, name='promotion'),
    path('promotion/preview/', views.promotion_preview_view, name='promotion_preview'),
    path('promotion/execute/', views.promotion_execute_view, name='promotion_execute'),
    path('api/classes/<int:class_pk>/students/', views.get_class_students_json, name='api_class_students'),
    path('api/suggest-target-class/', views.get_suggested_target_class, name='api_suggest_target'),
]
