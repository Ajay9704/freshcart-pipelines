"""Load the built-in Iris dataset for the Mage pipeline."""

from sklearn.datasets import load_iris

if "data_loader" not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_loader
    except ImportError:
        def data_loader(function):
            return function

if "test" not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(function):
            return function


@data_loader
def load_data(*args, **kwargs):
    iris = load_iris(as_frame=True)
    data = iris.frame
    print("Rows loaded:", len(data))
    return data


@test
def test_output(output, *args):
    assert len(output) == 150, "Iris must have 150 rows"
