# ============================================================================
# accounts/views.py
# ============================================================================

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponseForbidden
from tenants.models import School
from accounts.models import User


def login_view(request):
    """Login view for tenant users"""
    
    # Check if we're on public schema
    if connection.schema_name == 'public':
        # Redirect to admin login
        return redirect('/admin/login/')
    
    # Redirect if already authenticated
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    # Get current school info
    try:
        school = School.objects.get(schema_name=connection.schema_name)
    except School.DoesNotExist:
        school = None
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Set session expiry
            if not remember_me:
                request.session.set_expiry(0)  # Browser close
            else:
                request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(request, f'Welcome back, {user.email}!')
            
            # Redirect to next or dashboard
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    
    context = {
        'school': school,
    }
    
    return render(request, 'accounts/login.html', context)


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
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            # Update password
            request.user.set_password(new_password)
            request.user.save()
            
            # Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:profile')
    
    return render(request, 'accounts/change_password.html')
