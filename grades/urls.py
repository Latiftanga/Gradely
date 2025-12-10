"""
URL patterns for grades app
"""
from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # Assessment CRUD
    path('', views.assessment_list_view, name='assessment_list'),
    path('partial/', views.assessment_list_partial_view, name='assessment_list_partial'),
    path('add/', views.assessment_add_view, name='assessment_add'),
    path('<int:pk>/', views.assessment_detail_view, name='assessment_detail'),
    path('<int:pk>/edit/', views.assessment_update_view, name='assessment_update'),
    path('<int:pk>/delete/', views.assessment_delete_view, name='assessment_delete'),
    path('<int:pk>/toggle-publish/', views.toggle_publish_view, name='toggle_publish'),

    # Grade entry
    path('<int:assessment_pk>/grades/', views.grade_entry_view, name='grade_entry'),

    # Assessment types (admin)
    path('types/', views.assessment_type_list_view, name='assessment_type_list'),
    path('types/add/', views.assessment_type_add_view, name='assessment_type_add'),
    path('types/<int:pk>/edit/', views.assessment_type_update_view, name='assessment_type_update'),
    path('types/<int:pk>/delete/', views.assessment_type_delete_view, name='assessment_type_delete'),

    # Grade scales (admin)
    path('scales/', views.grade_scale_list_view, name='grade_scale_list'),
]
