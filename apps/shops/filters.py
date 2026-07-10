import django_filters

from apps.shops.models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="exact",
    )

    shop = django_filters.CharFilter(
        field_name="shop__slug",
        lookup_expr="exact",
    )

    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
    )

    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
    )

    class Meta:
        model = Product
        fields = []
