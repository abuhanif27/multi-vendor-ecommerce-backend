from apps.shops.permissions import IsProductOwner, IsVendor
from apps.shops.serializers import ShopSerializer, ProductSerializer
from apps.shops.models import Shop, Product
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly


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


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related("shop")
    serializer_class = ProductSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsVendor(), IsProductOwner()]
        return [IsAuthenticatedOrReadOnly()]
