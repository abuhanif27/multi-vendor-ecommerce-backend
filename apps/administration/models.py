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
            ("can_suspend_vendor", "Can suspend a vendor shop"),
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
