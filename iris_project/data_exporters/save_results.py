"""Export test predictions to CSV."""

try:
    from mage_ai.data_preparation.decorators import data_exporter
except ImportError:
    def data_exporter(function):
        return function


@data_exporter
def export_data(data, *args, **kwargs):
    data.to_csv("iris_predictions.csv", index=False)
    print("Saved", len(data), "predictions to iris_predictions.csv")
