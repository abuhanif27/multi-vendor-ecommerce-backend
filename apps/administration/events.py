from dataclasses import dataclass

@dataclass
class VendorApprovedEvent:
    shop_id: str
    admin_id: int
