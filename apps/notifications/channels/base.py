from abc import ABC, abstractmethod

class BaseChannelStrategy(ABC):
    @abstractmethod
    def send(self, delivery):
        """
        Takes a NotificationDelivery instance.
        Executes the network request or DB update.
        Returns None if successful, or raises an Exception.
        """
        pass
