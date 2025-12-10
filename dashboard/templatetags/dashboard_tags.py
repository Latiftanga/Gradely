from django import template
from django.urls import reverse, NoReverseMatch
from accounts.models import User # Import the tenant User model
import re

register = template.Library()

@register.inclusion_tag('dashboard/partials/navbar.html', takes_context=True)
def user_navbar(context):
    """
    Custom template tag to render the main navbar.
    """
    return {
        'user': context.get('user'),
        'tenant': context.get('tenant'),
    }


@register.inclusion_tag('dashboard/partials/sidebar_menu.html', takes_context=True)
def user_sidebar_menu(context):
    """
    Custom template tag to render the sidebar menu based on user role.
    Uses menu configuration from dashboard.menu_config module.
    """
    from dashboard.menu_config import get_user_menu

    user = context.get('user')
    if not user:
        return {'user_menu': []}

    user_menu = get_user_menu(user)
    return {'user_menu': user_menu}


@register.filter(name='is_safe_url')
def is_safe_url(url):
    """
    Validates that a URL is safe to use in templates.
    Only allows relative URLs starting with / or URL names.
    Blocks external URLs and javascript: schemes.
    """
    if not url or url == '':
        return False

    # Block javascript: and data: schemes
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:']
    url_lower = url.lower().strip()
    for scheme in dangerous_schemes:
        if url_lower.startswith(scheme):
            return False

    # Block absolute URLs (http://, https://, //)
    if url_lower.startswith(('http://', 'https://', '//')):
        return False

    # Allow relative URLs starting with /
    if url.startswith('/'):
        return True

    # Block everything else for safety
    return False

