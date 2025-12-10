from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='main'),
    path('content/', views.main_partial_view, name='main_partial'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/school-info/', views.settings_school_info_view, name='settings_school_info'),
    path('settings/academic-years/', views.settings_academic_years_view, name='settings_academic_years'),
    path('settings/terms/', views.settings_terms_view, name='settings_terms'),
    path('settings/grade-levels/', views.settings_grade_levels_view, name='settings_grade_levels'),
    path('settings/programmes/', views.settings_programmes_view, name='settings_programmes'),
    path('settings/grading-scales/', views.settings_grading_scales_view, name='settings_grading_scales'),
    path('settings/assessment-types/', views.settings_assessment_types_view, name='settings_assessment_types'),

    # Grading Scale CRUD
    path('settings/grading-scales/add/', views.grading_scale_add_view, name='grading_scale_add'),
    path('settings/grading-scales/<int:pk>/edit/', views.grading_scale_edit_view, name='grading_scale_edit'),
    path('settings/grading-scales/<int:pk>/delete/', views.grading_scale_delete_view, name='grading_scale_delete'),

    # Assessment Type CRUD
    path('settings/assessment-types/add/', views.assessment_type_add_view, name='assessment_type_add'),
    path('settings/assessment-types/<int:pk>/edit/', views.assessment_type_edit_view, name='assessment_type_edit'),
    path('settings/assessment-types/<int:pk>/delete/', views.assessment_type_delete_view, name='assessment_type_delete'),
]
