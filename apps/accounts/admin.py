from django.contrib import admin
from apps.accounts.models import User
# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email",)
    ordering = ("email",)
