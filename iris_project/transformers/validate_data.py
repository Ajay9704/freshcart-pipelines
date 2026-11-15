"""Validate the source Iris dataset before preparing the train/test split."""

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


@transformer
def validate(data, *args, **kwargs):
    return data.copy()


@test
def test_output(output, *args):
    assert not output.isna().any().any(), "Iris data must not contain missing values"
    assert output["target"].nunique() == 3, "Iris data must contain exactly 3 classes"
