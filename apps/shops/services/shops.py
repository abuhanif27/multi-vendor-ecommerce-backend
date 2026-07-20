from django.core.exceptions import ValidationError
from apps.shops.models import Shop

class ShopService:
    @staticmethod
    def approve_shop(shop_id: str) -> Shop:
        """
        Approves a shop. Contains business validation for the transition.
        """
        shop = Shop.objects.get(id=shop_id)
        
        # Idempotency
        if shop.status == Shop.ShopStatus.APPROVED:
            return shop

        # Allowed transitions: PENDING -> APPROVED or SUSPENDED -> APPROVED
        if shop.status not in [Shop.ShopStatus.PENDING, Shop.ShopStatus.SUSPENDED]:
            raise ValidationError(f"Cannot approve shop in status {shop.status}")

        shop.status = Shop.ShopStatus.APPROVED
        shop.save()
        return shop
