from celery import shared_task
import logging
from apps.reviews.services.review import ReviewService
from apps.shops.models import Product, Shop

logger = logging.getLogger(__name__)

@shared_task
def sync_product_rating_task(product_id):
    """
    Asynchronously aggregates the reviews for a product and updates the denormalized metrics.
    """
    try:
        ReviewService.sync_product_rating(product_id)
        logger.info(f"Successfully synced rating for Product {product_id}")
    except Exception as e:
        logger.error(f"Failed to sync rating for Product {product_id}: {str(e)}")
        raise e

@shared_task
def sync_shop_rating_task(shop_id):
    """
    Asynchronously aggregates the reviews for a shop and updates the denormalized metrics.
    """
    try:
        ReviewService.sync_shop_rating(shop_id)
        logger.info(f"Successfully synced rating for Shop {shop_id}")
    except Exception as e:
        logger.error(f"Failed to sync rating for Shop {shop_id}: {str(e)}")
        raise e

@shared_task
def true_up_all_ratings_task():
    """
    Nightly reconciliation task. Re-calculates all published ratings from scratch 
    to fix any mathematical drift caused by race conditions during the day.
    """
    products = Product.objects.all().values_list('id', flat=True)
    for p_id in products:
        sync_product_rating_task.delay(p_id)
        
    shops = Shop.objects.all().values_list('id', flat=True)
    for s_id in shops:
        sync_shop_rating_task.delay(s_id)
        
    logger.info("true_up_all_ratings_task triggered sync jobs for all products and shops.")
