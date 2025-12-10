from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.template import Context, Template

from students.models import Student
from teachers.models import Teacher
from academics.models import Class, AcademicYear, GradeLevel
from dashboard.menu_config import get_user_menu
from dashboard.templatetags.dashboard_tags import is_safe_url

User = get_user_model()


class DashboardViewTests(TestCase):
    """Tests for dashboard views"""

    def setUp(self):
        """Set up test user and data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            role=User.SCHOOL_ADMIN,
            password='testpass123'
        )

    def test_dashboard_view_requires_login(self):
        """Test that dashboard view requires authentication"""
        response = self.client.get(reverse('dashboard:main'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)

    def test_dashboard_view_loads_for_authenticated_user(self):
        """Test that dashboard loads for authenticated user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')

    def test_main_partial_view_requires_login(self):
        """Test that main partial view requires authentication"""
        response = self.client.get(reverse('dashboard:main_partial'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_main_partial_view_loads_with_statistics(self):
        """Test that main partial view loads with real statistics"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:main_partial'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/dashboard_main.html')
        # Check context contains expected variables
        self.assertIn('total_students', response.context)
        self.assertIn('total_teachers', response.context)
        self.assertIn('total_classes', response.context)
        self.assertIn('breadcrumbs', response.context)

    def test_main_partial_view_with_data(self):
        """Test statistics calculation with actual data"""
        # Create test data
        student_user = User.objects.create_user(
            email='student@example.com',
            role=User.STUDENT,
            password='testpass'
        )
        Student.objects.create(
            user=student_user,
            first_name='John',
            last_name='Doe',
            student_id='STU001',
            date_of_birth='2005-01-01',
            gender='M',
            is_active=True
        )

        teacher_user = User.objects.create_user(
            email='teacher@example.com',
            role=User.TEACHER,
            password='testpass'
        )
        Teacher.objects.create(
            user=teacher_user,
            first_name='Jane',
            last_name='Smith',
            staff_id='TCH001',
            date_employed='2020-01-01',
            is_active=True
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:main_partial'))

        # Verify statistics
        self.assertEqual(response.context['total_students'], 1)
        self.assertEqual(response.context['total_teachers'], 1)
        self.assertEqual(response.context['male_count'], 1)
        self.assertEqual(response.context['female_count'], 0)

    def test_main_partial_handles_errors_gracefully(self):
        """Test that view handles errors gracefully"""
        self.client.force_login(self.user)
        # Even with no data, view should not crash
        response = self.client.get(reverse('dashboard:main_partial'))
        self.assertEqual(response.status_code, 200)


class MenuConfigTests(TestCase):
    """Tests for menu configuration"""

    def setUp(self):
        """Set up test users with different roles"""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            role=User.SCHOOL_ADMIN,
            password='testpass'
        )
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            role=User.TEACHER,
            password='testpass'
        )
        self.student_user = User.objects.create_user(
            email='student@example.com',
            role=User.STUDENT,
            password='testpass'
        )

    def test_admin_gets_full_menu(self):
        """Test that admin users get appropriate menu items"""
        menu = get_user_menu(self.admin_user)
        self.assertGreater(len(menu), 0)
        # Admin should see Management section
        section_titles = [section['title'] for section in menu]
        self.assertIn('Management', section_titles)

    def test_teacher_gets_filtered_menu(self):
        """Test that teacher users get filtered menu"""
        menu = get_user_menu(self.teacher_user)
        self.assertGreater(len(menu), 0)

    def test_student_gets_limited_menu(self):
        """Test that student users get limited menu"""
        menu = get_user_menu(self.student_user)
        self.assertGreater(len(menu), 0)

    def test_no_user_returns_empty_menu(self):
        """Test that no user returns empty menu"""
        menu = get_user_menu(None)
        self.assertEqual(len(menu), 0)

    def test_user_without_role_returns_empty_menu(self):
        """Test that user without role attribute returns empty menu"""
        class FakeUser:
            pass
        fake_user = FakeUser()
        menu = get_user_menu(fake_user)
        self.assertEqual(len(menu), 0)


class TemplateTagTests(TestCase):
    """Tests for custom template tags"""

    def test_is_safe_url_filter_allows_relative_urls(self):
        """Test that is_safe_url allows relative URLs"""
        self.assertTrue(is_safe_url('/dashboard/'))
        self.assertTrue(is_safe_url('/students/list/'))

    def test_is_safe_url_filter_blocks_javascript(self):
        """Test that is_safe_url blocks javascript: scheme"""
        self.assertFalse(is_safe_url('javascript:alert(1)'))
        self.assertFalse(is_safe_url('JavaScript:alert(1)'))

    def test_is_safe_url_filter_blocks_data_urls(self):
        """Test that is_safe_url blocks data: scheme"""
        self.assertFalse(is_safe_url('data:text/html,<script>alert(1)</script>'))

    def test_is_safe_url_filter_blocks_external_urls(self):
        """Test that is_safe_url blocks external URLs"""
        self.assertFalse(is_safe_url('http://evil.com'))
        self.assertFalse(is_safe_url('https://evil.com'))
        self.assertFalse(is_safe_url('//evil.com'))

    def test_is_safe_url_filter_handles_empty_urls(self):
        """Test that is_safe_url handles empty/None URLs"""
        self.assertFalse(is_safe_url(''))
        self.assertFalse(is_safe_url(None))

    def test_sidebar_menu_tag_renders_for_authenticated_user(self):
        """Test that sidebar menu tag renders correctly"""
        user = User.objects.create_user(
            email='test@example.com',
            role=User.SCHOOL_ADMIN,
            password='testpass'
        )

        template = Template(
            "{% load dashboard_tags %}{% user_sidebar_menu %}"
        )
        context = Context({'user': user})
        output = template.render(context)

        # Should contain menu structure
        self.assertIn('Management', output)


class StatisticsCalculationTests(TestCase):
    """Tests for statistics calculations"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='admin@example.com',
            role=User.SCHOOL_ADMIN,
            password='testpass'
        )

    def test_gender_distribution_calculation(self):
        """Test that gender distribution is calculated correctly"""
        # Create male students
        for i in range(3):
            user = User.objects.create_user(
                email=f'male{i}@example.com',
                role=User.STUDENT,
                password='testpass'
            )
            Student.objects.create(
                user=user,
                first_name=f'Male{i}',
                last_name='Student',
                student_id=f'M{i:03d}',
                date_of_birth='2005-01-01',
                gender='M',
                is_active=True
            )

        # Create female students
        for i in range(2):
            user = User.objects.create_user(
                email=f'female{i}@example.com',
                role=User.STUDENT,
                password='testpass'
            )
            Student.objects.create(
                user=user,
                first_name=f'Female{i}',
                last_name='Student',
                student_id=f'F{i:03d}',
                date_of_birth='2005-01-01',
                gender='F',
                is_active=True
            )

        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:main_partial'))

        self.assertEqual(response.context['male_count'], 3)
        self.assertEqual(response.context['female_count'], 2)
        self.assertEqual(response.context['male_percentage'], 60.0)
        self.assertEqual(response.context['female_percentage'], 40.0)

    def test_empty_statistics(self):
        """Test that statistics handle empty data correctly"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:main_partial'))

        self.assertEqual(response.context['total_students'], 0)
        self.assertEqual(response.context['total_teachers'], 0)
        self.assertEqual(response.context['total_classes'], 0)
        self.assertEqual(response.context['male_percentage'], 0)
        self.assertEqual(response.context['female_percentage'], 0)
