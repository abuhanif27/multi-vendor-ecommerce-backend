from django.db import models
from django.conf import settings
from apps.common.models import UUIDModel, TimeStampedModel
from apps.shops.models import Shop, Product
from apps.orders.models import OrderItem, VendorOrder
from django.core.validators import MinValueValidator, MaxValueValidator

class ReviewStatus(models.TextChoices):
    PUBLISHED = 'PUBLISHED', 'Published'
    HIDDEN = 'HIDDEN', 'Hidden'
    REMOVED = 'REMOVED', 'Removed by Admin'

class MediaType(models.TextChoices):
    IMAGE = 'IMAGE', 'Image'
    VIDEO = 'VIDEO', 'Video'

class ProductReview(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.OneToOneField(OrderItem, on_delete=models.PROTECT, related_name='review')
    
    rating = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PUBLISHED)
    is_edited = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['product', 'status', '-created_at']),
        ]

    def __str__(self):
        return f"Review by {self.user.email} on {self.product.name}"

class ProductReviewMedia(UUIDModel, TimeStampedModel):
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='media')
    file_url = models.URLField(max_length=1000)
    media_type = models.CharField(max_length=10, choices=MediaType.choices, default=MediaType.IMAGE)

    def __str__(self):
        return f"Media for ProductReview {self.review.id}"

class ShopReview(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shop_reviews')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='reviews')
    vendor_order = models.OneToOneField(VendorOrder, on_delete=models.PROTECT, related_name='review')
    
    rating = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PUBLISHED)
    is_edited = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['shop', 'status', '-created_at']),
        ]

    def __str__(self):
        return f"Review by {self.user.email} on Shop {self.shop.name}"

class ShopReviewMedia(UUIDModel, TimeStampedModel):
    review = models.ForeignKey(ShopReview, on_delete=models.CASCADE, related_name='media')
    file_url = models.URLField(max_length=1000)
    media_type = models.CharField(max_length=10, choices=MediaType.choices, default=MediaType.IMAGE)

    def __str__(self):
        return f"Media for ShopReview {self.review.id}"

class ProductReviewReport(UUIDModel, TimeStampedModel):
    """
    Allows users to report abusive product reviews.
    """
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name="reports")
    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['review', 'is_resolved']),
        ]

    def __str__(self):
        return f"Report on ProductReview {self.review_id}"

class ShopReviewReport(UUIDModel, TimeStampedModel):
    """
    Allows users to report abusive shop reviews.
    """
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey(ShopReview, on_delete=models.CASCADE, related_name="reports")
    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['review', 'is_resolved']),
        ]

    def __str__(self):
        return f"Report on ShopReview {self.review_id}"
