# bank-onboarding-app

A small Flask + SQLite onboarding application demonstrating six configurable customer journeys:

- Sweden private individual
- Sweden business
- Spain private individual
- Spain business
- Poland private individual
- Poland business


## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

Run tests:

```bash
python -m pytest -q
```

### Why configuration-driven flows?

Country-specific behaviour is data, not controller branching. Adding a new country or customer type should mostly require a new flow definition and any genuinely new integration adapter. This avoids a large nested `if/elif` tree.

### Data model

- `applications`: selected flow, lifecycle status, final decision and timestamps.
- `steps`: completed step state and answers.
- `integration_results`: integration outcome, structured result and request ID.
- `audit_events`: non-sensitive operational events and outcomes.

Customer answers are not copied into audit events. The audit trail contains event type, integration, result/code and request/event identifiers rather than raw identifiers or financial answers.

## Tests

Tests cover:

- all six flow definitions and country-specific requirements;
- flow transitions / first incomplete step;
- identity, sanctions, UBO, credit, business-credit and bank mock outcomes;
- approved/manual/rejected decision precedence;
- server-side validation and a complete private journey;
- Spain private tax residency;
- signed resumability.