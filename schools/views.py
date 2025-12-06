from django.shortcuts import render
from .models import School

def school_dashboard(request):
    total_schools = School.objects.count()
    active_schools = School.objects.filter(is_active=True).count()
    inactive_schools = total_schools - active_schools
    schools = School.objects.all()

    context = {
        'total_schools': total_schools,
        'active_schools': active_schools,
        'inactive_schools': inactive_schools,
        'schools': schools,
    }
    return render(request, 'schools/dashboard.html', context)