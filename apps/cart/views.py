from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from apps.cart.models import Cart
from apps.cart.serializers import (
    CartReadSerializer,
    CartItemWriteSerializer,
    CartItemUpdateSerializer,
)
from apps.cart.services.cart import CartService


class CartRetrieveAPIView(generics.RetrieveAPIView):
    """
    Retrieve the current user's active cart.
    """
    serializer_class = CartReadSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart = CartService.get_or_create_cart(self.request.user)
        # Prefetch to prevent N+1
        return Cart.objects.prefetch_related(
            'items__variant__product__shop',
            'items__variant__inventory'
        ).get(id=cart.id)


class CartItemCollectionAPIView(generics.GenericAPIView):
    """
    POST: Add an item to cart.
    DELETE: Clear all items in cart.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemWriteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        sku = serializer.validated_data["sku"]
        quantity = serializer.validated_data["quantity"]
        
        try:
            CartService.add_item(request.user, sku, quantity)
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        return Response({"detail": "Item added to cart."}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        CartService.clear_cart(request.user)
        return Response({"detail": "Cart cleared."}, status=status.HTTP_204_NO_CONTENT)


class CartItemDetailAPIView(generics.GenericAPIView):
    """
    PATCH: Update cart item quantity.
    DELETE: Remove cart item.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemUpdateSerializer

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quantity = serializer.validated_data["quantity"]
        item_id = self.kwargs["pk"]
        
        try:
            CartService.update_quantity(request.user, item_id, quantity)
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        return Response({"detail": "Cart item updated."}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        item_id = self.kwargs["pk"]
        try:
            CartService.remove_item(request.user, item_id)
        except DjangoValidationError as e:
            raise ValidationError({"detail": e.messages})
            
        return Response(status=status.HTTP_204_NO_CONTENT)
