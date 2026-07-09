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


class CreateProductAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.select_related('shop').filter(status=Product.ProductStatus.ACTIVE, shop__status=Shop.ShopStatus.APPROVED)
