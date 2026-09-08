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
