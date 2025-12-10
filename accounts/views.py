# ============================================================================
# accounts/views.py
# ============================================================================

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import connection
from schools.models import School
from accounts.models import User


from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.db import connection
from schools.models import School
from accounts.models import User
from .forms import CustomAuthenticationForm # Import the custom form


def login_view(request):
    """Login view for tenant users, compatible with HTMX."""
    
    if connection.schema_name == 'public':
        return redirect('/admin/login/')
    
    if request.user.is_authenticated:
        return redirect(reverse('dashboard:main'))

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # For HTMX requests, send a redirect header
            if request.htmx:
                next_url = request.POST.get('next', reverse('dashboard:main'))
                response = HttpResponse()
                response['HX-Redirect'] = next_url
                return response
            
            # For standard requests, do a normal redirect
            next_url = request.POST.get('next') or request.GET.get('next', reverse('dashboard:main'))
            return redirect(next_url)
        else:
            # Form is invalid, re-render the form with errors
            # HTMX will swap this into the page
            return render(request, 'accounts/login.html', {'form': form})

    # For GET requests
    form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})




@login_required(login_url='accounts:login')
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required(login_url='accounts:login')
def dashboard(request):
    """Main dashboard - routes to role-specific dashboard"""
    
    user = request.user
    
    # Get school info
    try:
        school = School.objects.get(schema_name=connection.schema_name)
    except School.DoesNotExist:
        school = None
    
    # Get user profile
    profile = user.get_profile()
    
    context = {
        'user': user,
        'school': school,
        'profile': profile,
    }
    
    # Route to role-specific dashboard
    if user.is_school_admin():
        return render(request, 'accounts/dashboard_admin.html', context)
    elif user.is_teacher():
        return render(request, 'accounts/dashboard_teacher.html', context)
    elif user.is_student():
        return render(request, 'accounts/dashboard_student.html', context)
    elif user.is_parent():
        return render(request, 'accounts/dashboard_parent.html', context)
    
    # Fallback
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='accounts:login')
def profile_view(request):
    """View user profile"""
    
    user = request.user
    profile = user.get_profile()
    
    try:
        school = School.objects.get(schema_name=connection.schema_name)
    except School.DoesNotExist:
        school = None
    
    context = {
        'user': user,
        'school': school,
        'profile': profile,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='accounts:login')
def profile_edit(request):
    """Edit user profile (basic info only)"""
    
    user = request.user
    
    if request.method == 'POST':
        # Update basic user info
        # Note: Full profile editing should be in respective apps
        email = request.POST.get('email')
        
        if email and email != user.email:
            # Check if email already exists
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, 'This email is already in use.')
            else:
                user.email = email
                user.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('accounts:profile')
    
    context = {
        'user': user,
    }
    
    return render(request, 'accounts/profile_edit.html', context)


@login_required(login_url='accounts:login')
def change_password(request):
    """Change user password"""
    user = request.user
    is_forced = getattr(user, 'force_password_change', False)

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validate current password
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            # Update password
            user.set_password(new_password)

            # Clear force_password_change flag if it exists
            if hasattr(user, 'force_password_change'):
                user.force_password_change = False

            user.save()

            # Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)

            messages.success(request, 'Password changed successfully.')
            return redirect('dashboard:main')

    context = {
        'is_forced': is_forced,
    }
    return render(request, 'accounts/change_password.html', context)
