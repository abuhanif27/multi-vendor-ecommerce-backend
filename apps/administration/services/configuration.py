from typing import Any, Optional
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.administration.models import PlatformSetting, FeatureFlag
from apps.administration.services.audit import AuditService

User = get_user_model()

class PlatformConfigurationService:
    SETTING_CACHE_PREFIX = "platform_setting:"
    FEATURE_FLAG_CACHE_PREFIX = "feature_flag:"
    CACHE_TIMEOUT = 3600  # 1 hour, invalidated on save

    @classmethod
    def get_setting(cls, key: str) -> Any:
        """
        Retrieves a setting value from cache or DB.
        Returns the default_value if the setting exists but is inactive, 
        or if value is None.
        Raises ValueError if setting does not exist.
        """
        cache_key = f"{cls.SETTING_CACHE_PREFIX}{key}"
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value

        try:
            setting = PlatformSetting.objects.get(key=key)
        except PlatformSetting.DoesNotExist:
            raise ValueError(f"Platform setting '{key}' does not exist.")

        val = setting.value if setting.is_active and setting.value is not None else setting.default_value
        cache.set(cache_key, val, cls.CACHE_TIMEOUT)
        return val

    @classmethod
    def update_setting(
        cls, 
        key: str, 
        value: Any, 
        actor: User, 
        reason: Optional[str] = None
    ) -> PlatformSetting:
        """
        Updates a platform setting, enforces typing, invalidates cache, and records audit log.
        """
        try:
            setting = PlatformSetting.objects.get(key=key)
        except PlatformSetting.DoesNotExist:
            raise ValueError(f"Platform setting '{key}' does not exist.")

        before_state = {"value": setting.value}
        
        # Will raise ValidationError if typing is incorrect
        setting.value = value
        setting.clean()
        setting.save()

        after_state = {"value": setting.value}

        AuditService.log_action(
            actor=actor,
            action="UPDATE",
            resource_type="PlatformSetting",
            resource_id=key,
            result="SUCCESS",
            before_state=before_state,
            after_state=after_state,
            reason=reason
        )

        # Invalidate cache
        cache.delete(f"{cls.SETTING_CACHE_PREFIX}{key}")

        return setting

    @classmethod
    def is_feature_enabled(cls, key: str) -> bool:
        """
        Returns boolean indicating if a feature is enabled.
        Defaults to False if the feature flag doesn't exist to avoid hard crashing.
        """
        cache_key = f"{cls.FEATURE_FLAG_CACHE_PREFIX}{key}"
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value

        try:
            flag = FeatureFlag.objects.get(key=key)
            is_active = flag.is_active
        except FeatureFlag.DoesNotExist:
            is_active = False
            
        cache.set(cache_key, is_active, cls.CACHE_TIMEOUT)
        return is_active

    @classmethod
    def set_feature_flag(
        cls, 
        key: str, 
        is_active: bool, 
        actor: User, 
        reason: Optional[str] = None
    ) -> FeatureFlag:
        """
        Creates or updates a feature flag, invalidates cache, and records audit log.
        """
        flag, created = FeatureFlag.objects.get_or_create(
            key=key,
            defaults={'is_active': is_active}
        )

        before_state = {"is_active": flag.is_active} if not created else None

        if not created:
            flag.is_active = is_active
            flag.save()

        after_state = {"is_active": flag.is_active}

        AuditService.log_action(
            actor=actor,
            action="CREATE" if created else "UPDATE",
            resource_type="FeatureFlag",
            resource_id=key,
            result="SUCCESS",
            before_state=before_state,
            after_state=after_state,
            reason=reason
        )

        # Invalidate cache
        cache.delete(f"{cls.FEATURE_FLAG_CACHE_PREFIX}{key}")

        return flag
