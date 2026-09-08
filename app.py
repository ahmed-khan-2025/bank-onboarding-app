import json
import os
import re
import uuid

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from config import FLOWS
from db import (
    create_application,
    finalize,
    get_application,
    init_db,
    save_integration,
    save_step,
)
from services.decisioning import decide
from services.flow_engine import first_incomplete, get_flow
from services.mocks import run_integration

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
init_db()

COUNTRY_NAMES = {"SE": "Sweden", "ES": "Spain", "PL": "Poland"}
TYPE_NAMES = {"private": "Private", "business": "Business"}


@app.template_filter("fromjson")
def fromjson_filter(value):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}


@app.context_processor
def global_template_values():
    return {"country_names": COUNTRY_NAMES, "type_names": TYPE_NAMES}


def validate(step, form):
    errors = []
    answers = {}

    for field in step["fields"]:
        name = field["name"]
        label = field["label"]
        field_type = field["type"]

        if field_type == "checkbox":
            value = form.get(name) == "on"
            if field.get("required") and not value:
                errors.append(f"{label} is required.")
            answers[name] = value
            continue

        value = form.get(name, "").strip()

        if field.get("required") and not value:
            errors.append(f"{label} is required.")

        if value and field_type == "email":
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
                errors.append(f"{label} must be a valid email address.")

        if value and field_type == "number":
            try:
                number = float(value)
                if number < 0:
                    errors.append(f"{label} cannot be negative.")
                if name == "ubo_ownership" and number > 100:
                    errors.append("UBO ownership cannot exceed 100%.")
                if name == "dependants" and not number.is_integer():
                    errors.append("Dependants must be a whole number.")
            except ValueError:
                errors.append(f"{label} must be a number.")

        if field_type == "select" and value and value not in field.get("options", []):
            errors.append(f"Invalid value for {label}.")

        answers[name] = value

    return errors, answers


def load_context(app_id):
    record = get_application(app_id)
    if not record:
        abort(404)

    application = record["app"]
    flow = get_flow(application["country"], application["customer_type"])
    return record, application, flow


def all_steps_completed(record, flow):
    completed = {row["step_index"] for row in record["steps"]}
    return len(completed) == len(flow["steps"])


def decision_for(record):
    results = [json.loads(row["result_json"]) for row in record["results"]]
    return decide(results)


def resume_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="onboarding-resume")


def make_resume_token(app_id):
    return resume_serializer().dumps({"app_id": app_id})


def read_resume_token(token, max_age=86400):
    payload = resume_serializer().loads(token, max_age=max_age)
    return int(payload["app_id"])


@app.get("/")
def index():
    return render_template("index.html", flows=FLOWS)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start")
def start():
    country = request.form.get("country", "")
    customer_type = request.form.get("customer_type", "")

    if country not in FLOWS or customer_type not in FLOWS[country]:
        flash("Please choose a valid country and customer type.", "error")
        return redirect(url_for("index"))

    app_id = create_application(country, customer_type)
    return redirect(url_for("step", app_id=app_id, step_index=0))


