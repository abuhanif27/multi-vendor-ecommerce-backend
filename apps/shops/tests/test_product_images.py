import tempfile
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.models import Category
from apps.shops.models import Shop, Product, ProductImage
from apps.shops.services.product_images import ProductImageService

User = get_user_model()


class ProductImageBaseTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="vendor@example.com",
            password="testpassword",
        )
        # Setup role if it exists, but typically creating user is enough
        if hasattr(self.user, 'role'):
            self.user.role = "vendor"
            self.user.save()

        self.shop = Shop.objects.create(
            owner=self.user,
            name="Test Shop",
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

    def generate_image(self, name="test.jpg"):
        return SimpleUploadedFile(name, b"file_content", content_type="image/jpeg")


class ProductImageModelTest(ProductImageBaseTest):
    def test_product_image_creation_and_str(self):
        """
        Test that we can create a product image, and its string representation
        contains the product name and display order.
        """
        image = ProductImage.objects.create(
            product=self.product,
            image=self.generate_image(),
            display_order=1,
            is_primary=True,
        )
        self.assertEqual(str(image), "Test Product - Image 1")
        self.assertTrue(image.is_primary)
        self.assertEqual(image.display_order, 1)

class ProductImageServiceTest(ProductImageBaseTest):
    def test_create_image_auto_primary(self):
        """
        Test that the first created image automatically becomes primary.
        """
        image1 = ProductImageService.create(
            product=self.product,
            image=self.generate_image("1.jpg")
        )
        self.assertTrue(image1.is_primary)
        self.assertEqual(image1.display_order, 1)

        # Second image shouldn't be primary, should have display_order 2
        image2 = ProductImageService.create(
            product=self.product,
            image=self.generate_image("2.jpg")
        )
        self.assertFalse(image2.is_primary)
        self.assertEqual(image2.display_order, 2)

    def test_update_image(self):
        """
        Test updating an image's alt text.
        """
        image = ProductImageService.create(
            product=self.product,
            image=self.generate_image()
        )
        updated_image = ProductImageService.update(
            product_image=image,
            alt_text="New Alt Text"
        )
        self.assertEqual(updated_image.alt_text, "New Alt Text")

    def test_delete_image_shifts_display_order(self):
        """
        Test that deleting an image correctly shifts the display orders of subsequent images
        to close any gaps.
        """
        img1 = ProductImageService.create(product=self.product, image=self.generate_image("1.jpg"))
        img2 = ProductImageService.create(product=self.product, image=self.generate_image("2.jpg"))
        img3 = ProductImageService.create(product=self.product, image=self.generate_image("3.jpg"))
        
        # Delete middle image
        ProductImageService.delete(product_image=img2)

        img1.refresh_from_db()
        img3.refresh_from_db()

        self.assertEqual(img1.display_order, 1)
        self.assertEqual(img3.display_order, 2)  # Shifted from 3 to 2

    def test_delete_primary_image_reassigns_primary(self):
        """
        Test that deleting the primary image reassigns the primary status
        to the next available image (lowest display order).
        """
        img1 = ProductImageService.create(product=self.product, image=self.generate_image("1.jpg"))
        img2 = ProductImageService.create(product=self.product, image=self.generate_image("2.jpg"))
        
        self.assertTrue(img1.is_primary)

        ProductImageService.delete(product_image=img1)

        img2.refresh_from_db()
        self.assertTrue(img2.is_primary)
        self.assertEqual(img2.display_order, 1) # Shifted up

    def test_set_primary(self):
        """
        Test setting an image as primary correctly un-sets the previous primary image.
        """
        img1 = ProductImageService.create(product=self.product, image=self.generate_image("1.jpg"))
        img2 = ProductImageService.create(product=self.product, image=self.generate_image("2.jpg"))

        ProductImageService.set_primary(product_image=img2)

        img1.refresh_from_db()
        img2.refresh_from_db()

        self.assertFalse(img1.is_primary)
        self.assertTrue(img2.is_primary)

    def test_reorder_images(self):
        """
        Test reordering images updates their display orders correctly.
        """
        img1 = ProductImageService.create(product=self.product, image=self.generate_image("1.jpg"))
        img2 = ProductImageService.create(product=self.product, image=self.generate_image("2.jpg"))
        img3 = ProductImageService.create(product=self.product, image=self.generate_image("3.jpg"))

        # Desired order: img3, img1, img2 (so display orders should be 1, 2, 3)
        new_order = [str(img3.id), str(img1.id), str(img2.id)]
        ProductImageService.reorder(product=self.product, image_ids=new_order)

        img1.refresh_from_db()
        img2.refresh_from_db()
        img3.refresh_from_db()

        self.assertEqual(img3.display_order, 1)
        self.assertEqual(img1.display_order, 2)
        self.assertEqual(img2.display_order, 3)
