"""Train a decision tree and return its predictions for the held-out split."""

from sklearn.tree import DecisionTreeClassifier

if "transformer" not in globals():
    try:
        from mage_ai.data_preparation.decorators import transformer
    except ImportError:
        def transformer(function):
            return function

if "test" not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(function):
            return function


FEATURES = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
]


@transformer
def train(data, *args, **kwargs):
    max_depth = int(kwargs.get("max_depth", 3))
    train_data = data[data["split"] == "train"]
    test_data = data[data["split"] == "test"].copy()

    model = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    model.fit(train_data[FEATURES], train_data["target"])

    test_data["predicted"] = model.predict(test_data[FEATURES])
    accuracy = (test_data["predicted"] == test_data["target"]).mean()
    print("max_depth =", max_depth, "| Test accuracy =", round(accuracy, 3))
    return test_data


@test
def test_accuracy(output, *args):
    accuracy = (output["predicted"] == output["target"]).mean()
    assert accuracy >= 0.8, "Model accuracy is below 80%"
