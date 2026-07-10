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

    class Meta:
        model = Product
        fields = ()
