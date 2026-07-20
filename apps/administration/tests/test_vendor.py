from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from apps.shops.models import Shop
from apps.administration.models import AdminAuditLog
from apps.administration.services.vendor import VendorAdministrationService
from apps.administration.events import VendorApprovedEvent
from apps.notifications.events import EventBus

User = get_user_model()

class VendorAdministrationServiceTests(TransactionTestCase):
    def setUp(self):
        # Create test users
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
        
        # Create a pending shop
        self.shop = Shop.objects.create(
            name="Test Shop",
            owner=self.vendor_user,
            status=Shop.ShopStatus.PENDING
        )
        
        # Mock EventBus
        self.events_published = []
        def mock_handler(event):
            self.events_published.append(event)
            
        EventBus.clear()
        EventBus.subscribe(VendorApprovedEvent, mock_handler)

    def test_approve_vendor_success(self):
        shop = VendorAdministrationService.approve_vendor(
            shop_id=str(self.shop.id),
            actor=self.super_admin,
            reason="All documents verified"
        )
        
        self.assertEqual(shop.status, Shop.ShopStatus.APPROVED)
        
        # Verify Audit Log
        audit = AdminAuditLog.objects.get(resource_type="Shop", resource_id=str(shop.id))
        self.assertEqual(audit.action, "APPROVE")
        self.assertEqual(audit.before_state["status"], Shop.ShopStatus.PENDING)
        self.assertEqual(audit.after_state["status"], Shop.ShopStatus.APPROVED)
        self.assertEqual(audit.actor, self.super_admin)
        
        # Verify Event published (transaction is committed in test environment automatically if no nested tx fails)
        self.assertEqual(len(self.events_published), 1)
        self.assertIsInstance(self.events_published[0], VendorApprovedEvent)
        self.assertEqual(self.events_published[0].shop_id, str(shop.id))

    def test_approve_vendor_permission_denied(self):
        with self.assertRaises(PermissionDenied):
            VendorAdministrationService.approve_vendor(
                shop_id=str(self.shop.id),
                actor=self.staff_no_perms
            )

    def test_approve_vendor_invalid_transition(self):
        self.shop.status = Shop.ShopStatus.REJECTED
        self.shop.save()
        
        with self.assertRaises(ValidationError) as context:
            VendorAdministrationService.approve_vendor(
                shop_id=str(self.shop.id),
                actor=self.super_admin
            )
        self.assertIn("Cannot approve shop in status rejected", str(context.exception))

    def test_approve_vendor_idempotency(self):
        # Approve once
        VendorAdministrationService.approve_vendor(
            shop_id=str(self.shop.id),
            actor=self.super_admin
        )
        self.assertEqual(AdminAuditLog.objects.count(), 1)
        
        # Approve again
        VendorAdministrationService.approve_vendor(
            shop_id=str(self.shop.id),
            actor=self.super_admin
        )
        
        # Still only one audit log should exist
        self.assertEqual(AdminAuditLog.objects.count(), 1)
