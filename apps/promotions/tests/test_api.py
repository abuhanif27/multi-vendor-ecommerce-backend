from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.promotions.models import Promotion, PromotionStatus, Coupon, PromotionReward, RewardType
from apps.shops.models import Shop, Product, Category

User = get_user_model()

class PromotionAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="buyer@example.com", password="pwd")
        self.vendor = User.objects.create_user(email="vendor@example.com", password="pwd")
        self.shop = Shop.objects.create(owner=self.vendor, name="Vendor Shop")
        
        self.category = Category.objects.create(name="Shoes")
        self.product = Product.objects.create(shop=self.shop, category=self.category, name="Sneakers")
        
        # Vendor's promotion
        self.promo = Promotion.objects.create(
            name="Vendor Sale",
            status=PromotionStatus.ACTIVE,
            shop=self.shop,
            priority=10
        )
        PromotionReward.objects.create(
            promotion=self.promo,
            reward_type=RewardType.FIXED_AMOUNT,
            fixed_amount=Decimal('15.00')
        )
        self.coupon = Coupon.objects.create(
            promotion=self.promo,
            code="VENDOR15",
            max_uses=10,
            max_uses_per_user=1
        )
        
        self.client.force_authenticate(user=self.user)

    def test_validate_coupon_success(self):
        url = reverse('public-promotions-validate-cart')
        payload = {
            "subtotal": "100.00",
            "items": [
                {
                    "product_id": str(self.product.id),
                    "category_id": str(self.category.id),
                    "shop_id": str(self.shop.id),
                    "price": "100.00",
                    "quantity": 1
                }
            ],
            "coupon_codes": ["VENDOR15"]
        }
        
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(float(data["pricing"]["discount_total"]), 15.0)
        self.assertEqual(float(data["pricing"]["grand_total"]), 85.0)
        self.assertEqual(len(data["applied_promotions"]), 1)
        self.assertEqual(len(data["rejections"]), 0)

    def test_validate_coupon_invalid(self):
        url = reverse('public-promotions-validate-cart')
        payload = {
            "subtotal": "100.00",
            "items": [
                {
                    "product_id": str(self.product.id),
                    "category_id": str(self.category.id),
                    "shop_id": str(self.shop.id),
                    "price": "100.00",
                    "quantity": 1
                }
            ],
            "coupon_codes": ["FAKECODE"]
        }
        
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(float(data["pricing"]["discount_total"]), 0.0)
        self.assertEqual(len(data["applied_promotions"]), 0)
        self.assertEqual(len(data["rejections"]), 1)
        self.assertEqual(data["rejections"][0]["code"], "FAKECODE")
        self.assertEqual(data["rejections"][0]["reason_code"], "INVALID_CODE")

    def test_vendor_can_list_own_promotions(self):
        self.client.force_authenticate(user=self.vendor)
        url = reverse('admin-promotions-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['name'], "Vendor Sale")

    def test_buyer_cannot_access_admin_promotions(self):
        url = reverse('admin-promotions-list')
        response = self.client.get(url)
        # Assuming buyers don't have shops and aren't staff
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 0)
