from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Avg

from apps.reviews.models import ProductReview, ShopReview, ReviewStatus
from apps.shops.models import Product, Shop
from apps.orders.models import OrderItem, VendorOrder
from apps.notifications.events import EventBus
from apps.reviews.event_types import ProductReviewChangedEvent, ShopReviewChangedEvent

class ReviewService:
    @staticmethod
    @transaction.atomic
    def create_product_review(user, product_id, order_item_id, rating, comment=""):
        """
        Creates a product review. Enforces verified purchase constraints.
        """
        try:
            order_item = OrderItem.objects.select_related('vendor_order__order', 'variant__product').get(id=order_item_id)
        except OrderItem.DoesNotExist:
            raise ValidationError("Order item does not exist.")
            
        if order_item.vendor_order.order.user != user:
            raise ValidationError("You can only review items you purchased.")
            
        if order_item.vendor_order.status != VendorOrder.FulfillmentStatus.DELIVERED:
            raise ValidationError("You can only review items after the order is completed.")
            
        if str(order_item.variant.product.id) != str(product_id):
            raise ValidationError("Order item does not match the product being reviewed.")
            
        if hasattr(order_item, 'review'):
            raise ValidationError("You have already reviewed this item.")
            
        review = ProductReview.objects.create(
            user=user,
            product_id=product_id,
            order_item=order_item,
            rating=rating,
            comment=comment,
            status=ReviewStatus.PUBLISHED
        )
        
        # We publish the event AFTER the transaction commits successfully.
        transaction.on_commit(lambda: EventBus.publish(ProductReviewChangedEvent(product_id=product_id)))
        
        return review

    @staticmethod
    @transaction.atomic
    def update_product_review(user, review_id, rating=None, comment=None):
        try:
            review = ProductReview.objects.get(id=review_id)
        except ProductReview.DoesNotExist:
            raise ValidationError("Review does not exist.")
            
        if review.user != user:
            raise ValidationError("You can only edit your own reviews.")
            
        if rating is not None:
            review.rating = rating
        if comment is not None:
            review.comment = comment
            
        review.is_edited = True
        review.save(update_fields=['rating', 'comment', 'is_edited', 'updated_at'])
        
        transaction.on_commit(lambda: EventBus.publish(ProductReviewChangedEvent(product_id=review.product_id)))
        return review

    @staticmethod
    @transaction.atomic
    def delete_product_review(user, review_id):
        try:
            review = ProductReview.objects.get(id=review_id)
        except ProductReview.DoesNotExist:
            raise ValidationError("Review does not exist.")
            
        if review.user != user:
            raise ValidationError("You can only delete your own reviews.")
            
        product_id = review.product_id
        review.delete()
        
        transaction.on_commit(lambda: EventBus.publish(ProductReviewChangedEvent(product_id=product_id)))

    @staticmethod
    @transaction.atomic
    def create_shop_review(user, shop_id, vendor_order_id, rating, comment=""):
        """
        Creates a shop review. Enforces verified purchase constraints.
        """
        try:
            vendor_order = VendorOrder.objects.select_related('order', 'shop').get(id=vendor_order_id)
        except VendorOrder.DoesNotExist:
            raise ValidationError("Vendor order does not exist.")
            
        if vendor_order.order.user != user:
            raise ValidationError("You can only review shops you purchased from.")
            
        if vendor_order.status != VendorOrder.FulfillmentStatus.DELIVERED:
            raise ValidationError("You can only review shops after the order is completed.")
            
        if str(vendor_order.shop.id) != str(shop_id):
            raise ValidationError("Vendor order does not match the shop being reviewed.")
            
        if hasattr(vendor_order, 'review'):
            raise ValidationError("You have already reviewed this shop for this order.")
            
        review = ShopReview.objects.create(
            user=user,
            shop_id=shop_id,
            vendor_order=vendor_order,
            rating=rating,
            comment=comment,
            status=ReviewStatus.PUBLISHED
        )
        
        transaction.on_commit(lambda: EventBus.publish(ShopReviewChangedEvent(shop_id=shop_id)))
        
        return review

    @staticmethod
    @transaction.atomic
    def update_shop_review(user, review_id, rating=None, comment=None):
        try:
            review = ShopReview.objects.get(id=review_id)
        except ShopReview.DoesNotExist:
            raise ValidationError("Review does not exist.")
            
        if review.user != user:
            raise ValidationError("You can only edit your own reviews.")
            
        if rating is not None:
            review.rating = rating
        if comment is not None:
            review.comment = comment
            
        review.is_edited = True
        review.save(update_fields=['rating', 'comment', 'is_edited', 'updated_at'])
        
        transaction.on_commit(lambda: EventBus.publish(ShopReviewChangedEvent(shop_id=review.shop_id)))
        return review

    @staticmethod
    @transaction.atomic
    def delete_shop_review(user, review_id):
        try:
            review = ShopReview.objects.get(id=review_id)
        except ShopReview.DoesNotExist:
            raise ValidationError("Review does not exist.")
            
        if review.user != user:
            raise ValidationError("You can only delete your own reviews.")
            
        shop_id = review.shop_id
        review.delete()
        
        transaction.on_commit(lambda: EventBus.publish(ShopReviewChangedEvent(shop_id=shop_id)))
        
    @staticmethod
    def sync_product_rating(product_id):
        """
        Aggregates ratings for a product and updates the denormalized fields.
        Typically called by Celery tasks in response to a ProductReviewChangedEvent.
        """
        product = Product.objects.get(id=product_id)
        reviews = ProductReview.objects.filter(product=product, status=ReviewStatus.PUBLISHED)
        
        data = reviews.aggregate(avg_rating=Avg('rating'))
        
        product.review_count = reviews.count()
        product.average_rating = data['avg_rating'] or 0.00
        product.save(update_fields=['review_count', 'average_rating'])

    @staticmethod
    def sync_shop_rating(shop_id):
        """
        Aggregates ratings for a shop and updates the denormalized fields.
        """
        shop = Shop.objects.get(id=shop_id)
        reviews = ShopReview.objects.filter(shop=shop, status=ReviewStatus.PUBLISHED)
        
        data = reviews.aggregate(avg_rating=Avg('rating'))
        
        shop.review_count = reviews.count()
        shop.average_rating = data['avg_rating'] or 0.00
        shop.save(update_fields=['review_count', 'average_rating'])
