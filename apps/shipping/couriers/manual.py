from apps.shipping.couriers.base import BaseCourierStrategy

class ManualCourierStrategy(BaseCourierStrategy):
    """
    Handles couriers that don't have API integrations.
    Tracking URLs are generated via simple string substitution if a template exists.
    """
    
    def generate_tracking_url(self, courier, tracking_number):
        if not courier or not courier.tracking_url_template or not tracking_number:
            return ""
        try:
            return courier.tracking_url_template.format(tracking_number=tracking_number)
        except KeyError:
            return ""
            
    def get_latest_status(self, tracking_number):
        """
        Manual couriers don't support automated polling.
        """
        raise NotImplementedError("Manual couriers cannot be polled automatically.")
