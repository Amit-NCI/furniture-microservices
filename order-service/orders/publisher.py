import pika
import json
import logging
from decouple import config

logger = logging.getLogger(__name__)


def get_connection():
    """Create a RabbitMQ connection using credentials from .env"""
    credentials = pika.PlainCredentials(
        username=config('RABBITMQ_USER', default='guest'),
        password=config('RABBITMQ_PASSWORD', default='guest'),
    )
    parameters = pika.ConnectionParameters(
        host=config('RABBITMQ_HOST', default='rabbitmq'),
        port=config('RABBITMQ_PORT', default=5672, cast=int),
        credentials=credentials,
        connection_attempts=3,
        retry_delay=2,
    )
    return pika.BlockingConnection(parameters)


def publish_order_placed(order_id, user_id, items):
    """
    Publish an order.placed event to RabbitMQ.

    items is a list of dicts: [{ product_id, quantity, product_name }]

    Order service calls this after checkout succeeds.
    Product service consumes it to decrement stock.
    """
    try:
        connection = get_connection()
        channel = connection.channel()

        # Declare the exchange — durable means it survives RabbitMQ restart
        channel.exchange_declare(
            exchange='orders',
            exchange_type='topic',
            durable=True,
        )

        message = {
            'event': 'order.placed',
            'order_id': order_id,
            'user_id': user_id,
            'items': items,
        }

        channel.basic_publish(
            exchange='orders',
            routing_key='order.placed',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent — survives RabbitMQ restart
                content_type='application/json',
            ),
        )

        connection.close()
        logger.info(f"Published order.placed event for order {order_id}")

    except Exception as e:
        # Log the error but DO NOT raise — checkout already succeeded
        # This is the key resilience property: event failure doesn't
        # roll back the user's order
        logger.error(f"Failed to publish order.placed event: {e}")