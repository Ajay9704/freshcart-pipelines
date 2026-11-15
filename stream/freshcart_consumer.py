"""Collect FreshCart-shaped order messages from the RabbitMQ topic exchange."""

import argparse
import json
import logging
import math
import os
import time
from collections.abc import Callable
from typing import Any

import pika

EXCHANGE = "rapido-dispatch"
REQUIRED_FIELDS = (
    "order_id",
    "cust_email",
    "cust_name",
    "order_date",
    "amount",
    "currency",
    "pincode",
    "updated_at",
)


def handle_message(channel, method, properties, body, orders):
    try:
        order = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logging.error("Rejected malformed FreshCart message")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    if not isinstance(order, dict):
        logging.error("Rejected a non-object FreshCart message")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    missing = [field for field in REQUIRED_FIELDS if field not in order]
    if missing:
        logging.error(
            "Rejected FreshCart message %s; missing fields: %s",
            properties.message_id,
            ", ".join(missing),
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    orders.append(order)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def collect_orders(
    url,
    duration_seconds=60,
    on_ready: Callable[[], None] | None = None,
):
    """Collect and acknowledge valid order objects for a bounded duration."""
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        raise ValueError("duration_seconds must be a finite positive number")

    connection = pika.BlockingConnection(pika.URLParameters(url))
    orders: list[dict[str, Any]] = []
    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=EXCHANGE,
            exchange_type="topic",
            durable=True,
        )
        queue = channel.queue_declare(queue="", exclusive=True).method.queue
        channel.queue_bind(exchange=EXCHANGE, queue=queue, routing_key="#")
        channel.basic_qos(prefetch_count=100)
        channel.basic_consume(
            queue=queue,
            on_message_callback=lambda ch, method, properties, body: handle_message(
                ch, method, properties, body, orders
            ),
        )

        deadline = time.monotonic() + duration_seconds
        if on_ready is not None:
            on_ready()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            connection.process_data_events(time_limit=min(1.0, remaining))
    finally:
        connection.close()

    return orders


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F"),
        help="AMQP URL (or set RABBITMQ_URL)",
    )
    parser.add_argument("--duration", type=float, default=60)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    orders = collect_orders(args.url, args.duration)
    print(f"Collected {len(orders)} valid FreshCart order messages", flush=True)


if __name__ == "__main__":
    main()
