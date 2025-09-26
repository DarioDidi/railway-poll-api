# users/models.py
from django.contrib.auth.models import (UserManager, AbstractUser,
                                        Group, Permission)
import uuid
from django.db import models
from django.utils import timezone


class CustomerUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create a new user profile"""
        if not email:
            raise ValueError('User must have an email address')

        email = self.normalize_email(email)
        if 'username' not in extra_fields:
            extra_fields['username'] = self.generate_unique_username(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, email, password=None,
                         username='Super', **extra_fields):
        return super().create_superuser(
            email=email, password=password, username='super', **extra_fields)

    @classmethod
    def normalize_email(cls, email):
        """Normalize the email address by lowercasing both parts"""
        email = email or ''
        try:
            email_name, domain_part = email.strip().rsplit('@', 1)
        except ValueError:
            pass
        else:
            email = '@'.join([email_name.lower(), domain_part.lower()])
        return email

    @classmethod
    def generate_unique_username(cls, email):
        """Generate a unique username from email"""
        base_username = email.split('@')[0]
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username


class User(AbstractUser):
    """Custom user model extending Django's
     AbstractUser with UUID primary key."""
    objects = CustomerUserManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_email_sent = models.DateTimeField(null=True, blank=True)

    username = models.CharField(max_length=150, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

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

    def save(self, *args, **kwargs):
        """Auto-generate username if not provided"""
        if not self.username:
            self.username = CustomerUserManager.generate_unique_username(
                self.email)
        super().save(*args, **kwargs)


class EmailVerificationToken(models.Model):
    """Model to track email verification tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(hours=24)


class PasswordResetToken(models.Model):
    """Model to track password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(hours=1)
