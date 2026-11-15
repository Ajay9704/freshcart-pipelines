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
running the notebook: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_ROLE`,
and `SNOWFLAKE_PASSWORD`. The notebook reads them at runtime; do not put their
values in source files or notebook outputs.

### Mage Iris pipeline

From the repository root, run the Mage pipeline and its block tests:

```powershell
mage run iris_project iris_classifier --test
mage run iris_project iris_classifier --test --runtime-vars '{"max_depth": 1}'
```

Change `max_depth` for the other experiment runs. Remove `iris_predictions.csv`
before each run when checking whether a failed quality test blocked the exporter.

### RabbitMQ stream

Set `RABBITMQ_URL` in the shell that will run the scripts, or use the local
default broker URL. Start drivers with their name and binding pattern, then
start the dispatcher:

```powershell
python stream/driver.py Ravi "bangalore.koramangala.*"
python stream/dispatcher.py
```

The dispatcher publishes every two seconds and omits `zone` from every tenth
message. Valid deliveries are acknowledged; invalid ones are rejected without
requeue. Keep hosted broker URLs out of source control.

## Assignment status

This repository is being completed in stages. Results, screenshots, and report
answers will be added only after the corresponding pipeline has been run and
verified.
