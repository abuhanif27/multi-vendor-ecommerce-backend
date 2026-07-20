from apps.notifications.channels.base import BaseChannelStrategy

class InAppChannel(BaseChannelStrategy):
    """
    In-App notifications don't require network requests. 
    Creating the Notification record is enough, so sending is a no-op.
    """
    def send(self, delivery):
        pass
