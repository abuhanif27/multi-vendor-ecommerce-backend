import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    Explicit Domain Event Bus.
    Decouples business services from background/side-effect execution.
    """
    _subscribers = {}

    @classmethod
    def subscribe(cls, event_name, handler):
        if event_name not in cls._subscribers:
            cls._subscribers[event_name] = []
        cls._subscribers[event_name].append(handler)

    @classmethod
    def publish(cls, event_name, **kwargs):
        handlers = cls._subscribers.get(event_name, [])
        for handler in handlers:
            try:
                handler(**kwargs)
            except Exception as e:
                # We log the error but don't crash the main business transaction.
                handler_name = getattr(handler, '__name__', str(handler))
                logger.error(f"Error in event handler '{handler_name}' for event '{event_name}': {str(e)}")

    @classmethod
    def clear(cls):
        """Used strictly for testing."""
        cls._subscribers = {}
