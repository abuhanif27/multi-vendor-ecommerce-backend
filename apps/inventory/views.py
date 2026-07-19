from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.common.mixins import ReadResponseMixin
from apps.shops.mixins import ProductLookupMixin
from apps.inventory.permissions import IsInventoryOwner
from apps.inventory.serializers import InventoryReadSerializer


class InventoryLookupMixin(ProductLookupMixin):
    def get_variant(self):
        product = self.get_product()
        sku = self.kwargs["sku"]
        return get_object_or_404(product.variants.select_related("inventory"), sku=sku)

    def get_object(self):
        variant = self.get_variant()
        obj = variant.inventory
        self.check_object_permissions(self.request, obj)
        return obj


class InventoryDetailAPIView(
    InventoryLookupMixin,
    ReadResponseMixin,
    generics.RetrieveAPIView,
):
    """
    Retrieve full inventory ledger for a variant.
    Accessible only to the shop owner.
    """
    serializer_class = InventoryReadSerializer
    permission_classes = [IsAuthenticated, IsInventoryOwner]

    def get_queryset(self):
        # The queryset is managed entirely by InventoryLookupMixin logic,
        # but DRF expects get_queryset to exist on generic views.
        from apps.inventory.models import Inventory
        return Inventory.objects.all()

