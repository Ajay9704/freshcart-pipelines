"""Publish a deterministic FreshCart-style order for the lakehouse demo."""

import argparse
import json
import logging
import os
import time

import pika

EXCHANGE = "rapido-dispatch"
SAMPLE_ORDER = {
    "order_id": "RABBIT-1001",
    "cust_email": "arjun.k@yahoo.in",
    "cust_name": "Arjun K",
    "order_date": "2026-09-01",
    "amount": "25.00",
    "currency": "USD",
    "pincode": "560034",
    "updated_at": "2026-09-05 10:00:00",
}


def publish_sample_orders(url, count=1, interval=1.0):
    if count <= 0:
        raise ValueError("count must be greater than zero")
    if interval < 0:
        raise ValueError("interval must not be negative")

    connection = pika.BlockingConnection(pika.URLParameters(url))
    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=EXCHANGE,
            exchange_type="topic",
            durable=True,
        )
        channel.confirm_delivery()
        body = json.dumps(SAMPLE_ORDER).encode("utf-8")

        for sequence in range(count):
            confirmed = channel.basic_publish(
                exchange=EXCHANGE,
                routing_key="freshcart.web.order",
                body=body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=pika.DeliveryMode.Persistent,
                    message_id=SAMPLE_ORDER["order_id"],
                ),
            )
            if confirmed is False:
                raise RuntimeError(
                    f"Broker did not confirm message {SAMPLE_ORDER['order_id']}."
                )
            logging.info(
                "Published FreshCart order %s (%s/%s)",
                SAMPLE_ORDER["order_id"],
                sequence + 1,
                count,
            )
            if sequence + 1 < count:
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
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    publish_sample_orders(args.url, args.count, args.interval)


if __name__ == "__main__":
    main()
