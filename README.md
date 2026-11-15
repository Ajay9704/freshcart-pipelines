# FreshCart Pipelines

Course assignment: **From Git to Gold** — version control and CI, a FreshCart
ELT pipeline, an Iris ML pipeline, and RabbitMQ food-order routing.

## Repository layout

- `elt/freshcart_elt.ipynb` — FreshCart ELT notebook and RabbitMQ-to-Snowflake bonus.
- `iris_project/` — Mage-compatible Iris pipeline blocks.
- `stream/` — RabbitMQ dispatcher and driver scripts.
- `tests/` — automated checks that run outside Mage.
- `.github/workflows/ci.yml` — pytest workflow for pushes and pull requests.
- `report/` — final report PDF.
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

The bonus cell imports the project helpers, so first clone the repository in
Colab and set its folder as the working directory:

```python
!git clone --depth 1 https://github.com/Ajay9704/freshcart-pipelines.git /content/freshcart-pipelines
%cd /content/freshcart-pipelines
```

For the demonstrated Colab run, start a temporary RabbitMQ broker in that
runtime and set its URL:

```python
!apt-get update -qq
!apt-get install -y rabbitmq-server
!service rabbitmq-server start
!rabbitmqctl status

import os
os.environ["RABBITMQ_URL"] = "amqp://guest:guest@127.0.0.1:5672/%2F"
```

The notebook publishes three deterministic messages after declaring its
queue, collects for one minute, lands the records through `write_landing()`,
loads them with `load_file()`, and replays the same batch. The verified run
kept the Gold totals and the streamed order's `published_at` unchanged. Keep
Snowflake secrets in Colab Secrets and never add credentials to source files.

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

The FreshCart bonus consumer/publisher and landing handoff have focused
mock-based tests. The live Colab run also verified the Snowflake path: the
same RabbitMQ batch was loaded twice without changing Gold totals or the
streamed order's `published_at` value.

## Assignment status

The assignment implementation, live bonus run, report, and available
screenshots are complete. The full local test suite passed (**16 passed**).
The Colab evidence shows three streamed messages for one distinct order and
matching first-run/replay totals: 5 Gold orders, ₹9,865 revenue, and 201
loyalty points. The report and screenshot appendix are in `report/` and
`screenshots/`.
