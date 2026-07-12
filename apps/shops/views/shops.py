from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from apps.common.permissions import IsVendor
from apps.shops.models import Shop
from apps.shops.permissions import IsShopOwner
from apps.shops.schema.shops import (
    SHOP_LIST_SCHEMA,
    SHOP_DETAIL_SCHEMA,
    MY_SHOPS_SCHEMA,
)


from apps.shops.serializers import ShopSerializer


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
