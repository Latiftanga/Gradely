from django.shortcuts import redirect
from django.db import connection
from django.http import Http404
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """
    Forces users with force_password_change=True to change their password
    before accessing any other pages.
    """
    # URLs that should be accessible even when password change is required
    EXEMPT_URLS = [
        '/accounts/change-password/',
        '/accounts/logout/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user has force_password_change attribute and it's True
            if hasattr(request.user, 'force_password_change') and request.user.force_password_change:
                # Check if the current path is exempt
                path = request.path
                is_exempt = any(path.startswith(url) for url in self.EXEMPT_URLS)

                if not is_exempt:
                    return redirect('accounts:change_password')

        return self.get_response(request)


class SchoolUserRedirectMiddleware:
    """
    Prevents tenant users from accessing public admin
    Redirects them to their tenant domain
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only process authenticated users trying to access admin
        if request.user.is_authenticated and request.path.startswith('/admin/'):
            schema_name = connection.schema_name
            
            # If a tenant user tries to access public admin, redirect
            if schema_name == 'public' and hasattr(request.user, 'role'):
                # This is a User (tenant), not SystemUser
                # Redirect to their tenant domain
                return redirect('/')  # Or show error message
        
        response = self.get_response(request)
        return response


class BlockSchoolAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/admin/'):
            if connection.schema_name != 'public':
                raise Http404("Page not found")
        
        return self.get_response(request)
