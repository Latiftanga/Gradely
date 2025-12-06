from django.shortcuts import render
from .models import School

def school_dashboard(request):
    # Exclude the public schema from the list of schools
    schools = School.objects.exclude(schema_name='public')
    
    total_schools = schools.count()
    active_schools = schools.filter(is_active=True).count()
    inactive_schools = total_schools - active_schools

    context = {
        'total_schools': total_schools,
        'active_schools': active_schools,
        'inactive_schools': inactive_schools,
        'schools': schools,
    }
    return render(request, 'schools/dashboard.html', context)