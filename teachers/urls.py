from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list_view, name='list'),
    path('partial/', views.teacher_list_partial_view, name='list_partial'),
    path('add/', views.teacher_add_view, name='add'),
    path('bulk-import/', views.teacher_bulk_import_view, name='bulk_import'),
    path('template/<str:format>/', views.download_import_template, name='download_template'),
    path('<int:pk>/', views.teacher_detail_view, name='detail'),
    path('<int:pk>/edit/', views.teacher_update_view, name='update'),
    path('<int:pk>/delete/', views.teacher_delete_view, name='delete'),
]
