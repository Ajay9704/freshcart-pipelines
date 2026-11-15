"""Publish synthetic food-order requests to a RabbitMQ topic exchange."""

import argparse
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timezone

import pika

EXCHANGE = "rapido-dispatch"
CITIES = {
    "bangalore": ("koramangala", "indiranagar", "whitefield"),
    "chennai": ("tnagar", "velachery", "adyar"),
}
ORDER_TYPES = ("ride", "food")


def build_request(sequence, rng=None):
    rng = rng or random
    city = rng.choice(tuple(CITIES))
    zone = rng.choice(CITIES[city])
    order_type = rng.choice(ORDER_TYPES)
    request = {
        "id": str(uuid.uuid4()),
        "city": city,
        "type": order_type,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    if sequence % 10 != 0:
        request["zone"] = zone

    routing_key = f"{city}.{zone}.{order_type}"
    return routing_key, request


def publish_requests(url, interval, count=None):
    connection = pika.BlockingConnection(pika.URLParameters(url))
    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=EXCHANGE,
            exchange_type="topic",
            durable=True,
        )
        channel.confirm_delivery()

        sequence = 0
        while count is None or sequence < count:
            sequence += 1
            routing_key, request = build_request(sequence)
            body = json.dumps(request).encode("utf-8")
            published = channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=pika.DeliveryMode.Persistent,
                    message_id=request["id"],
                ),
            )
            if not published:
                raise RuntimeError(f"Broker did not confirm message {request['id']}.")
            logging.info("Published %s: %s", routing_key, body.decode("utf-8"))
            if count is None or sequence < count:
                time.sleep(interval)
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F"),
        help="AMQP URL (or set RABBITMQ_URL)",
    )
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--count", type=int, help="Stop after this many messages")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    if args.count is not None and args.count <= 0:
        parser.error("--count must be greater than zero")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    publish_requests(args.url, args.interval, args.count)


if __name__ == "__main__":
    main()
