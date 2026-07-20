from rest_framework.test import APITransactionTestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from apps.shops.models import Shop
from apps.administration.events import VendorApprovedEvent
from apps.notifications.events import EventBus
import uuid

User = get_user_model()

class VendorAdministrationAPITests(APITransactionTestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            email="admin@example.com",
            password="password"
        )
        self.staff_no_perms = User.objects.create_user(
            email="staff@example.com",
            password="password",
            is_staff=True
        )
        self.vendor_user = User.objects.create_user(
            email="vendor@example.com",
            password="password"
        )
        
        self.shop = Shop.objects.create(
            name="Test Shop",
            owner=self.vendor_user,
            status=Shop.ShopStatus.PENDING
        )
        
        self.url = reverse('admin-vendor-approve', kwargs={'shop_id': str(self.shop.id)})
        
        self.events_published = []
        def mock_handler(event):
            self.events_published.append(event)
            
        EventBus.clear()
        EventBus.subscribe(VendorApprovedEvent, mock_handler)

    def test_anonymous_user_blocked(self):
        response = self.client.post(self.url, {"reason": "ok"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_without_permission_blocked(self):
        self.client.force_authenticate(user=self.staff_no_perms)
        response = self.client.post(self.url, {"reason": "ok"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_shop_id(self):
        self.client.force_authenticate(user=self.super_admin)
        invalid_url = reverse('admin-vendor-approve', kwargs={'shop_id': str(uuid.uuid4())})
        response = self.client.post(invalid_url, {"reason": "ok"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_successful_approval_and_event_payload(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(self.url, {"reason": "All clear"})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "approved")
        
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.status, Shop.ShopStatus.APPROVED)
        
        # Verify event consumer payload
        self.assertEqual(len(self.events_published), 1)
        event = self.events_published[0]
        self.assertIsInstance(event, VendorApprovedEvent)
        
        # Verify payload integrity
        self.assertEqual(event.shop_id, str(self.shop.id))
        self.assertEqual(event.vendor_id, self.vendor_user.id)
        self.assertEqual(event.approved_by, self.super_admin.id)
        self.assertIsNotNone(event.approved_at)

    def test_successful_suspension(self):
        self.shop.status = Shop.ShopStatus.APPROVED
        self.shop.save()
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('admin-vendor-suspend', kwargs={'shop_id': str(self.shop.id)})
        response = self.client.post(url, {"reason": "TOS violation"})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.status, Shop.ShopStatus.SUSPENDED)

    def test_successful_restoration(self):
        self.shop.status = Shop.ShopStatus.SUSPENDED
        self.shop.save()
        self.client.force_authenticate(user=self.super_admin)
        url = reverse('admin-vendor-restore', kwargs={'shop_id': str(self.shop.id)})
        response = self.client.post(url, {"reason": "Reviewed and resolved"})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.status, Shop.ShopStatus.APPROVED)
