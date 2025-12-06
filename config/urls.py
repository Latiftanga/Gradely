from django.urls import path, include
from django.conf import settings
from django.views.generic.base import RedirectView


urlpatterns = [
    # Redirect tenant root to the dashboard
    path('', RedirectView.as_view(pattern_name='dashboard:main', permanent=False), name='tenant_root_redirect'),

    # App-specific URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]