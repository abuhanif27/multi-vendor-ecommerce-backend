from apps.notifications.events import EventBus
from apps.reviews.event_types import ProductReviewChangedEvent, ShopReviewChangedEvent
from apps.reviews.tasks import sync_product_rating_task, sync_shop_rating_task

def handle_product_review_changed(event: ProductReviewChangedEvent):
    """
    Triggers the Celery task to recalculate the product rating.
    """
    sync_product_rating_task.delay(event.product_id)

def handle_shop_review_changed(event: ShopReviewChangedEvent):
    """
    Triggers the Celery task to recalculate the shop rating.
    """
    sync_shop_rating_task.delay(event.shop_id)

# Register handlers to the explicit EventBus
EventBus.subscribe(ProductReviewChangedEvent, handle_product_review_changed)
EventBus.subscribe(ShopReviewChangedEvent, handle_shop_review_changed)
