"""Bridge collected RabbitMQ orders into the notebook's existing landing loader."""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

LandingPath = str | Path
WriteLanding = Callable[[str, Sequence[dict[str, Any]], str], LandingPath]
LoadFile = Callable[[LandingPath, str, str], None]


def land_and_load_orders(
    orders: Sequence[dict[str, Any]],
    run_id: str,
    write_landing: WriteLanding,
    load_file: LoadFile,
) -> LandingPath:
    """Write the raw order batch using the notebook helper, then load bronze."""
    if not orders:
        raise ValueError("Cannot land an empty RabbitMQ order batch")

    landing_path = write_landing("web", orders, run_id)
    load_file(landing_path, "bronze.orders_raw", f"orders_web/{run_id}")
    return landing_path
