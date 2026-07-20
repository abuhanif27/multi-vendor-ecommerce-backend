from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

User = get_user_model()

class RBACTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="staff@example.com",
            password="password",
            is_staff=True
        )
        
        # We assume the migration has run and created the custom permissions attached to AdminAuditLog
        self.vendor_read_perm = Permission.objects.get(codename="can_read_vendors")
        self.vendor_write_perm = Permission.objects.get(codename="can_write_vendors")
        self.finance_read_perm = Permission.objects.get(codename="can_read_finance")

        self.vendor_manager_group = Group.objects.create(name="Vendor Manager")
        self.vendor_manager_group.permissions.add(self.vendor_read_perm, self.vendor_write_perm)

    def test_user_without_role_lacks_permission(self):
        self.assertFalse(self.user.has_perm('administration.can_read_vendors'))
        self.assertFalse(self.user.has_perm('administration.can_write_vendors'))

    def test_user_with_role_has_permission(self):
        self.user.groups.add(self.vendor_manager_group)
        # We need to fetch from db or use a fresh instance to clear permission cache
        user = User.objects.get(id=self.user.id)
        
        self.assertTrue(user.has_perm('administration.can_read_vendors'))
        self.assertTrue(user.has_perm('administration.can_write_vendors'))
        self.assertFalse(user.has_perm('administration.can_read_finance'))

    def test_superuser_has_all_permissions(self):
        superuser = User.objects.create_superuser(
            email="super@example.com",
            password="password"
        )
        self.assertTrue(superuser.has_perm('administration.can_read_vendors'))
        self.assertTrue(superuser.has_perm('administration.can_write_vendors'))
        self.assertTrue(superuser.has_perm('administration.can_read_finance'))
        self.assertTrue(superuser.has_perm('administration.can_write_finance'))
