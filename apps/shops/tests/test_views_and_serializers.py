import tempfile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.models import Category
from apps.shops.models import Shop, Product, ProductImage
from apps.shops.services.product_images import ProductImageService

User = get_user_model()


class ProductImageViewsTest(APITestCase):
    def setUp(self):
        # Create Owner User
        self.owner_user = User.objects.create_user(
            email="owner@example.com",
            password="testpassword",
        )
        if hasattr(self.owner_user, 'role'):
            self.owner_user.role = "vendor"
            self.owner_user.save()

        # Create Other Vendor User
        self.other_vendor = User.objects.create_user(
            email="other@example.com",
            password="testpassword",
        )
        if hasattr(self.other_vendor, 'role'):
            self.other_vendor.role = "vendor"
            self.other_vendor.save()

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
            status=Product.ProductStatus.ACTIVE
        )

        self.image_create_url = reverse(
            "product-image-create", 
            kwargs={
                "shop_slug": self.shop.slug,
                "product_slug": self.product.slug,
            }
        )

    def generate_image(self, name="test.jpg"):
        return SimpleUploadedFile(name, b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00eee,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;", content_type="image/jpeg")

    def test_create_image_permissions(self):
        """
        Only the shop/product owner can upload an image.
        """
        payload = {
            "image": self.generate_image()
        }

        # 1. Unauthenticated -> 401
        response = self.client.post(self.image_create_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Other Vendor -> 403
        self.client.force_authenticate(user=self.other_vendor)
        payload["image"] = self.generate_image()
        response = self.client.post(self.image_create_url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Owner -> 201
        self.client.force_authenticate(user=self.owner_user)
        payload["image"] = self.generate_image()
        response = self.client.post(self.image_create_url, payload, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductImage.objects.count(), 1)
        
        # Verify it became primary
        img = ProductImage.objects.first()
        self.assertTrue(img.is_primary)

    def test_update_image(self):
        """
        Test that we can patch an image's alt_text and is_primary status.
        """
        img1 = ProductImageService.create(product=self.product, image=self.generate_image("1.jpg"))
        img2 = ProductImageService.create(product=self.product, image=self.generate_image("2.jpg"))

        detail_url = reverse(
            "product-image-detail", 
            kwargs={
                "shop_slug": self.shop.slug,
                "product_slug": self.product.slug,
                "pk": img2.id,
            }
        )

        self.client.force_authenticate(user=self.owner_user)

        payload = {
            "alt_text": "Updated Alt",
            "is_primary": True
        }
        response = self.client.patch(detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        img1.refresh_from_db()
        img2.refresh_from_db()

        self.assertEqual(img2.alt_text, "Updated Alt")
        self.assertTrue(img2.is_primary)
        self.assertFalse(img1.is_primary)

    def test_delete_image(self):
        """
        Test deleting an image through the detail endpoint.
        """
        img1 = ProductImageService.create(product=self.product, image=self.generate_image("1.jpg"))

        detail_url = reverse(
            "product-image-detail", 
            kwargs={
                "shop_slug": self.shop.slug,
                "product_slug": self.product.slug,
                "pk": img1.id,
            }
        )

        self.client.force_authenticate(user=self.owner_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProductImage.objects.count(), 0)

    def test_product_serializer_embeds_images(self):
        """
        Test that calling the product detail GET endpoint includes the 'images' field.
        """
        img1 = ProductImageService.create(product=self.product, image=self.generate_image("1.jpg"))
        img2 = ProductImageService.create(product=self.product, image=self.generate_image("2.jpg"))

        product_detail_url = reverse("product-detail", kwargs={"slug": self.product.slug})

        response = self.client.get(product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn("images", data)
        self.assertEqual(len(data["images"]), 2)
        
        # Verify nested fields
        self.assertEqual(data["images"][0]["display_order"], 1)
        self.assertEqual(data["images"][1]["display_order"], 2)
        self.assertTrue(data["images"][0]["is_primary"])
