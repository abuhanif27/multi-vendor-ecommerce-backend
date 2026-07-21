from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class AdminAuditLog(models.Model):
    """
    Generic platform audit infrastructure.
    Immutable ledger recording all state-changing actions performed by staff across all domains.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('SUSPEND', 'Suspend'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('REFUND', 'Refund'),
        ('OTHER', 'Other'),
    ]

    RESULT_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_audit_logs',
        help_text="The staff user who performed the action"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource_type = models.CharField(
        max_length=100, 
        help_text="The type of resource modified (e.g., 'Shop', 'Product')"
    )
    resource_id = models.CharField(
        max_length=100,
        help_text="The ID of the modified resource"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default='SUCCESS')
    before_state = models.JSONField(
        null=True, 
        blank=True,
        help_text="Optional JSON representation of the resource before modification. Avoid large payloads."
    )
    after_state = models.JSONField(
        null=True, 
        blank=True,
        help_text="Optional JSON representation of the resource after modification. Avoid large payloads."
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    reason = models.TextField(
        null=True, 
        blank=True,
        help_text="Optional reason or comment provided by the staff user"
    )

    class Meta:
        ordering = ['-timestamp']
        permissions = [
            ("can_approve_vendor", "Can approve a vendor shop"),
            ("can_reject_vendor", "Can reject a vendor shop"),
            ("can_suspend_vendor", "Can suspend a vendor shop"),
            ("can_restore_vendor", "Can restore a vendor shop"),
            ("can_force_refund", "Can force a refund on an order"),
            ("can_manage_platform_settings", "Can manage platform configuration"),
            ("can_moderate_products", "Can moderate products"),
            ("can_moderate_reviews", "Can moderate reviews"),
            ("can_read_audit_logs", "Can read audit logs"),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("AdminAuditLog entries are immutable and cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("AdminAuditLog entries are immutable and cannot be deleted.")

    def __str__(self):
        return f"{self.actor} - {self.action} ({self.result}) - {self.resource_type}:{self.resource_id}"

class FeatureFlag(models.Model):
    """Controls the availability of platform features."""
    key = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("can_manage_feature_flags", "Can manage feature flags"),
        ]

    def __str__(self):
        return f"FeatureFlag: {self.key} (Active: {self.is_active})"


class PlatformSetting(models.Model):
    """Strongly typed global configuration settings."""
    CATEGORY_CHOICES = [
        ('MARKETPLACE', 'Marketplace'),
        ('ORDERS', 'Orders'),
        ('PAYMENTS', 'Payments'),
        ('SHIPPING', 'Shipping'),
        ('PROMOTIONS', 'Promotions'),
        ('NOTIFICATIONS', 'Notifications'),
        ('SECURITY', 'Security'),
        ('ANALYTICS', 'Analytics'),
        ('SYSTEM', 'System'),
    ]

    TYPE_CHOICES = [
        ('BOOLEAN', 'Boolean'),
        ('INTEGER', 'Integer'),
        ('DECIMAL', 'Decimal'),
        ('STRING', 'String'),
        ('JSON', 'JSON'),
    ]

    key = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    value_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    value = models.JSONField(help_text="Stored as JSON internally to support exact typing.")
    default_value = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False, help_text="System settings cannot be modified by staff.")
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("can_manage_platform_settings", "Can manage platform configuration"),
        ]

    def clean(self):
        super().clean()
        if self.key and self.key.startswith('sys_') and not self.is_system:
            raise ValidationError("Non-system settings cannot use the 'sys_' prefix.")
            
        if self.value is not None:
            self._validate_type(self.value, self.value_type)
        if self.default_value is not None:
            self._validate_type(self.default_value, self.value_type)

    def _validate_type(self, val, val_type):
        if val_type == 'BOOLEAN' and not isinstance(val, bool):
            raise ValidationError(f"Value '{val}' is not a valid Boolean.")
        elif val_type == 'INTEGER' and (not isinstance(val, int) or isinstance(val, bool)):
            raise ValidationError(f"Value '{val}' is not a valid Integer.")
        elif val_type == 'DECIMAL' and not isinstance(val, (float, int)):
            raise ValidationError(f"Value '{val}' is not a valid Decimal/Float.")
        elif val_type == 'STRING' and not isinstance(val, str):
            raise ValidationError(f"Value '{val}' is not a valid String.")
        elif val_type == 'JSON' and not isinstance(val, (dict, list)):
            raise ValidationError(f"Value '{val}' is not valid JSON object/array.")

    def __str__(self):
        return f"Setting: {self.key} ({self.value_type})"
