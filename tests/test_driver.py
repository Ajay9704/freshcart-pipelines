import json
from types import SimpleNamespace

from stream.driver import handle_message


class RecordingChannel:
    def __init__(self):
        self.acknowledged = []
        self.rejected = []

    def basic_ack(self, delivery_tag):
        self.acknowledged.append(delivery_tag)

    def basic_nack(self, delivery_tag, requeue):
        self.rejected.append((delivery_tag, requeue))


def test_missing_zone_is_rejected_without_requeue():
    channel = RecordingChannel()
    method = SimpleNamespace(delivery_tag=7, routing_key="bangalore.whitefield.ride")
    properties = SimpleNamespace(message_id="bad-order")
    body = json.dumps({"id": "bad-order", "city": "bangalore", "type": "ride", "ts": "now"}).encode()

    handle_message(channel, method, properties, body, "Ravi")

    assert channel.rejected == [(7, False)]
    assert channel.acknowledged == []


def test_valid_order_is_acknowledged():
    channel = RecordingChannel()
    method = SimpleNamespace(delivery_tag=8, routing_key="bangalore.whitefield.ride")
    properties = SimpleNamespace(message_id="good-order")
    body = json.dumps(
        {
            "id": "good-order",
            "city": "bangalore",
            "zone": "whitefield",
            "type": "ride",
            "ts": "now",
        }
    ).encode()

    handle_message(channel, method, properties, body, "Arjun")

    assert channel.acknowledged == [8]
    assert channel.rejected == []
