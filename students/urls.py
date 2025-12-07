from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list_view, name='list'),
    path('add/', views.student_add_view, name='add'),
    path('bulk-import/', views.student_bulk_import_view, name='bulk_import'),
    path('template/<str:format>/', views.download_import_template, name='download_template'),
    path('<int:pk>/', views.student_detail_view, name='detail'),
    path('<int:pk>/update/', views.student_update_view, name='update'),
    path('<int:pk>/delete/', views.student_delete_view, name='delete'),
]
