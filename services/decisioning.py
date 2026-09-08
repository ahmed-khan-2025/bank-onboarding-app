"""Pure deterministic decisioning policy."""


def decide(results):
    if not results:
        return "manual_review", "No external checks were recorded."

    failures = [r for r in results if r.get("status") == "fail"]
    reviews = [r for r in results if r.get("status") == "manual_review"]

    if failures:
        reasons = [r.get("data", {}).get("decision_reason") or r.get("code", "check failed").replace("_", " ").title() for r in failures]
        return "rejected", "; ".join(reasons)
    if reviews:
        reasons = [r.get("data", {}).get("decision_reason") or r.get("code", "manual review").replace("_", " ").title() for r in reviews]
        return "manual_review", "; ".join(reasons)
    return "approved", "All mandatory checks passed."
