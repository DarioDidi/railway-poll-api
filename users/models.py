import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import UserManager


class CustomerUserManager(UserManager):

    def create_user(self, email, password=None):
        """Create a new user profile"""
        if not email:
            raise ValueError('User must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self.db)
        return user


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser with UUID primary key.
    """
    objects = CustomerUserManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    username = None  # use email for auth

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Add related_name to avoid clashes with built-in User model
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_permissions_set',
        related_query_name='user',
    )

    def __str__(self):
        return self.email
