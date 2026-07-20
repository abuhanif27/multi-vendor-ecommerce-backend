from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

@dataclass
class WidgetDataDTO:
    """
    Reusable dashboard widget representation to decouple the frontend from backend schemas.
    """
    title: str
    value: str
    delta_percentage: Optional[Decimal] = None
    delta_label: Optional[str] = None
    chart_labels: Optional[List[str]] = None
    chart_data: Optional[List[float]] = None

@dataclass
class SalesSummaryDTO:
    """
    Core derived KPI measurements for a given period.
    """
    gross_revenue: Decimal
    net_revenue: Decimal
    order_count: int
    average_order_value: Decimal
    cancellation_rate: Decimal
    return_rate: Decimal

@dataclass
class TopProductDTO:
    product_id: str
    product_name: str
    units_sold: int
    gross_revenue: Decimal
