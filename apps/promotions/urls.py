from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.promotions.views import PromotionViewSet, PublicPromotionViewSet

router = DefaultRouter()
router.register(r'admin/promotions', PromotionViewSet, basename='admin-promotions')
router.register(r'promotions', PublicPromotionViewSet, basename='public-promotions')

urlpatterns = [
    path('', include(router.urls)),
]
