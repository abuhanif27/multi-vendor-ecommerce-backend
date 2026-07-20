from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from apps.shops.models import Shop, Product
from apps.shops.serializers import ProductSerializer
from apps.common.pagination import DefaultPagination
from apps.shops.permissions import IsProductOwner, IsVendor
from apps.shops.filters import ProductFilter

from apps.shops.schema.products import (
    PRODUCT_LIST_SCHEMA,
    PRODUCT_DETAIL_SCHEMA,
    MY_PRODUCTS_SCHEMA,
)


@PRODUCT_LIST_SCHEMA
class ProductListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    pagination_class = DefaultPagination

    search_fields = ["name", "description", "shop__name", "category__name"]
    ordering_fields = ["price", "created_at", "name"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsVendor()]
        return []

    def get_queryset(self):
        return (Product.objects
                .select_related("shop", "category")
                .prefetch_related("images")
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
            .prefetch_related("images")
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
    permission_classes = [IsAuthenticated, IsVendor]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return (
            Product.objects
            .select_related("shop", "category")
            .prefetch_related("images")
            .filter(
                shop__owner=self.request.user,
            )
        )
