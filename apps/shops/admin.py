from django.contrib import admin
from apps.shops.models import Shop
# Register your models here.


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "owner__username")
    select_related_fields = ("owner",)
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["owner"]
