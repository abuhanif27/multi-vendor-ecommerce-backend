from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from apps.shops.mixins import ProductLookupMixin
from apps.inventory.permissions import IsInventoryOwner
from apps.inventory.serializers import (
    InventoryReadSerializer,
    InventoryActionSerializer,
    InventoryTransactionSerializer,
)
from apps.inventory.services import InventoryService


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

class InventoryTransactionListCreateAPIView(InventoryLookupMixin, generics.ListCreateAPIView):
    """
    List history of inventory transactions or create a new transaction (increase, decrease, adjust).
    """
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsAuthenticated, IsInventoryOwner]

    def get_queryset(self):
        inventory = self.get_object()
        return inventory.transactions.all().order_by("-created_at")

    def create(self, request, *args, **kwargs):
        inventory = self.get_object()
        action_serializer = InventoryActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        
        action = action_serializer.validated_data["action"]
        quantity = action_serializer.validated_data["quantity"]
        note = action_serializer.validated_data.get("note", "")
        reference = action_serializer.validated_data.get("reference", "")
        user = request.user
        
        try:
            if action == "increase":
                InventoryService.increase_stock(inventory.id, quantity, user, note, reference)
            elif action == "decrease":
                InventoryService.decrease_stock(inventory.id, quantity, user, note, reference)
            elif action == "adjust":
                InventoryService.adjust_stock(inventory.id, quantity, user, note, reference)
        except Exception as e:
            from django.core.exceptions import ValidationError as DjangoValidationError
            from rest_framework.exceptions import ValidationError
            if isinstance(e, DjangoValidationError):
                raise ValidationError({"detail": e.messages})
            raise
            
        # Returning the latest transaction created
        transaction = inventory.transactions.latest("created_at")
        serializer = self.get_serializer(transaction)
        from rest_framework.response import Response
        return Response(serializer.data, status=201)

