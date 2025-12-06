# ============================================================================
# schools/management/commands/setup_schools.py
# ============================================================================

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import schema_context
from schools.models import School, Domain
from accounts.models import SystemUser, User
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = 'Setup public tenant and create test schools with user accounts'
    
    def add_arguments(self, parser):
        parser.add_argument('--domain', type=str, default='localhost', help='Base domain (default: localhost)')
        parser.add_argument('--skip-public', action='store_true', help='Skip public tenant creation if already exists')
        parser.add_argument('--skip-schools', action='store_true', help='Skip test schools creation')
        parser.add_argument('--schools-only', action='store_true', help='Only create test schools (assumes public exists)')
        parser.add_argument('--minimal', action='store_true', help='Create minimal users (only 1 admin per school)')
    
    def handle(self, *args, **options):
        base_domain = options['domain']
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🚀 Multi-Tenant School Management Setup'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        try:
            if not options['schools_only']:
                self.create_public_tenant(base_domain, options['skip_public'])
            
            if not options['skip_schools']:
                self.create_test_schools(base_domain, options['minimal'])
            
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
            self.stdout.write(self.style.SUCCESS('✅ Setup completed successfully!'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            
            self.print_summary(base_domain, options['minimal'])
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Setup failed: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise CommandError(f'Setup failed: {str(e)}')
    
    def create_public_tenant(self, base_domain, skip_if_exists):
        """Create public tenant (System Admin)"""
        self.stdout.write('\n📦 [1/3] Setting up Public Schema...')
        
        public_exists = School.objects.filter(schema_name='public').exists()
        
        if public_exists and skip_if_exists:
            self.stdout.write(self.style.WARNING('  ⊙ Public tenant already exists, skipping...'))
            return
        
        with transaction.atomic():
            if not public_exists:
                public_tenant = School.objects.create(
                    schema_name='public',
                    name='Platform Administration',
                    short_name='public',         # Model field
                    school_code='SYS-ADMIN',     # Model field (Unique)
                    email='admin@platform.com',
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS('  ✓ Public tenant created'))
            else:
                public_tenant = School.objects.get(schema_name='public')
                self.stdout.write(self.style.WARNING('  ⊙ Public tenant already exists'))
            
            domain, created = Domain.objects.update_or_create(
                tenant=public_tenant,
                is_primary=True,
                defaults={'domain': base_domain}
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Domain: {domain.domain}'))
        
        self.create_system_superuser()
    
    def create_system_superuser(self):
        """Create system superuser"""
        self.stdout.write('\n👤 [2/3] Creating System Superuser...')
        email = 'admin@platform.com'
        password = 'Admin123!'
        
        try:
            with transaction.atomic():
                user, created = SystemUser.objects.update_or_create(
                    email=email,
                    defaults={
                        'first_name': 'Platform',
                        'last_name': 'Administrator',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                        'password': make_password(password)
                    }
                )
                status = 'Created' if created else 'Updated'
                self.stdout.write(self.style.SUCCESS(f'  ✓ {status}: {email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed to create superuser: {str(e)}'))
            raise
    
    def create_test_schools(self, base_domain, minimal=False):
        """Create test schools with sample data"""
        self.stdout.write('\n🏫 [3/3] Creating Test Schools...')
        
        schools_data = [
            {
                'schema_name': 'greenvalley',
                'name': 'Green Valley High School',
                'short_name': 'greenvalley',     # Replaces slug
                'school_code': 'GVHS-001',       # New Required field
                'email': 'info@greenvalley.edu',
                'phone': '+1-555-0101',
                'address': '123 Education Lane, Springfield',
                'domain': f'greenvalley.{base_domain}',
            },
            {
                'schema_name': 'riverside',
                'name': 'Riverside Academy',
                'short_name': 'riverside',       # Replaces slug
                'school_code': 'RSA-002',        # New Required field
                'email': 'info@riverside.edu',
                'phone': '+1-555-0202',
                'address': '456 Learning Drive, Rivertown',
                'domain': f'riverside.{base_domain}',
            }
        ]
        
        for idx, school_data in enumerate(schools_data, 1):
            self.stdout.write(f'\n  School {idx}/2: {school_data["name"]}')
            self.create_school_with_users(school_data, minimal)
    
    def create_school_with_users(self, school_data, minimal=False):
        """Create a school with user accounts"""
        schema_name = school_data['schema_name']
        
        try:
            with transaction.atomic():
                # Note: We use update_or_create to allow re-running the script
                school, created = School.objects.update_or_create(
                    schema_name=schema_name,
                    defaults={
                        'name': school_data['name'],
                        'short_name': school_data['short_name'], # Replaces slug
                        'school_code': school_data['school_code'], # Required
                        'email': school_data['email'],
                        'phone': school_data.get('phone', ''),
                        'address': school_data.get('address', ''),
                        'is_active': True,
                    }
                )
                
                status = 'Created' if created else 'Updated'
                self.stdout.write(self.style.SUCCESS(f'    ✓ {status}: {school.name}'))
                
                domain, _ = Domain.objects.update_or_create(
                    tenant=school,
                    is_primary=True,
                    defaults={'domain': school_data['domain']}
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    ✗ Failed to create school: {str(e)}'))
            raise
        
        self.create_school_users(schema_name, school_data['name'], minimal)
    
    def create_school_users(self, schema_name, school_name, minimal=False):
        """Create user accounts for the school"""
        self.stdout.write(f'    Creating user accounts...')
        
        base_users = [
            {'email': f'admin@{schema_name}.edu', 'password': 'Admin123!', 'role': User.SCHOOL_ADMIN, 'display_name': 'Admin'},
        ]
        
        additional_users = [
            {'email': f'john@{schema_name}.edu', 'password': 'Teacher123!', 'role': User.TEACHER, 'display_name': 'John (Teacher)'},
            {'email': f'jane@{schema_name}.edu', 'password': 'Student123!', 'role': User.STUDENT, 'display_name': 'Jane (Student)'},
            {'email': f'mary@{schema_name}.edu', 'password': 'Parent123!', 'role': User.PARENT, 'display_name': 'Mary (Parent)'}
        ]
        
        users_data = base_users if minimal else base_users + additional_users
        
        with schema_context(schema_name):
            for user_data in users_data:
                try:
                    with transaction.atomic():
                        if user_data['role'] == User.SCHOOL_ADMIN:
                            create_func = User.objects.create_school_adminuser
                        elif user_data['role'] == User.TEACHER:
                            create_func = User.objects.create_teacheruser
                        elif user_data['role'] == User.STUDENT:
                            create_func = User.objects.create_studentuser
                        elif user_data['role'] == User.PARENT:
                            create_func = User.objects.create_parentuser
                        
                        self._get_or_create_user(create_func, user_data['email'], user_data['password'])
                        self.stdout.write(self.style.SUCCESS(f'      ✓ {user_data["display_name"]}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'      ✗ Failed {user_data["display_name"]}: {str(e)}'))

    def _get_or_create_user(self, create_method, email, password):
        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            return user, False
        except User.DoesNotExist:
            user = create_method(email=email, password=password)
            return user, True

    def print_summary(self, base_domain, minimal=False):
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(f'SETUP COMPLETE. Hosts file mappings for {base_domain}:'))
        self.stdout.write(f'127.0.0.1  {base_domain}')
        self.stdout.write(f'127.0.0.1  greenvalley.{base_domain}')
        self.stdout.write(f'127.0.0.1  riverside.{base_domain}')
        self.stdout.write('=' * 70)