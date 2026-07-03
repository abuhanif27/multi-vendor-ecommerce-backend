from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

import secrets
from datetime import timedelta

from apps.accounts.choices import UserRole
from apps.accounts.managers import UserManager
from apps.common.models import TimeStampedModel, UUIDModel


class User(UUIDModel, TimeStampedModel, AbstractUser):
    """
    Custom User model for the marketplace.
    """

    username = None

    email = models.EmailField(
        unique=True,
        verbose_name="Email Address",
    )

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
    )

    is_verified = models.BooleanField(
        default=False,
        help_text="Designates whether the user's email has been verified.",
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()


class EmailVerificationToken(UUIDModel, TimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification",
    )

    token = models.CharField(
        max_length=128,
        unique=True,
        editable=False,
    )

    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(48)

        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)

        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"{self.user.email}"
