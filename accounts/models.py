from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# ============================================================================
# SYSTEM USER (Public Schema)
# ============================================================================

class SystemUserManager(BaseUserManager):
    """Manager for system-wide administrators"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular system user"""
        if not email:
            raise ValueError(_('Email address is required'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with all permissions"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True'))
        
        return self.create_user(email, password, **extra_fields)


class SystemUser(AbstractBaseUser, PermissionsMixin):
    """
    System-wide administrator for platform management
    Stored in public schema only
    """
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
        error_messages={
            'unique': _('A user with this email already exists.'),
        }
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active.')
    )
    
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)
    
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="systemuser_set",
        related_query_name="system_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="systemuser_set",
        related_query_name="system_user",
    )
    
    objects = SystemUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('system user')
        verbose_name_plural = _('system users')
        db_table = 'system_users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between"""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email
    
    def get_short_name(self):
        """Return the short name for the user"""
        return self.first_name or self.email.split('@')[0]
    
    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)


# ============================================================================
# SCHOOL USER (Tenant Schema) - Base Authentication Model
# ============================================================================

class UserManager(BaseUserManager):
    """Manager for tenant-specific users"""
    
    def create_user(self, email, role, password=None, **extra_fields):
        """Create and return a school user with specified role"""
        if not email:
            raise ValueError(_('Email address is required'))
        if not role:
            raise ValueError(_('User role is required'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_school_adminuser(self, email, password=None, **extra_fields):
        """Create and return a school administrator"""
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, User.SCHOOL_ADMIN, password, **extra_fields)
    
    def create_teacheruser(self, email, password=None, **extra_fields):
        """Create and return a teacher user"""
        return self.create_user(email, User.TEACHER, password, **extra_fields)
    
    def create_studentuser(self, email, password=None, **extra_fields):
        """Create and return a student user"""
        return self.create_user(email, User.STUDENT, password, **extra_fields)
    
    def create_parentuser(self, email, password=None, **extra_fields):
        """Create and return a parent user"""
        return self.create_user(email, User.PARENT, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Base authentication model for tenant users
    Extended by Teacher, Student, and Parent models via OneToOne
    """
    # Role constants
    SCHOOL_ADMIN = 'school_admin'
    TEACHER = 'teacher'
    STUDENT = 'student'
    PARENT = 'parent'
    
    ROLE_CHOICES = [
        (SCHOOL_ADMIN, _('School Administrator')),
        (TEACHER, _('Teacher')),
        (STUDENT, _('Student')),
        (PARENT, _('Parent')),
    ]
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
        error_messages={
            'unique': _('A user with this email already exists.'),
        }
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=ROLE_CHOICES,
        db_index=True
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active.')
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="user_set",
        related_query_name="user",
    )
    
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email', 'role'], name='user_email_role_idx'),
            models.Index(fields=['role', 'is_active'], name='user_role_active_idx'),
        ]
    
    def __str__(self):
        return f'{self.email} ({self.get_role_display()})'
    
    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)
    
    def get_full_name(self):
        """Get full name from related profile"""
        profile = self.get_profile()
        return profile.get_full_name() if profile else self.email
    
    def get_short_name(self):
        """Get short name from related profile"""
        profile = self.get_profile()
        if profile and hasattr(profile, 'first_name'):
            return profile.first_name
        return self.email.split('@')[0]
    
    def get_profile(self):
        """Get the related profile object based on role"""
        profile_map = {
            self.TEACHER: 'teacher',
            self.STUDENT: 'student',
            self.PARENT: 'parent',
        }
        profile_attr = profile_map.get(self.role)
        return getattr(self, profile_attr, None) if profile_attr else None
    
    @property
    def is_staff(self):
        """School admins have staff privileges within their tenant"""
        return self.role == self.SCHOOL_ADMIN
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role
    
    # Role checking methods
    def is_school_admin(self):
        return self.role == self.SCHOOL_ADMIN
    
    def is_teacher(self):
        return self.role == self.TEACHER
    
    def is_student(self):
        return self.role == self.STUDENT
    
    def is_parent(self):
        return self.role == self.PARENT
