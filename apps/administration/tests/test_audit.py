from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.administration.models import AdminAuditLog
from apps.administration.services.audit import AuditService

User = get_user_model()

class AuditServiceTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="password"
        )
        self.vendor_user = User.objects.create_user(
            email="vendor@example.com",
            password="password"
        )

    def test_log_action_creates_immutable_record(self):
        """Test that AuditService.log_action successfully creates a record with all fields."""
        log = AuditService.log_action(
            actor=self.admin_user,
            action='SUSPEND',
            resource_type='Shop',
            resource_id='shop-123',
            before_state={'status': 'ACTIVE'},
            after_state={'status': 'SUSPENDED'},
            reason="Violation of terms",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0"
        )

        self.assertIsInstance(log, AdminAuditLog)
        self.assertEqual(log.actor, self.admin_user)
        self.assertEqual(log.action, 'SUSPEND')
        self.assertEqual(log.resource_type, 'Shop')
        self.assertEqual(log.resource_id, 'shop-123')
        self.assertEqual(log.before_state, {'status': 'ACTIVE'})
        self.assertEqual(log.after_state, {'status': 'SUSPENDED'})
        self.assertEqual(log.reason, "Violation of terms")
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertEqual(log.user_agent, "Mozilla/5.0")
        
        # Verify it exists in DB
        self.assertEqual(AdminAuditLog.objects.count(), 1)
