from django.apps import AppConfig
import threading
import logging

logger = logging.getLogger(__name__)


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'

    def ready(self):
        """
        Start the RabbitMQ consumer in a background thread
        when Django starts up.

        The consumer runs independently of HTTP requests —
        it processes events as they arrive from the order service.
        """
        import os
        # Only start in the main process, not in Django's autoreloader child
        if os.environ.get('RUN_MAIN') != 'true':
            threading.Thread(
                target=self._start_consumer,
                daemon=True,
                name='rabbitmq-consumer',
            ).start()

    def _start_consumer(self):
        import time
        # Give Django a moment to finish initialising before consuming
        time.sleep(5)
        try:
            from products.consumer import start_consumer
            start_consumer()
        except Exception as e:
            logger.error(f"Consumer thread failed: {e}")