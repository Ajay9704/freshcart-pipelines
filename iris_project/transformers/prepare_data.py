"""Prepare Iris features and assign a deterministic stratified split."""

import pandas as pd
from sklearn.model_selection import train_test_split

try:
    from mage_ai.data_preparation.decorators import test, transformer
except ImportError:
    def transformer(function):
        return function

    def test(function):
        return function


@transformer
def transform(data, *args, **kwargs):
    train_data, test_data = train_test_split(
        data,
        test_size=0.2,
        random_state=42,
    )

    train_data = train_data.copy()
    test_data = test_data.copy()
    train_data["split"] = "train"
    test_data["split"] = "test"
    return pd.concat([train_data, test_data])


@test
def validate_split(output, *args):
    assert (output["split"] == "train").sum() == 120
    assert (output["split"] == "test").sum() == 30
