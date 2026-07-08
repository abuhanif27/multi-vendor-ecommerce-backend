from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.shops.models import Shop
from apps.shops.serializers import ShopSerializer


class CreateShopAPIView(generics.CreateAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
