from django.contrib import admin
from apps.shops.models import Shop, Product, ProductImage
# Register your models here.


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    readonly_fields = ("slug", )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    readonly_fields = ("slug", )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    pass
