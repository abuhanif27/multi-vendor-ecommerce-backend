from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from apps.orders.models import VendorOrder, Dispute, DisputeStatus, ResolutionOutcome
from apps.notifications.events import EventBus
from apps.orders.events import DisputeOpenedEvent, DisputeEscalatedEvent, DisputeResolvedEvent

class DisputeService:
    @staticmethod
    @transaction.atomic
    def open_dispute(vendor_order_id: str, reason: str):
        vendor_order = VendorOrder.objects.get(id=vendor_order_id)
        
        if vendor_order.status != VendorOrder.FulfillmentStatus.DELIVERED:
            raise ValidationError("Disputes can only be opened for DELIVERED orders.")
            
        # Hard-coded rule: Dispute must be opened within 30 days of delivery
        # Assuming we track 'delivered_at' or 'updated_at' when status changed to DELIVERED
        # Since TimeStampedModel updates updated_at, let's use that for now
        time_limit = timezone.now() - timedelta(days=30)
        if vendor_order.updated_at < time_limit:
            raise ValidationError("Disputes must be opened within 30 days of delivery.")
            
        active_disputes = Dispute.objects.filter(
            vendor_order=vendor_order
        ).exclude(
            status__in=[DisputeStatus.RESOLVED, DisputeStatus.REJECTED, DisputeStatus.CANCELLED]
        ).exists()
        
        if active_disputes:
            raise ValidationError("An active dispute already exists for this order.")
            
        dispute = Dispute.objects.create(
            vendor_order=vendor_order,
            reason=reason,
            status=DisputeStatus.OPEN
        )
        
        event = DisputeOpenedEvent(
            dispute_id=str(dispute.id),
            vendor_order_id=str(vendor_order.id),
            occurred_at=timezone.now()
        )
        transaction.on_commit(lambda: EventBus.publish(event))
        
        return dispute

    @staticmethod
    @transaction.atomic
    def escalate_dispute(dispute_id: str, actor):
        dispute = Dispute.objects.select_for_update().get(id=dispute_id)
        
        if dispute.status not in [DisputeStatus.OPEN, DisputeStatus.VENDOR_REVIEW]:
            raise ValidationError("Only OPEN or VENDOR_REVIEW disputes can be escalated.")
            
        dispute.status = DisputeStatus.ESCALATED
        dispute.save(update_fields=['status'])
        
        event = DisputeEscalatedEvent(
            dispute_id=str(dispute.id),
            vendor_order_id=str(dispute.vendor_order.id),
            actor_id=actor.id,
            occurred_at=timezone.now()
        )
        transaction.on_commit(lambda: EventBus.publish(event))
        
        return dispute

    @staticmethod
    @transaction.atomic
    def resolve_dispute(dispute_id: str, actor, outcome: ResolutionOutcome, resolution_notes: str = ""):
        dispute = Dispute.objects.select_for_update().get(id=dispute_id)
        
        if dispute.status in [DisputeStatus.RESOLVED, DisputeStatus.REJECTED, DisputeStatus.CANCELLED]:
            raise ValidationError("Dispute is already closed.")
            
        dispute.status = DisputeStatus.RESOLVED
        dispute.outcome = outcome
        dispute.resolution_notes = resolution_notes
        dispute.save(update_fields=['status', 'outcome', 'resolution_notes'])
        
        # Integration event
        event = DisputeResolvedEvent(
            dispute_id=str(dispute.id),
            vendor_order_id=str(dispute.vendor_order.id),
            actor_id=actor.id,
            outcome=outcome,
            occurred_at=timezone.now()
        )
        transaction.on_commit(lambda: EventBus.publish(event))
        
        return dispute

    @staticmethod
    @transaction.atomic
    def cancel_dispute(dispute_id: str, actor):
        dispute = Dispute.objects.select_for_update().get(id=dispute_id)
        
        if dispute.status in [DisputeStatus.RESOLVED, DisputeStatus.REJECTED, DisputeStatus.CANCELLED]:
            raise ValidationError("Dispute is already closed.")
            
        dispute.status = DisputeStatus.CANCELLED
        dispute.save(update_fields=['status'])
        
        return dispute
