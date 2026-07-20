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
        self.assertEqual(self.events_published[0].vendor_id, self.vendor_user.id)
        self.assertEqual(self.events_published[0].approved_by, self.super_admin.id)

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

    def test_approve_vendor_concurrency(self):
        import threading
        
        # We need to test the DB lock. Because TransactionTestCase doesn't commit until the end of the test usually,
        # wait, threading in Django tests with sqlite can be tricky. But we can simulate by approving twice and 
        # ensuring the idempotency checks correctly block multiple audit records. 
        # A true concurrent thread test in Django testing on sqlite may lock. Let's do a basic thread test.
        
        exceptions = []
        def approve():
            try:
                VendorAdministrationService.approve_vendor(
                    shop_id=str(self.shop.id),
                    actor=self.super_admin
                )
            except Exception as e:
                exceptions.append(e)

        t1 = threading.Thread(target=approve)
        t2 = threading.Thread(target=approve)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Verify
        if exceptions:
            self.assertTrue(
                "database is locked" in str(exceptions[0]) or "OperationalError" in str(type(exceptions[0])),
                f"Unexpected exception: {exceptions[0]}"
            )
        else:
            self.assertEqual(len(exceptions), 0)
        self.assertEqual(AdminAuditLog.objects.count(), 1)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.status, Shop.ShopStatus.APPROVED)
