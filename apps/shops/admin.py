from django.contrib import admin
from apps.shops.models import Shop
# Register your models here.


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    readonly_fields = ("slug", )
