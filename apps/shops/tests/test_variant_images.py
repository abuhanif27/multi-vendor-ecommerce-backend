import tempfile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.models import Category
from apps.shops.models import Shop, Product, ProductVariant, VariantImage, ProductImage
from apps.shops.services.variant_images import VariantImageService

User = get_user_model()


class VariantImageViewsTest(APITestCase):
    def setUp(self):
        # Create Owner User
        self.owner_user = User.objects.create_user(
            email="owner@example.com",
            password="testpassword",
        )
        if hasattr(self.owner_user, 'role'):
            self.owner_user.role = "vendor"
            self.owner_user.save()

        self.shop = Shop.objects.create(
            owner=self.owner_user,
            name="Owner Shop",
            status=Shop.ShopStatus.APPROVED
        )
        self.category = Category.objects.create(
            name="Test Category",
        )
        self.product = Product.objects.create(
            shop=self.shop,
            category=self.category,
            name="Test Product",
            price=10.00,
            stock=10,
            status=Product.ProductStatus.ACTIVE
        )
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="TEST-SKU",
            price=15.00,
            stock=5,
        )

        self.image_create_url = reverse(
            "variant-image-create", 
            kwargs={
                "shop_slug": self.shop.slug,
                "product_slug": self.product.slug,
                "sku": self.variant.sku,
            }
        )

    def generate_image(self, name="test.jpg"):
        return SimpleUploadedFile(
            name,
            b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00eee,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif"
        )

    def test_create_variant_image(self):
        self.client.force_authenticate(user=self.owner_user)
        payload = {"image": self.generate_image()}
        
        response = self.client.post(self.image_create_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VariantImage.objects.count(), 1)
        
        img = VariantImage.objects.first()
        self.assertTrue(img.is_primary)
        self.assertEqual(img.display_order, 1)

    def test_variant_serializer_fallback_to_product_image(self):
        # Create product image
        prod_img = ProductImage.objects.create(
            product=self.product,
            image=self.generate_image("prod.jpg"),
            is_primary=True,
            display_order=1
        )
        
        variant_detail_url = reverse(
            "variant-detail", 
            kwargs={
                "shop_slug": self.shop.slug,
                "product_slug": self.product.slug,
                "sku": self.variant.sku,
            }
        )
        
        # When variant has NO images, it should fallback to product primary image
        response = self.client.get(variant_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn("images", data)
        self.assertEqual(len(data["images"]), 1)
        # Should be the product image
        self.assertEqual(data["images"][0]["id"], str(prod_img.id))
        
        # Now add a Variant Image
        var_img = VariantImageService.create(
            variant=self.variant,
            image=self.generate_image("var.jpg")
        )
        
        # When variant HAS images, it should return variant images
        response = self.client.get(variant_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn("images", data)
        self.assertEqual(len(data["images"]), 1)
        # Should be the variant image
        self.assertEqual(data["images"][0]["id"], str(var_img.id))
