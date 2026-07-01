from django.contrib.auth.models import AbstractUser
from apps.common.models import TimeStampedModel, UUIDModel


class User(UUIDModel, TimeStampedModel, AbstractUser):
    """
    Custom User model.
    We'll extend this later with UUID, email login, roles, etc.
    """
    pass
