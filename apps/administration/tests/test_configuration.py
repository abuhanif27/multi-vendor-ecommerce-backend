from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.cache import cache
from apps.administration.models import PlatformSetting, FeatureFlag, AdminAuditLog
from apps.administration.services.configuration import PlatformConfigurationService

User = get_user_model()

class PlatformConfigurationServiceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="password"
        )
        
        self.setting = PlatformSetting.objects.create(
            key="base_commission",
            category="MARKETPLACE",
            value_type="DECIMAL",
            value=10.5,
            default_value=5.0
        )
        
        self.flag = FeatureFlag.objects.create(
            key="enable_new_checkout",
            is_active=False
        )
        
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_get_setting_uses_cache(self):
        # First call hits DB
        val1 = PlatformConfigurationService.get_setting("base_commission")
        self.assertEqual(val1, 10.5)
        
        # Modify DB directly (bypassing service to test cache)
        PlatformSetting.objects.filter(key="base_commission").update(value=15.0)
        
        # Second call should hit cache, returning old value
        val2 = PlatformConfigurationService.get_setting("base_commission")
        self.assertEqual(val2, 10.5)

    def test_get_setting_inactive_uses_default(self):
        PlatformSetting.objects.filter(key="base_commission").update(is_active=False)
        val = PlatformConfigurationService.get_setting("base_commission")
        self.assertEqual(val, 5.0)

    def test_update_setting_validates_type(self):
        with self.assertRaises(ValidationError):
            PlatformConfigurationService.update_setting(
                key="base_commission",
                value="not-a-decimal",
                actor=self.admin
            )
            
    def test_update_setting_invalidates_cache_and_audits(self):
        # Warm cache
        PlatformConfigurationService.get_setting("base_commission")
        
        # Update via service
        PlatformConfigurationService.update_setting(
            key="base_commission",
            value=12.5,
            actor=self.admin,
            reason="Increased rate"
        )
        
        # Cache should be invalidated, next get should return new value
        new_val = PlatformConfigurationService.get_setting("base_commission")
        self.assertEqual(new_val, 12.5)
        
        # Verify Audit Log
        audit = AdminAuditLog.objects.get(resource_type="PlatformSetting")
        self.assertEqual(audit.action, "UPDATE")
        self.assertEqual(audit.after_state['value'], 12.5)
        self.assertEqual(audit.reason, "Increased rate")

    def test_is_feature_enabled_cache_and_default(self):
        self.assertFalse(PlatformConfigurationService.is_feature_enabled("enable_new_checkout"))
        
        # Non-existent feature flag defaults to False safely
        self.assertFalse(PlatformConfigurationService.is_feature_enabled("does_not_exist"))
        
    def test_set_feature_flag_creates_or_updates(self):
        # Update existing
        PlatformConfigurationService.set_feature_flag(
            key="enable_new_checkout",
            is_active=True,
            actor=self.admin
        )
        self.assertTrue(PlatformConfigurationService.is_feature_enabled("enable_new_checkout"))
        
        # Create new
        PlatformConfigurationService.set_feature_flag(
            key="magic_wand",
            is_active=True,
            actor=self.admin
        )
        self.assertTrue(PlatformConfigurationService.is_feature_enabled("magic_wand"))
        
        # Verify audit logs
        audits = AdminAuditLog.objects.filter(resource_type="FeatureFlag").order_by('timestamp')
        self.assertEqual(audits.count(), 2)
        self.assertEqual(audits[0].resource_id, "enable_new_checkout")
        self.assertEqual(audits[0].action, "UPDATE")
        self.assertEqual(audits[1].resource_id, "magic_wand")
        self.assertEqual(audits[1].action, "CREATE")

    def test_immutable_system_setting(self):
        PlatformSetting.objects.filter(key="base_commission").update(is_system=True)
        with self.assertRaises(ValidationError) as context:
            PlatformConfigurationService.update_setting(
                key="base_commission",
                value=20.0,
                actor=self.admin
            )
        self.assertIn("is a system setting and cannot be modified", str(context.exception))

    def test_reserved_key_prefix_validation(self):
        setting = PlatformSetting(
            key="sys_core_debug",
            category="SYSTEM",
            value_type="BOOLEAN",
            value=True,
            is_system=False
        )
        with self.assertRaises(ValidationError) as context:
            setting.clean()
        self.assertIn("Non-system settings cannot use the 'sys_' prefix", str(context.exception))
        
        # Should work if is_system=True
        setting.is_system = True
        setting.clean()  # Should not raise

    def test_inactive_feature_flags_behavior(self):
        # We already have 'enable_new_checkout' = False in setUp
        self.assertFalse(PlatformConfigurationService.is_feature_enabled("enable_new_checkout"))
        
        # Test it populates cache
        cache_key = f"{PlatformConfigurationService.FEATURE_FLAG_CACHE_PREFIX}enable_new_checkout"
        self.assertFalse(cache.get(cache_key))

    def test_cache_miss_after_invalidation(self):
        # Warm cache
        val = PlatformConfigurationService.get_setting("base_commission")
        self.assertEqual(val, 10.5)
        
        cache_key = f"{PlatformConfigurationService.SETTING_CACHE_PREFIX}base_commission"
        self.assertEqual(cache.get(cache_key), 10.5)
        
        # Invalidate via update
        PlatformConfigurationService.update_setting("base_commission", 11.0, self.admin)
        
        # Internal cache should be cleared
        self.assertIsNone(cache.get(cache_key))
        
        # Next read should hit DB and set cache
        new_val = PlatformConfigurationService.get_setting("base_commission")
        self.assertEqual(new_val, 11.0)
        self.assertEqual(cache.get(cache_key), 11.0)

