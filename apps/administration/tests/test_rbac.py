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
        
        # New permissions
        from django.contrib.contenttypes.models import ContentType
        from apps.administration.models import AdminAuditLog
        content_type = ContentType.objects.get_for_model(AdminAuditLog)
        
        self.manage_platform_perm = Permission.objects.get(
            codename="can_manage_platform_settings", 
            content_type=content_type
        )
        self.approve_vendor_perm = Permission.objects.get(
            codename="can_approve_vendor", 
            content_type=content_type
        )
        self.suspend_vendor_perm = Permission.objects.get(codename="can_suspend_vendor", content_type=content_type)
        self.force_refund_perm = Permission.objects.get(codename="can_force_refund", content_type=content_type)

        self.vendor_manager_group = Group.objects.create(name="Vendor Manager")
        self.vendor_manager_group.permissions.add(self.approve_vendor_perm, self.suspend_vendor_perm)

        self.support_agent_group = Group.objects.create(name="Support Agent")
        self.support_agent_group.permissions.add(self.force_refund_perm)

    def test_user_without_role_lacks_permission(self):
        self.assertFalse(self.user.has_perm('administration.can_approve_vendor'))
        self.assertFalse(self.user.has_perm('administration.can_force_refund'))

    def test_user_with_single_role_has_permission(self):
        self.user.groups.add(self.vendor_manager_group)
        user = User.objects.get(id=self.user.id)
        
        self.assertTrue(user.has_perm('administration.can_approve_vendor'))
        self.assertTrue(user.has_perm('administration.can_suspend_vendor'))
        self.assertFalse(user.has_perm('administration.can_force_refund'))

    def test_user_with_multiple_roles_has_combined_permissions(self):
        self.user.groups.add(self.vendor_manager_group)
        self.user.groups.add(self.support_agent_group)
        user = User.objects.get(id=self.user.id)

        self.assertTrue(user.has_perm('administration.can_approve_vendor'))
        self.assertTrue(user.has_perm('administration.can_force_refund'))
        self.assertFalse(user.has_perm('administration.can_manage_platform_settings'))

    def test_superuser_has_all_permissions(self):
        superuser = User.objects.create_superuser(
            email="super@example.com",
            password="password"
        )
        self.assertTrue(superuser.has_perm('administration.can_approve_vendor'))
        self.assertTrue(superuser.has_perm('administration.can_suspend_vendor'))
        self.assertTrue(superuser.has_perm('administration.can_force_refund'))
        self.assertTrue(superuser.has_perm('administration.can_manage_platform_settings'))
