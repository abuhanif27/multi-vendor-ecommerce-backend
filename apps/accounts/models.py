from django.contrib.auth.models import AbstractUser
from django.db import models

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

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()
