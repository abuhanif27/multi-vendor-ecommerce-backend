from rest_framework import generics

from apps.shops.models import Shop, Product
from apps.shops.serializers import ShopSerializer, ProductSerializer
from apps.shops.permissions import IsVendor


class CreateShopAPIView(generics.CreateAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsVendor]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProductListCreateApiView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsVendor()]
        return []

    def get_queryset(self):
        return (Product.objects
                .select_related('shop')
                .filter(status=Product.ProductStatus.ACTIVE, shop__status=Shop.ShopStatus.APPROVED)
                )


class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects
            .select_related("shop")
            .filter(
                status=Product.ProductStatus.ACTIVE,
                shop__status=Shop.ShopStatus.APPROVED,
            )
        )
