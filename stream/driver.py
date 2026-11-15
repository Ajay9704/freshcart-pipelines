"""Consume matching RabbitMQ food-order requests and acknowledge valid ones."""

import argparse
import json
import logging
import os

import pika

EXCHANGE = "rapido-dispatch"
REQUIRED_FIELDS = ("id", "city", "zone", "type", "ts")


def handle_message(channel, method, properties, body, name):
    try:
        request = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logging.error("%s rejected malformed JSON", name)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    if not isinstance(request, dict):
        logging.error("%s rejected a non-object request", name)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    missing = [field for field in REQUIRED_FIELDS if field not in request]
    if missing:
        logging.error(
            "%s rejected message %s; missing fields: %s",
            name,
            properties.message_id,
            ", ".join(missing),
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    print(f"{name} received {method.routing_key}: {json.dumps(request)}", flush=True)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def consume(url, name, pattern):
    connection = pika.BlockingConnection(pika.URLParameters(url))
    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange=EXCHANGE,
            exchange_type="topic",
            durable=True,
        )
        queue = channel.queue_declare(queue="", exclusive=True).method.queue
        channel.queue_bind(
            exchange=EXCHANGE,
            queue=queue,
            routing_key=pattern,
        )
        channel.basic_qos(prefetch_count=1)
        logging.info("%s listening on %s (%s)", name, queue, pattern)

        def callback(channel, method, properties, body):
            handle_message(channel, method, properties, body, name)

        channel.basic_consume(queue=queue, on_message_callback=callback)
        channel.start_consuming()
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="Driver name")
    parser.add_argument("pattern", help="RabbitMQ topic binding pattern")
    parser.add_argument(
        "--url",
        default=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F"),
        help="AMQP URL (or set RABBITMQ_URL)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    consume(args.url, args.name, args.pattern)


if __name__ == "__main__":
    main()
