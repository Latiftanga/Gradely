"""
Dashboard menu configuration
Define menu structure and role-based access control
"""

from accounts.models import User


# Dashboard menu structure
# Each menu section contains items with:
# - url_name: Django URL name (resolved via reverse())
# - label: Display text
# - icon: FontAwesome icon class
# - roles: List of user roles that can access this item
DASHBOARD_MENU = [
    {
        'title': 'Management',
        'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.STUDENT],
        'items': [
            {
                'url_name': 'dashboard:main_partial',
                'label': 'Dashboard',
                'icon': 'fa-tachometer-alt',
                'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.STUDENT],
                'push_url': '/'  # Override URL to push to browser
            },
            {
                'url_name': 'students:list',
                'label': 'Students',
                'icon': 'fa-users',
                'roles': [User.SCHOOL_ADMIN, User.TEACHER]
            },
            {
                'url_name': 'teachers:list',
                'label': 'Teachers',
                'icon': 'fa-chalkboard-teacher',
                'roles': [User.SCHOOL_ADMIN]
            },
            {
                'url_name': 'academics:classes',
                'label': 'Classes',
                'icon': 'fa-chalkboard',
                'roles': [User.SCHOOL_ADMIN, User.TEACHER]
            },
            {
                'url_name': 'academics:subjects',
                'label': 'Subjects',
                'icon': 'fa-book',
                'roles': [User.SCHOOL_ADMIN, User.TEACHER]
            },
            {
                'url_name': 'grades:assessment_list',
                'label': 'Assessments',
                'icon': 'fa-clipboard-list',
                'roles': [User.SCHOOL_ADMIN, User.TEACHER]
            },
        ]
    },
    {
        'title': 'Communication',
        'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.PARENT],
        'items': [
            # TODO: Implement announcements view
            # {
            #     'url_name': 'communication:announcements',
            #     'label': 'Announcements',
            #     'icon': 'fa-bullhorn',
            #     'roles': [User.SCHOOL_ADMIN, User.TEACHER]
            # },
            # TODO: Implement events view
            # {
            #     'url_name': 'communication:events',
            #     'label': 'Events',
            #     'icon': 'fa-calendar-alt',
            #     'roles': [User.SCHOOL_ADMIN, User.TEACHER, User.STUDENT, User.PARENT]
            # },
        ]
    },
    {
        'title': 'Settings',
        'roles': [User.SCHOOL_ADMIN],
        'items': [
            {
                'url_name': 'dashboard:settings',
                'label': 'School Settings',
                'icon': 'fa-cog',
                'roles': [User.SCHOOL_ADMIN]
            },
        ]
    },
]


def get_user_menu(user):
    """
    Get filtered menu items based on user role.

    Args:
        user: Django User instance with role attribute

    Returns:
        List of menu sections with items filtered by user role
    """
    if not user or not hasattr(user, 'role'):
        return []

    user_menu = []
    for section in DASHBOARD_MENU:
        # Check if user's role has access to the section
        if user.role in section['roles']:
            # Filter items within the section
            visible_items = [
                item for item in section['items']
                if user.role in item['roles']
            ]
            if visible_items:
                user_menu.append({
                    'title': section['title'],
                    'items': visible_items
                })

    return user_menu
