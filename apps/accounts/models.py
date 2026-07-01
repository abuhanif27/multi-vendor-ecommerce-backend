from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.common.models import TimeStampedModel, UUIDModel
from apps.accounts.choices import UserRole


class User(UUIDModel, TimeStampedModel, AbstractUser):
    """
    Custom User model.
    """
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
    )
