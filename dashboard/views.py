from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse


@login_required
def dashboard_view(request):
    """
    Renders the main dashboard layout for a logged-in tenant user.
    The actual content is loaded via HTMX.
    """
    return render(request, 'dashboard/dashboard.html')


@login_required
def main_partial_view(request):
    """
    Renders the main dashboard content (widgets) for HTMX requests.
    """
    breadcrumbs = [
        {'name': 'Dashboard', 'url': ''},
    ]

    # In the future, you would pass real stats for the tenant here.
    context = {
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'dashboard/partials/dashboard_main.html', context)