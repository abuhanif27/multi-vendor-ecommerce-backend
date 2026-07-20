from abc import ABC, abstractmethod

class BaseCourierStrategy(ABC):
    """
    Abstract Base Class for Courier integrations.
    """
    
    @abstractmethod
    def generate_tracking_url(self, courier, tracking_number):
        """
        Takes a Courier instance and tracking number.
        Returns the formatted tracking URL.
        """
        pass
    
    @abstractmethod
    def get_latest_status(self, tracking_number):
        """
        Fetch the latest status from the Courier's API (if supported).
        Returns a dictionary or raises an exception.
        """
        pass
