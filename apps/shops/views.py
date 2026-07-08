from rest_framework import generics

from apps.shops.models import Shop
from apps.shops.serializers import ShopSerializer
from apps.shops.permissions import IsVendor


class CreateShopAPIView(generics.CreateAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsVendor]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
