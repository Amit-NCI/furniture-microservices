import pika
import json
import django
import os
import logging
import time

logger = logging.getLogger(__name__)


def get_connection():
    """Create a RabbitMQ connection with retry logic"""
    from decouple import config

    credentials = pika.PlainCredentials(
        username=config('RABBITMQ_USER', default='guest'),
        password=config('RABBITMQ_PASSWORD', default='guest'),
    )
    parameters = pika.ConnectionParameters(
        host=config('RABBITMQ_HOST', default='rabbitmq'),
        port=config('RABBITMQ_PORT', default=5672, cast=int),
        credentials=credentials,
        connection_attempts=5,
        retry_delay=5,
    )
    return pika.BlockingConnection(parameters)


def handle_order_placed(ch, method, properties, body):
    """
    Called when an order.placed event arrives.
    Decrements stock_quantity for each item in the order.
    """
    from products.models import Product

    try:
        message = json.loads(body)
        items = message.get('items', [])
        order_id = message.get('order_id')

        logger.info(f"Received order.placed event for order {order_id}")

        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)

            try:
                product = Product.objects.get(id=product_id)
                if product.stock_quantity >= quantity:
                    product.stock_quantity -= quantity
                    product.save()
                    logger.info(
                        f"Decremented stock for product {product_id} "
                        f"by {quantity}. Remaining: {product.stock_quantity}"
                    )
                else:
                    logger.warning(
                        f"Insufficient stock for product {product_id}. "
                        f"Available: {product.stock_quantity}, Requested: {quantity}"
                    )
            except Product.DoesNotExist:
                logger.error(f"Product {product_id} not found")

        # Acknowledge the message — tells RabbitMQ we processed it successfully
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing order.placed event: {e}")
        # Negative acknowledge — requeue the message so it can be retried
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    """
    Start consuming order.placed events from RabbitMQ.
    Runs as a blocking loop — meant to be started in a separate thread.
    """
    while True:
        try:
            connection = get_connection()
            channel = connection.channel()

            # Declare the same exchange the publisher uses
            channel.exchange_declare(
                exchange='orders',
                exchange_type='topic',
                durable=True,
            )

            # Declare a durable queue so messages survive RabbitMQ restart
            channel.queue_declare(queue='product_stock_updates', durable=True)

            # Bind the queue to the exchange with the routing key
            channel.queue_bind(
                exchange='orders',
                queue='product_stock_updates',
                routing_key='order.placed',
            )

            # Only process one message at a time — fair dispatch
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue='product_stock_updates',
                on_message_callback=handle_order_placed,
            )

            logger.info("Product service consumer started — waiting for order.placed events")
            channel.start_consuming()

        except Exception as e:
            logger.error(f"Consumer error: {e}. Retrying in 5 seconds...")
            time.sleep(5)