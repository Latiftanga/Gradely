from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import connection
from accounts.models import User as SchoolUser


class MultiTenantAuthBackend(ModelBackend):
    """
    Custom backend that handles authentication for both:
    1. SystemUser (public schema)
    2. User (tenant schema)
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Get the current schema from the connection
        schema_name = connection.schema_name
        
        if schema_name == 'public':
            # Public schema: authenticate SystemUser
            UserModel = get_user_model()  # SystemUser
            try:
                user = UserModel.objects.get(email=username)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except UserModel.DoesNotExist:
                return None
        else:
            # Tenant schema: authenticate User
            try:
                user = SchoolUser.objects.get(email=username)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except SchoolUser.DoesNotExist:
                return None
        
        return None
    
    def get_user(self, user_id):
        """Retrieve user from appropriate schema"""
        schema_name = connection.schema_name
        
        if schema_name == 'public':
            UserModel = get_user_model()
        else:
            UserModel = SchoolUser
        
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None