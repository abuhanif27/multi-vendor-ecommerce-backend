from django.contrib.auth.models import AbstractUser
from apps.common.models import TimeStampedModel


class User(TimeStampedModel, AbstractUser):
    """
    Custom User model.
    We'll extend this later with UUID, email login, roles, etc.
    """
    pass
