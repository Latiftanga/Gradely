from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='main'),
    path('main/', views.main_partial_view, name='main_partial'),
    # Add other dashboard-related URLs here
]
