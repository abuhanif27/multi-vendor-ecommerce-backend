from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model.
    We'll extend this later with UUID, email login, roles, etc.
    """
    pass
