"""Calculate and display evaluation metrics for the trained Iris model."""

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

try:
    from mage_ai.data_preparation.decorators import test, transformer
except ImportError:
    def transformer(function):
        return function

    def test(function):
        return function


@transformer
def evaluate(data, *args, **kwargs):
    actual = data["target"]
    predicted = data["predicted"]

    print("Confusion matrix:")
    print(pd.crosstab(actual, predicted, rownames=["actual"], colnames=["predicted"]))

    return pd.DataFrame(
        {
            "metric": ["accuracy", "precision", "recall", "f1_score"],
            "value": [
                round(accuracy_score(actual, predicted), 3),
                round(precision_score(actual, predicted, average="macro"), 3),
                round(recall_score(actual, predicted, average="macro"), 3),
                round(f1_score(actual, predicted, average="macro"), 3),
            ],
        }
    )


@test
def test_metrics(output, *args):
    assert set(output["metric"]) == {"accuracy", "precision", "recall", "f1_score"}
    assert output["value"].between(0, 1).all()
