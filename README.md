# FreshCart Pipelines

Course assignment: **From Git to Gold** — version control and CI, a FreshCart
ELT pipeline, an Iris ML pipeline, and RabbitMQ food-order routing.

## Repository layout

- `elt/freshcart_elt.ipynb` — supplied FreshCart notebook, to be run and extended.
- `iris_project/` — Mage-compatible Iris pipeline blocks.
- `stream/` — RabbitMQ dispatcher and driver scripts.
- `tests/` — automated checks that run outside Mage.
- `.github/workflows/ci.yml` — pytest workflow for pushes and pull requests.
- `report/` — final report source and supporting material.
- `screenshots/` — evidence captured from actual runs.

## Local checks

Use Python 3.12 in a virtual environment, then install dependencies and run:

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

## Run the pipelines

### Snowflake ELT

Open `elt/freshcart_elt.ipynb` in Google Colab. Add these Colab Secrets before
running the Snowflake cells: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`,
`SNOWFLAKE_ROLE`, and `SNOWFLAKE_PASSWORD`. The notebook reads them at runtime;
do not put their values in source files or notebook outputs.

The bonus cell imports `stream/` and `elt/` helpers, so run it from a checkout
of this repository (clone the repo in Colab and change the working directory
to its root first). Set `RABBITMQ_URL` in the notebook runtime to a broker
reachable from that runtime; a Docker broker bound only to your own computer
is not reachable from hosted Colab. The cell publishes three deterministic
sample messages after creating its queue, collects for one minute, uses the
existing landing and Snowflake load helpers, then replays the same batch and
checks that Gold totals and the order's `published_at` remain stable. Keep
broker credentials out of notebook source and outputs.

### Mage Iris pipeline

From the repository root, run the Mage pipeline and its block tests:

```powershell
.\.venv\Scripts\mage.exe run iris_project iris_classifier --test
.\.venv\Scripts\mage.exe run iris_project iris_classifier --test --runtime-vars '{"max_depth": 1}'
.\.venv\Scripts\mage.exe start iris_project --host 127.0.0.1 --port 6789
```

The evaluation block prints the confusion matrix and metrics table during a
full pipeline run. Run the pipeline, rather than only the `evaluate_model`
block, so its `train_model` input is available. If Mage is installed globally,
`mage` can be used instead of the virtual-environment executable above.

Change `max_depth` for the other experiment runs. The exporter writes
`iris_project/iris_predictions.csv`, where it is visible in Mage's project file
browser. Remove that file before each run when checking whether a failed
quality test blocked the exporter.
The last command starts the local Mage UI; open
`http://127.0.0.1:6789/pipelines/iris_classifier/edit` to view the graph.
Keep the server bound to localhost unless you have configured secure
authentication for remote access.

### RabbitMQ stream

Set `RABBITMQ_URL` in the shell that will run the scripts. For a Docker-hosted
broker, use the local broker account's URL; RabbitMQ restricts its default
`guest` account to local broker connections. Keep credentials out of source
control. Start drivers with their name and binding pattern, then start the
dispatcher:

```powershell
python stream/driver.py Ravi "bangalore.koramangala.*"
python stream/dispatcher.py
```

The dispatcher publishes every two seconds and omits `zone` from every tenth
message. Valid deliveries are acknowledged; invalid ones are rejected without
requeue. Keep hosted broker URLs out of source control.

The FreshCart bonus consumer/publisher and the landing handoff have focused
mock-based tests. The live Snowflake idempotency assertion is in the notebook;
it must be run with valid Snowflake credentials and a broker URL reachable
from the notebook environment before reporting a live end-to-end result.

## Assignment status

The Mage exporter, RabbitMQ D2 stream, report, screenshots, and bonus
implementation are present. The full local test suite passed (**16 passed**).
The final report PDF is `report/23BCS061_BUDIDA_AJAY_Pipelines.pdf`.
The bonus notebook has not been run live in this local session because no
Snowflake credentials or reachable broker URL are available; do not describe
the mock-based tests as a live Snowflake result.
