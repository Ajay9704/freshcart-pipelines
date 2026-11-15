from sklearn.datasets import load_iris

from iris_project.transformers.prepare_data import transform


def test_split_is_80_20():
    data = load_iris(as_frame=True).frame

    output = transform(data)

    assert (output["split"] == "train").sum() == 120
    assert (output["split"] == "test").sum() == 30
