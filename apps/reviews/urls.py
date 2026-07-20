from rest_framework.routers import DefaultRouter
from apps.reviews.views import ProductReviewViewSet, ShopReviewViewSet

router = DefaultRouter()
router.register(r'product-reviews', ProductReviewViewSet, basename='product-review')
router.register(r'shop-reviews', ShopReviewViewSet, basename='shop-review')

urlpatterns = router.urls
