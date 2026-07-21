import unittest
from django.conf import settings
from django.test import TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from apps.shops.models import Shop
from apps.administration.models import AdminAuditLog
from apps.administration.services.vendor import VendorAdministrationService
from apps.administration.events import VendorApprovedEvent, VendorSuspendedEvent, VendorRestoredEvent, VendorRejectedEvent
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

    @unittest.skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3', "SQLite locks entire database")
    def test_approve_vendor_concurrency(self):
        import threading
        
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
        self.assertEqual(len(exceptions), 0)
        self.assertEqual(AdminAuditLog.objects.count(), 1)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.status, Shop.ShopStatus.APPROVED)

    def test_suspend_vendor_success(self):
        self.shop.status = Shop.ShopStatus.APPROVED
        self.shop.save()
        
        EventBus.clear()
        events = []
        EventBus.subscribe(VendorSuspendedEvent, lambda e: events.append(e))

        shop = VendorAdministrationService.suspend_vendor(
            shop_id=str(self.shop.id),
            actor=self.super_admin,
            reason="Violation of TOS"
        )
        
        self.assertEqual(shop.status, Shop.ShopStatus.SUSPENDED)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], VendorSuspendedEvent)
        self.assertEqual(events[0].shop_id, str(shop.id))
        
        audit = AdminAuditLog.objects.get(resource_type="Shop", resource_id=str(shop.id), action="SUSPEND")
        self.assertEqual(audit.after_state["status"], Shop.ShopStatus.SUSPENDED)
        
    def test_restore_vendor_success(self):
        self.shop.status = Shop.ShopStatus.SUSPENDED
        self.shop.save()
        
        EventBus.clear()
        events = []
        EventBus.subscribe(VendorRestoredEvent, lambda e: events.append(e))

        shop = VendorAdministrationService.restore_vendor(
            shop_id=str(self.shop.id),
            actor=self.super_admin,
            reason="Issue resolved"
        )
        
        self.assertEqual(shop.status, Shop.ShopStatus.APPROVED)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], VendorRestoredEvent)
        self.assertEqual(events[0].shop_id, str(shop.id))
        
        audit = AdminAuditLog.objects.get(resource_type="Shop", resource_id=str(shop.id), action="UPDATE")
        self.assertEqual(audit.after_state["status"], Shop.ShopStatus.APPROVED)

    def test_reject_vendor_success(self):
        self.shop.status = Shop.ShopStatus.PENDING
        self.shop.save()
        
        EventBus.clear()
        events = []
        EventBus.subscribe(VendorRejectedEvent, lambda e: events.append(e))

        shop = VendorAdministrationService.reject_vendor(
            shop_id=str(self.shop.id),
            actor=self.super_admin,
            reason="Incomplete documents"
        )
        
        self.assertEqual(shop.status, Shop.ShopStatus.REJECTED)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], VendorRejectedEvent)
        self.assertEqual(events[0].shop_id, str(shop.id))
        self.assertEqual(events[0].reason, "Incomplete documents")
        
        audit = AdminAuditLog.objects.get(resource_type="Shop", resource_id=str(shop.id), action="REJECT")
        self.assertEqual(audit.after_state["status"], Shop.ShopStatus.REJECTED)
