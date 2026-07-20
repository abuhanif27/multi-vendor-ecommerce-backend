from django.db import models
from django.conf import settings

class AdminAuditLog(models.Model):
    """
    Immutable ledger recording all state-changing actions performed by staff.
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
    before_state = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON representation of the resource before modification"
    )
    after_state = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON representation of the resource after modification"
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
            ("can_read_platform", "Can read platform configuration"),
            ("can_write_platform", "Can write platform configuration"),
            ("can_read_rbac", "Can read staff roles and permissions"),
            ("can_write_rbac", "Can write staff roles and permissions"),
            ("can_read_vendors", "Can read vendor administration"),
            ("can_write_vendors", "Can write vendor administration"),
            ("can_read_products", "Can read product moderation"),
            ("can_write_products", "Can write product moderation"),
            ("can_read_orders", "Can read order administration"),
            ("can_write_orders", "Can write order administration"),
            ("can_read_finance", "Can read financial administration"),
            ("can_write_finance", "Can write financial administration"),
        ]

    def __str__(self):
        return f"{self.actor} - {self.action} - {self.resource_type}:{self.resource_id}"
