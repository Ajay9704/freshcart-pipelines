import pytest
import pandas as pd

from iris_project.data_exporters import save_results
from iris_project.data_loaders.load_iris import load_data
from iris_project.transformers.evaluate_model import evaluate
from iris_project.transformers.prepare_data import transform
from iris_project.transformers.train_model import test_accuracy as check_accuracy
from iris_project.transformers.train_model import train
from iris_project.transformers.validate_data import validate


def test_export_writes_predictions_to_mage_project(tmp_path, monkeypatch):
    output_path = tmp_path / "iris_predictions.csv"
    monkeypatch.setattr(save_results, "OUTPUT_PATH", output_path)
    predictions = pd.DataFrame(
        {
            "target": [0, 1],
            "predicted": [0, 1],
        }
    )

    save_results.export_data(predictions)

    assert output_path.is_file()
    saved = pd.read_csv(output_path)
    assert saved.equals(predictions)


def test_pipeline_blocks_produce_valid_metrics(capsys):
    data = validate(load_data())
    prepared = transform(data)
    predictions = train(prepared, max_depth=3)

    metrics = evaluate(predictions)

    assert len(predictions) == 30
    assert set(metrics["metric"]) == {"accuracy", "precision", "recall", "f1_score"}
    assert metrics["value"].between(0, 1).all()
    output = capsys.readouterr().out
    assert "Confusion matrix:" in output
    assert "Metrics:" in output
    assert all(metric in output for metric in metrics["metric"])


def test_model_quality_gate_rejects_shallow_tree():
    prepared = transform(load_data())
    predictions = train(prepared, max_depth=1)

    with pytest.raises(AssertionError, match="below 80%"):
        check_accuracy(predictions)
