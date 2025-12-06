# tenants/management/commands/create_school.py
# Quick command to create a single school

from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import School, Domain


class Command(BaseCommand):
    help = 'Create a new school (tenant)'
    
    def add_arguments(self, parser):
        parser.add_argument('--name', required=True, help='School name')
        parser.add_argument('--slug', required=True, help='School slug (schema name)')
        parser.add_argument('--domain', required=True, help='Domain (e.g., school.localhost)')
        parser.add_argument('--email', required=True, help='Contact email')
        parser.add_argument('--phone', default='', help='Phone number')
    
    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Create school
                school = School.objects.create(
                    schema_name=options['slug'],
                    name=options['name'],
                    slug=options['slug'],
                    email=options['email'],
                    phone=options['phone'],
                    is_active=True
                )
                
                # Create domain
                domain = Domain.objects.create(
                    domain=options['domain'],
                    tenant=school,
                    is_primary=True
                )
                
                self.stdout.write(self.style.SUCCESS(f'✓ School created: {school.name}'))
                self.stdout.write(self.style.SUCCESS(f'✓ Schema: {school.schema_name}'))
                self.stdout.write(self.style.SUCCESS(f'✓ Domain: {domain.domain}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {str(e)}'))
