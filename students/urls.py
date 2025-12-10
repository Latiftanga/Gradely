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
    path('<int:pk>/export-pdf/', views.student_export_pdf_view, name='export_pdf'),
    # Parent management
    path('<int:student_pk>/parents/add/', views.add_parent_view, name='add_parent'),
    path('<int:student_pk>/parents/link/', views.link_parent_view, name='link_parent'),
    path('<int:student_pk>/parents/<int:parent_pk>/unlink/', views.unlink_parent_view, name='unlink_parent'),
]
