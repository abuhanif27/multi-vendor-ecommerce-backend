import logging
import time

logger = logging.getLogger(__name__)

class EventBus:
    """
    Explicit Domain Event Bus.
    Supports strongly typed Event classes.
    """
    _subscribers = {}

    @classmethod
    def subscribe(cls, event_class, handler):
        if event_class not in cls._subscribers:
            cls._subscribers[event_class] = []
        cls._subscribers[event_class].append(handler)

    @classmethod
    def publish(cls, event):
        event_class = type(event)
        event_name = event_class.__name__
        handlers = cls._subscribers.get(event_class, [])
        
        logger.info(f"Event published: {event_name}")
        
        for handler in handlers:
            handler_name = getattr(handler, '__name__', str(handler))
            logger.info(f"Handler execution started: {handler_name} for {event_name}")
            start_time = time.time()
            
            try:
                handler(event)
                elapsed = time.time() - start_time
                logger.info(f"Handler completed: {handler_name} for {event_name} in {elapsed:.3f}s")
            except Exception as e:
                logger.error(f"Error in event handler '{handler_name}' for event '{event_name}': {str(e)}")

    @classmethod
    def clear(cls):
        """Used strictly for testing."""
        cls._subscribers = {}
