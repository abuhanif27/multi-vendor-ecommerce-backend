from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from apps.shops.models import Shop, Product
from apps.shops.serializers import ShopSerializer, ProductSerializer
from apps.shops.permissions import IsProductOwner, IsVendor, IsShopOwner
from apps.shops.filters import ProductFilter

from apps.shops.schema.shops import (
    SHOP_LIST_SCHEMA,
    SHOP_DETAIL_SCHEMA,
    MY_SHOPS_SCHEMA,
)
from apps.shops.schema.products import (
    PRODUCT_LIST_SCHEMA,
    PRODUCT_DETAIL_SCHEMA,
    MY_PRODUCTS_SCHEMA,
)


@SHOP_LIST_SCHEMA
class ShopListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ShopSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsVendor()]

        return []

    def get_queryset(self):
        return (
            Shop.objects
            .filter(
                status=Shop.ShopStatus.APPROVED,
            )
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@SHOP_DETAIL_SCHEMA
class ShopDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShopSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [
                IsVendor(),
                IsShopOwner(),
            ]

        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        if self.request.method == "GET":
            return Shop.objects.filter(
                status=Shop.ShopStatus.APPROVED,
            )

        return Shop.objects.all()


@MY_SHOPS_SCHEMA
class MyShopListAPIView(generics.ListAPIView):
    serializer_class = ShopSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return (
            Shop.objects
            .filter(
                owner=self.request.user,
            )
        )


@PRODUCT_LIST_SCHEMA
class ProductListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = ProductFilter

    search_fields = ['name', 'description', 'shop__name', 'category__name']
    ordering_fields = ['price', 'created_at', 'name']

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsVendor()]
        return []

    def get_queryset(self):
        return (Product.objects
                .select_related('shop', 'category')
                .filter(status=Product.ProductStatus.ACTIVE, shop__status=Shop.ShopStatus.APPROVED)
                )


@PRODUCT_DETAIL_SCHEMA
class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects
            .select_related("shop", "category")
            .filter(
                status=Product.ProductStatus.ACTIVE,
                shop__status=Shop.ShopStatus.APPROVED,
            )
        )

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [
                IsVendor(),
                IsProductOwner(),
            ]

        return [IsAuthenticatedOrReadOnly()]


@MY_PRODUCTS_SCHEMA
class MyProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return (
            Product.objects
            .select_related("shop")
            .filter(
                shop__owner=self.request.user,
            )
        )
