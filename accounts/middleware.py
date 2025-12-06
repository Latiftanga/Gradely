from django.shortcuts import redirect
from django.db import connection
from django.http import Http404


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
