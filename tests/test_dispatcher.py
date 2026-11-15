import random

import stream.dispatcher as dispatcher
from stream.dispatcher import build_request


def test_every_tenth_dispatch_is_missing_zone():
    normal_key, normal_message = build_request(9, random.Random(1))
    invalid_key, invalid_message = build_request(10, random.Random(1))

    assert "zone" in normal_message
    assert "zone" not in invalid_message
    assert len(normal_key.split(".")) == 3
    assert len(invalid_key.split(".")) == 3


def test_publisher_accepts_pika_confirm_returning_none(monkeypatch):
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
        dispatcher.pika,
        "BlockingConnection",
        lambda parameters: connection,
    )

    dispatcher.publish_requests("amqp://localhost", interval=0, count=1)

    assert len(connection.channel_instance.published) == 1
    assert connection.closed
