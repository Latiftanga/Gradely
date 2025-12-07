from django import template
from accounts.models import User # Import the tenant User model

register = template.Library()

@register.inclusion_tag('dashboard/partials/navbar.html', takes_context=True)
def user_navbar(context):
    """
    Custom template tag to render the main navbar.
    """
    return {
        'user': context.get('user'),
        'tenant': context.get('tenant'),
    }


@register.inclusion_tag('dashboard/partials/sidebar_menu.html', takes_context=True)
def user_sidebar_menu(context):
    """
    Custom template tag to render the sidebar menu based on user role.
    """
    user = context.get('user')
    if not user:
        return {'menu_items': []}

    # Define all possible menu items with associated roles
    all_menu_items = [
        {
            'title': 'Management',
            'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.STUDENT],
            'items': [
                {'url_name': 'dashboard:main_partial', 'label': 'Dashboard', 'icon': 'fa-tachometer-alt', 'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.STUDENT]},
                {'url_name': 'students:list', 'label': 'Students', 'icon': 'fa-users', 'roles': [User.SCHOOL_ADMIN, User.TEACHER]},
                {'url_name': '#', 'label': 'Teachers', 'icon': 'fa-chalkboard-teacher', 'roles': [User.SCHOOL_ADMIN]},
                {'url_name': '#', 'label': 'Classes', 'icon': 'fa-school', 'roles': [User.SCHOOL_ADMIN, User.TEACHER]},
                {'url_name': '#', 'label': 'Subjects', 'icon': 'fa-book', 'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.STUDENT]},
                {'url_name': '#', 'label': 'Grades', 'icon': 'fa-clipboard-list', 'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.STUDENT]},
            ]
        },
        {
            'title': 'Communication',
            'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.PARENT],
            'items': [
                {'url_name': '#', 'label': 'Announcements', 'icon': 'fa-bullhorn', 'roles': [User.SCHOOL_ADMIN, User.TEACHER]},
                {'url_name': '#', 'label': 'Events', 'icon': 'fa-calendar-alt', 'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.STUDENT, User.PARENT]},
            ]
        },
    ]

    # Filter menu sections and items based on the user's role
    user_menu = []
    for section in all_menu_items:
        # Check if user's role has access to the section
        if hasattr(user, 'role') and user.role in section['roles']:
            # Filter items within the section
            visible_items = [item for item in section['items'] if user.role in item['roles']]
            if visible_items:
                user_menu.append({
                    'title': section['title'],
                    'items': visible_items
                })
    
    return {'user_menu': user_menu}

