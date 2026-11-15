"""Export test predictions to CSV."""

from pathlib import Path

from mage_ai.settings.repo import get_repo_path

if "data_exporter" not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_exporter
    except ImportError:
        def data_exporter(function):
            return function


OUTPUT_PATH = Path(get_repo_path()) / "iris_predictions.csv"


@data_exporter
def export_data(data, *args, **kwargs):
    data.to_csv(OUTPUT_PATH, index=False)
    print("Saved", len(data), "predictions to", OUTPUT_PATH)


if "test" not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(function):
            return function


@test
def test_saved_predictions(*args, **kwargs):
    import pandas as pd

    assert OUTPUT_PATH.is_file(), f"Predictions file was not created: {OUTPUT_PATH}"
    saved = pd.read_csv(OUTPUT_PATH)
    assert len(saved) == 30, f"Expected 30 predictions, found {len(saved)}"
    assert {"target", "predicted"}.issubset(saved.columns)
