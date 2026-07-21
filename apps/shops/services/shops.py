from typing import Tuple
from django.core.exceptions import ValidationError
from apps.shops.models import Shop

class ShopService:
    @staticmethod
    def approve_shop(shop_id: str) -> Tuple[Shop, bool]:
        """
        Approves a shop. Contains business validation for the transition.
        Returns a tuple: (shop_instance, was_approved_now)
        """
        # Acquire lock to prevent concurrent modifications
        shop = Shop.objects.select_for_update().get(id=shop_id)
        
        # Idempotency
        if shop.status == Shop.ShopStatus.APPROVED:
            return shop, False

        # Allowed transitions: PENDING -> APPROVED or SUSPENDED -> APPROVED
        if shop.status not in [Shop.ShopStatus.PENDING, Shop.ShopStatus.SUSPENDED]:
            raise ValidationError(f"Cannot approve shop in status {shop.status}")

        shop.status = Shop.ShopStatus.APPROVED
        shop.save()
        return shop, True

    @staticmethod
    def suspend_shop(shop_id: str) -> Tuple[Shop, bool]:
        shop = Shop.objects.select_for_update().get(id=shop_id)
        if shop.status == Shop.ShopStatus.SUSPENDED:
            return shop, False
        if shop.status != Shop.ShopStatus.APPROVED:
            raise ValidationError(f"Cannot suspend shop in status {shop.status}")
        shop.status = Shop.ShopStatus.SUSPENDED
        shop.save()
        return shop, True

    @staticmethod
    def restore_shop(shop_id: str) -> Tuple[Shop, bool]:
        shop = Shop.objects.select_for_update().get(id=shop_id)
        if shop.status == Shop.ShopStatus.APPROVED:
            return shop, False
        if shop.status != Shop.ShopStatus.SUSPENDED:
            raise ValidationError(f"Cannot restore shop in status {shop.status}")
        shop.status = Shop.ShopStatus.APPROVED
        shop.save()
        return shop, True

    @staticmethod
    def reject_shop(shop_id: str) -> Tuple[Shop, bool]:
        shop = Shop.objects.select_for_update().get(id=shop_id)
        if shop.status == Shop.ShopStatus.REJECTED:
            return shop, False
        if shop.status != Shop.ShopStatus.PENDING:
            raise ValidationError(f"Cannot reject shop in status {shop.status}. Only pending applications can be rejected.")
        shop.status = Shop.ShopStatus.REJECTED
        shop.save()
        return shop, True
