from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import schema_context
from accounts.models import User
from tenants.models import School


class Command(BaseCommand):
    help = 'Create a user in a school'
    
    def add_arguments(self, parser):
        parser.add_argument('--schema', required=True, help='School schema')
        parser.add_argument('--email', required=True, help='User email')
        parser.add_argument('--password', required=True, help='User password')
        parser.add_argument('--role', required=True, 
                          choices=['school_admin', 'teacher', 'student', 'parent'])
    
    def handle(self, *args, **options):
        schema = options['schema']
        
        try:
            school = School.objects.get(schema_name=schema)
        except School.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ School "{schema}" not found'))
            return
        
        with schema_context(schema):
            try:
                with transaction.atomic():
                    role = options['role']
                    
                    if role == 'school_admin':
                        user = User.objects.create_school_adminuser(
                            email=options['email'],
                            password=options['password']
                        )
                    elif role == 'teacher':
                        user = User.objects.create_teacheruser(
                            email=options['email'],
                            password=options['password']
                        )
                    elif role == 'student':
                        user = User.objects.create_studentuser(
                            email=options['email'],
                            password=options['password']
                        )
                    elif role == 'parent':
                        user = User.objects.create_parentuser(
                            email=options['email'],
                            password=options['password']
                        )
                    
                    self.stdout.write(self.style.SUCCESS(f'✓ User created: {user.email}'))
                    self.stdout.write(self.style.SUCCESS(f'✓ Role: {user.get_role_display()}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed: {str(e)}'))
