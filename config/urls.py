from django.urls import path, include
from django.conf import settings
from django.views.generic.base import RedirectView


urlpatterns = [
    # App-specific URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('students/', include('students.urls', namespace='students')),
    path('teachers/', include('teachers.urls', namespace='teachers')),
    path('academics/', include('academics.urls', namespace='academics')),
    path('grades/', include('grades.urls', namespace='grades')),

    # Dashboard at root (must be last to not override other paths)
    path('', include('dashboard.urls', namespace='dashboard')),
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]