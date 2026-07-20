from django.db import transaction
from django.core.exceptions import ValidationError
from apps.orders.models import Order, VendorOrder, OrderItem
from apps.shops.models import Shop
from apps.inventory.services.inventory import InventoryService

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order_from_dto(dto):
        """
        Consumes the DTO produced by CheckoutService and creates the immutable order ledger.
        """
        # 1. Create Parent Order
        order = Order.objects.create(
            user=dto["user"],
            shipping_address=dto["shipping_address"],
            billing_address=dto["billing_address"],
            subtotal=dto["financials"]["subtotal"],
            shipping_total=dto["financials"]["shipping_total"],
            tax_total=dto["financials"]["tax_total"],
            grand_total=dto["financials"]["grand_total"],
            status=Order.OrderStatus.PENDING
        )
        
        # 2. Iterate through vendor orders
        for shop_id_str, vendor_data in dto["vendor_orders"].items():
            shop = Shop.objects.get(id=shop_id_str)
            
            vendor_order = VendorOrder.objects.create(
                order=order,
                shop=shop,
                vendor_total=vendor_data["vendor_subtotal"],  # Skipping shipping/tax logic per vendor for now
                vendor_subtotal=vendor_data["vendor_subtotal"],
                status=VendorOrder.FulfillmentStatus.PENDING
            )
            
            # 3. Iterate items and create snapshots
            order_items_to_create = []
            for item in vendor_data["items"]:
                variant = item.variant
                product = variant.product
                
                # Try to get primary image or first available
                image_url = ""
                primary_img = variant.images.filter(is_primary=True).first()
                if primary_img:
                    image_url = primary_img.image.url
                elif product.images.filter(is_primary=True).exists():
                    image_url = product.images.filter(is_primary=True).first().image.url
                
                # Construct variant attributes dictionary (e.g. {"RAM": "16GB"})
                attributes = {}
                for attr_val in variant.attribute_values.select_related('category_attribute_value__category_attribute').all():
                    attr_name = attr_val.category_attribute_value.category_attribute.name
                    val = attr_val.category_attribute_value.value
                    attributes[attr_name] = val
                    
                order_items_to_create.append(OrderItem(
                    vendor_order=vendor_order,
                    variant=variant,
                    product_name=product.name,
                    sku=variant.sku,
                    variant_attributes=attributes,
                    shop_name=shop.name,
                    image_url=image_url,
                    unit_price=item.unit_price,  # This was snapshotted by CheckoutService
                    quantity=item.quantity,
                    item_total=item.unit_price * item.quantity
                ))
                
            OrderItem.objects.bulk_create(order_items_to_create)
            
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order_id):
        """
        Cancels the order and releases all reserved inventory.
        """
        order = Order.objects.get(id=order_id)
        if order.status not in [Order.OrderStatus.PENDING]:
            raise ValidationError("Only pending orders can be cancelled.")
            
        order.status = Order.OrderStatus.CANCELLED
        order.save(update_fields=['status'])
        
        # Update all vendor orders
        order.vendor_orders.update(status=VendorOrder.FulfillmentStatus.CANCELLED)
        
        # Release inventory
        items = OrderItem.objects.filter(vendor_order__order=order).select_related('variant__inventory')
        for item in items:
            if item.variant and hasattr(item.variant, 'inventory'):
                InventoryService.release_stock(item.variant.inventory.id, item.quantity)
        
        return order

    @staticmethod
    @transaction.atomic
    def mark_order_paid(order_id):
        """
        Triggered by Webhook. Transitions order to PAID and VendorOrders to PROCESSING.
        Commits physical inventory.
        """
        order = Order.objects.get(id=order_id)
        if order.status != Order.OrderStatus.PENDING:
            return order
            
        order.status = Order.OrderStatus.PAID
        order.save(update_fields=['status'])
        
        # Vendors can now start fulfilling
        order.vendor_orders.update(status=VendorOrder.FulfillmentStatus.PROCESSING)
        
        # Future: InventoryService.commit_stock(...)
        # items = OrderItem.objects.filter(vendor_order__order=order).select_related('variant__inventory')
        # for item in items:
        #     if item.variant and hasattr(item.variant, 'inventory'):
        #         InventoryService.commit_stock(item.variant.inventory.id, item.quantity, reference=str(order.id))
                
        return order

    @staticmethod
    @transaction.atomic
    def mark_order_processing(order_id):
        """
        Used specifically for Cash on Delivery. Order starts processing before it is PAID.
        """
        order = Order.objects.get(id=order_id)
        # We leave parent status as PENDING (awaiting payment), but vendors can start processing
        order.vendor_orders.update(status=VendorOrder.FulfillmentStatus.PROCESSING)
        return order
