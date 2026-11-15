import json
from types import SimpleNamespace

import pytest

import stream.freshcart_consumer as consumer
import stream.freshcart_publisher as publisher
from elt.rabbitmq_ingest import land_and_load_orders


ORDER = {
    "order_id": "RABBIT-1001",
    "cust_email": "arjun.k@yahoo.in",
    "cust_name": "Arjun K",
    "order_date": "2026-09-01",
    "amount": "25.00",
    "currency": "USD",
    "pincode": "560034",
    "updated_at": "2026-09-05 10:00:00",
}


class RecordingChannel:
    def __init__(self):
        self.acks = []
        self.nacks = []
        self.callback = None

    def exchange_declare(self, **kwargs):
        pass

    def queue_declare(self, **kwargs):
        return SimpleNamespace(method=SimpleNamespace(queue="orders"))

    def queue_bind(self, **kwargs):
        pass

    def basic_qos(self, **kwargs):
        pass

    def basic_consume(self, **kwargs):
        self.callback = kwargs["on_message_callback"]

    def basic_ack(self, **kwargs):
        self.acks.append(kwargs)

    def basic_nack(self, **kwargs):
        self.nacks.append(kwargs)


def test_collect_orders_acks_valid_messages_and_nacks_malformed(monkeypatch):
    channel = RecordingChannel()

    class RecordingConnection:
        def __init__(self):
            self.closed = False
            self.elapsed = 0.0
            self.sent = False

        def channel(self):
            return channel

        def process_data_events(self, time_limit):
            if not self.sent:
                channel.callback(
                    channel,
                    SimpleNamespace(delivery_tag=1, routing_key="freshcart.web.order"),
                    SimpleNamespace(message_id="RABBIT-1001"),
                    json.dumps(ORDER).encode("utf-8"),
                )
                channel.callback(
                    channel,
                    SimpleNamespace(delivery_tag=2, routing_key="freshcart.web.order"),
                    SimpleNamespace(message_id="invalid"),
                    b"{invalid",
                )
                channel.callback(
                    channel,
                    SimpleNamespace(delivery_tag=3, routing_key="freshcart.web.order"),
                    SimpleNamespace(message_id="missing-fields"),
                    json.dumps({"order_id": "incomplete"}).encode("utf-8"),
                )
                self.sent = True
            self.elapsed += time_limit

        def close(self):
            self.closed = True

    connection = RecordingConnection()
    monkeypatch.setattr(consumer.pika, "BlockingConnection", lambda _: connection)
    monkeypatch.setattr(consumer.time, "monotonic", lambda: connection.elapsed)
    ready = []

    orders = consumer.collect_orders(
        "amqp://localhost",
        duration_seconds=2.5,
        on_ready=lambda: ready.append(True),
    )

    assert orders == [ORDER]
    assert ready == [True]
    assert channel.acks == [{"delivery_tag": 1}]
    assert channel.nacks == [
        {"delivery_tag": 2, "requeue": False},
        {"delivery_tag": 3, "requeue": False},
    ]
    assert connection.elapsed == pytest.approx(2.5)
    assert connection.closed


@pytest.mark.parametrize("duration", [0, -1, float("inf"), float("nan")])
def test_collect_orders_rejects_invalid_duration(duration):
    with pytest.raises(ValueError, match="finite positive"):
        consumer.collect_orders("amqp://localhost", duration_seconds=duration)


def test_publisher_accepts_pika_confirm_none_and_closes_connection(monkeypatch):
    class RecordingChannel:
        def __init__(self):
            self.published = []

        def exchange_declare(self, **kwargs):
            pass

        def confirm_delivery(self):
            pass

        def basic_publish(self, **kwargs):
            self.published.append(kwargs)

    class RecordingConnection:
        def __init__(self):
            self.channel_instance = RecordingChannel()
            self.closed = False

        def channel(self):
            return self.channel_instance

        def close(self):
            self.closed = True

    connection = RecordingConnection()
    monkeypatch.setattr(
        publisher.pika,
        "BlockingConnection",
        lambda _: connection,
    )

    publisher.publish_sample_orders("amqp://localhost", count=2, interval=0)

    assert len(connection.channel_instance.published) == 2
    assert connection.closed


def test_land_and_load_orders_uses_notebook_helpers_in_order():
    calls = []

    def write_landing(source, records, run_id):
        calls.append(("write", source, records, run_id))
        return "orders.json.gz"

    def load_file(path, table, stage_dir):
        calls.append(("load", path, table, stage_dir))

    result = land_and_load_orders([ORDER], "run-1", write_landing, load_file)

    assert result == "orders.json.gz"
    assert calls == [
        ("write", "web", [ORDER], "run-1"),
        ("load", "orders.json.gz", "bronze.orders_raw", "orders_web/run-1"),
    ]


def test_land_and_load_orders_rejects_empty_batch():
    with pytest.raises(ValueError, match="empty"):
        land_and_load_orders([], "run-1", lambda *args: None, lambda *args: None)
