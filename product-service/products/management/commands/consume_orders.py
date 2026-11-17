"""
Run the product stock-update RabbitMQ consumer independently
from the Gunicorn HTTP workers.
"""

from django.core.management.base import BaseCommand

from products.consumer import start_consumer


class Command(BaseCommand):
    help = "Consume order.placed events and update product stock"

    def handle(self, *args, **options):
        self.stdout.write(
            "Starting dedicated product stock-update consumer..."
        )
        start_consumer()
