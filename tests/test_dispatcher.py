import random

from stream.dispatcher import build_request


def test_every_tenth_dispatch_is_missing_zone():
    normal_key, normal_message = build_request(9, random.Random(1))
    invalid_key, invalid_message = build_request(10, random.Random(1))

    assert "zone" in normal_message
    assert "zone" not in invalid_message
    assert len(normal_key.split(".")) == 3
    assert len(invalid_key.split(".")) == 3
