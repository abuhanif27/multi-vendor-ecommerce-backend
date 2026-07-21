import uuid
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITransactionTestCase
from rest_framework import status
from apps.shops.models import Shop, Product
from apps.catalog.models import Category
from apps.notifications.events import EventBus
from apps.administration.events import ProductApprovedEvent
from apps.administration.models import AdminAuditLog

User = get_user_model()

class ProductModerationAPITests(APITransactionTestCase):
    def setUp(self):
        EventBus.clear()
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='password123',
            is_staff=True
        )
        
        self.vendor_user = User.objects.create_user(
            email='vendor@example.com',
            password='password123'
        )
        
        self.shop = Shop.objects.create(
            owner=self.vendor_user,
            name='Test Shop',
            status=Shop.ShopStatus.APPROVED
        )
        
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )
        
        self.product = Product.objects.create(
            shop=self.shop,
            category=self.category,
            name="Test Product",
            status=Product.ProductStatus.PENDING
        )

    def test_approve_product_requires_permission(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-product-approve', kwargs={'product_id': self.product.id})
        
        response = self.client.post(url, {'reason': 'Looks good'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_approve_product_success(self):
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='can_moderate_products')
        self.admin_user.user_permissions.add(perm)
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-product-approve', kwargs={'product_id': self.product.id})
        
        events = []
        EventBus.subscribe(ProductApprovedEvent, lambda e: events.append(e))
        
        response = self.client.post(url, {'reason': 'Verified content'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.ProductStatus.ACTIVE)
        
        # Check audit log
        audit = AdminAuditLog.objects.filter(resource_id=str(self.product.id)).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "APPROVE")
        self.assertEqual(audit.result, "SUCCESS")
        
        # Check event bus
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].product_id, str(self.product.id))
        self.assertEqual(events[0].actor_id, self.admin_user.id)

    def test_reject_product_success(self):
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='can_moderate_products')
        self.admin_user.user_permissions.add(perm)
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('admin-product-reject', kwargs={'product_id': self.product.id})
        response = self.client.post(url, {'reason': 'Invalid image'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.ProductStatus.REJECTED)

    def test_suspend_product_success(self):
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='can_moderate_products')
        self.admin_user.user_permissions.add(perm)
        self.client.force_authenticate(user=self.admin_user)
        
        self.product.status = Product.ProductStatus.ACTIVE
        self.product.save()
        
        url = reverse('admin-product-suspend', kwargs={'product_id': self.product.id})
        response = self.client.post(url, {'reason': 'TOS violation'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.ProductStatus.SUSPENDED)

    def test_restore_product_success(self):
        from django.contrib.auth.models import Permission
        perm = Permission.objects.get(codename='can_moderate_products')
        self.admin_user.user_permissions.add(perm)
        self.client.force_authenticate(user=self.admin_user)
        
        self.product.status = Product.ProductStatus.SUSPENDED
        self.product.save()
        
        url = reverse('admin-product-restore', kwargs={'product_id': self.product.id})
        response = self.client.post(url, {'reason': 'All good'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.ProductStatus.ACTIVE)