@app.route("/applications/<int:app_id>/step/<int:step_index>", methods=["GET", "POST"])
def step(app_id, step_index):
    record, application, flow = load_context(app_id)

    if application["status"] == "completed":
        return redirect(url_for("complete", app_id=app_id))

    if step_index < 0 or step_index >= len(flow["steps"]):
        abort(404)

    # Prevent jumping ahead. Previously completed steps remain editable.
    completed = {row["step_index"] for row in record["steps"]}
    expected = first_incomplete(len(flow["steps"]), completed)
    if step_index > expected and step_index not in completed:
        flash("Please complete the current step first.", "error")
        return redirect(url_for("step", app_id=app_id, step_index=expected))

    current = flow["steps"][step_index]
    previous = {}
    for row in record["steps"]:
        if row["step_index"] == step_index:
            previous = json.loads(row["answers_json"])
            break

    if request.method == "POST":
        action = request.form.get("action", "continue")
        errors, answers = validate(current, request.form)

        if errors:
            return render_template(
                "step.html",
                application=application,
                flow=flow,
                step=current,
                step_index=step_index,
                errors=errors,
                values=answers,
            )

        save_step(app_id, step_index, answers, current.get("integration"))

        if current.get("integration"):
            # Integrations receive the complete application context, not only
            # the current step. This is important for affordability/credit
            # decisions that depend on income and debt inputs collected earlier.
            all_answers = {}
            refreshed = get_application(app_id)
            for saved_step in refreshed["steps"]:
                all_answers.update(json.loads(saved_step["answers_json"]))
            result = run_integration(current["integration"], all_answers)
            save_integration(app_id, result)

            if result["status"] != "pass":
                # A failed check is a rejection; a manual check enters manual review.
                decision = "rejected" if result["status"] == "fail" else "manual_review"
                reason = result.get("data", {}).get("decision_reason") or result["code"].replace("_", " ").title()
                finalize(app_id, decision, reason)
                return redirect(url_for("integration_result", app_id=app_id))

        if action == "save":
            flash("Your progress has been saved.", "success")
            return redirect(url_for("step", app_id=app_id, step_index=step_index))

        if step_index + 1 < len(flow["steps"]):
            return redirect(url_for("step", app_id=app_id, step_index=step_index + 1))
        return redirect(url_for("review", app_id=app_id))

    return render_template(
        "step.html",
        application=application,
        flow=flow,
        step=current,
        step_index=step_index,
        errors=[],
        values=previous,
    )


@app.get("/applications/<int:app_id>/integration-result")
def integration_result(app_id):
    record, application, flow = load_context(app_id)
    if not record["results"]:
        return redirect(url_for("review", app_id=app_id))

    latest = record["results"][-1]
    result = json.loads(latest["result_json"])
    return render_template(
        "step_result.html",
        application=application,
        flow=flow,
        result=result,
    )


@app.get("/applications/<int:app_id>/review")
def review(app_id):
    record, application, flow = load_context(app_id)

    if application["status"] == "completed":
        return redirect(url_for("complete", app_id=app_id))

    if not all_steps_completed(record, flow):
        completed = {row["step_index"] for row in record["steps"]}
        next_index = first_incomplete(len(flow["steps"]), completed)
        flash("Please complete all onboarding steps before review.", "error")
        return redirect(url_for("step", app_id=app_id, step_index=next_index))

    decision, reason = decision_for(record)
    return render_template(
        "review.html",
        application=application,
        flow=flow,
        steps=record["steps"],
        results=record["results"],
        audit=record["audit"],
        decision=decision,
        reason=reason,
    )


@app.post("/applications/<int:app_id>/submit")
def submit(app_id):
    record, application, flow = load_context(app_id)

    if not all_steps_completed(record, flow):
        abort(400, "Application is incomplete")

    decision, reason = decision_for(record)
    finalize(app_id, decision, reason)
    return redirect(url_for("complete", app_id=app_id))


@app.get("/applications/<int:app_id>/complete")
def complete(app_id):
    record, application, _ = load_context(app_id)
    if application["status"] != "completed":
        return redirect(url_for("review", app_id=app_id))
    return render_template("complete.html", application=application, record=record)


@app.get("/applications/<int:app_id>/resume-link")
def resume_link(app_id):
    record, application, flow = load_context(app_id)
    if application["status"] == "completed":
        return redirect(url_for("complete", app_id=app_id))
    token = make_resume_token(app_id)
    return render_template("resume.html", application=application, token=token, expires_hours=24)


@app.get("/resume/<token>")
def resume_token(token):
    try:
        app_id = read_resume_token(token)
    except SignatureExpired:
        return render_template("error.html", code=410, message="This resume link has expired."), 410
    except BadSignature:
        return render_template("error.html", code=400, message="This resume link is invalid."), 400

    record = get_application(app_id)
    if not record:
        abort(404)
    if record["app"]["status"] == "completed":
        return redirect(url_for("complete", app_id=app_id))
    flow = get_flow(record["app"]["country"], record["app"]["customer_type"])
    completed = {row["step_index"] for row in record["steps"]}
    next_index = first_incomplete(len(flow["steps"]), completed)
    return redirect(url_for("step", app_id=app_id, step_index=next_index))


@app.get("/applications/<int:app_id>/resume")
def resume_legacy(app_id):
    """Compatibility route; redirects to a signed resume-link page."""
    return redirect(url_for("resume_link", app_id=app_id))


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=str(error.description)), 400


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="The requested page was not found."), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
