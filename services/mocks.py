"""Deterministic mock integration clients.

These are deliberately local and side-effect free. They mimic external service
boundaries without calling real KYC, registry, credit or banking systems.
"""
import uuid
from typing import Any, Callable


def _result(integration: str, status: str, code: str, data: dict[str, Any] | None = None):
    return {
        "integration": integration,
        "status": status,
        "code": code,
        "data": data or {},
        "request_id": str(uuid.uuid4()),
    }


def identity(data):
    identifier = str(next((data.get(k) for k in ("personal_number", "dni_nie", "pesel") if data.get(k)), "")).lower()
    scenario = str(data.get("identity_scenario", "success")).lower()
    if scenario in {"fail", "document_mismatch"} or "fail" in identifier:
        return _result("identity", "fail", "document_mismatch", {"verified": False, "identity_confidence": 0.12})
    if scenario in {"manual_review", "manual"} or "manual" in identifier:
        return _result("identity", "manual_review", "manual_identity_review", {"verified": False, "identity_confidence": 0.61})
    if scenario == "expired" or "expired" in identifier:
        return _result("identity", "fail", "expired_id", {"verified": False, "identity_confidence": 0.05})
    return _result("identity", "pass", "verified", {"verified": True, "identity_confidence": 0.99})


def address(data):
    scenario = str(data.get("address_scenario", "verified")).lower()
    raw = str(data.get("address", "")).lower()
    if scenario == "fail" or "invalid" in raw or "fail" in raw:
        return _result("address", "fail", "address_not_verified", {"verified": False, "address_confidence": 0.10})
    if scenario == "manual_review" or "manual" in raw:
        return _result("address", "manual_review", "address_manual_review", {"verified": False, "address_confidence": 0.58})
    return _result("address", "pass", "verified", {"verified": True, "address_confidence": 0.98})


def sanctions(data):
    pep = str(data.get("pep_declared", "no")).lower()
    if pep == "yes":
        return _result("sanctions", "manual_review", "possible_hit", {"pep": True, "sanctions": "no_hit"})
    return _result("sanctions", "pass", "no_hit", {"pep": False, "sanctions": "no_hit"})


def affordability(data):
    try:
        income = float(data.get("monthly_income", 0))
        expenses = float(data.get("monthly_expenses", data.get("housing_cost", 0)))
        debt = float(data.get("monthly_debt_payments", 0))
    except (ValueError, TypeError):
        return _result("affordability", "fail", "invalid_financials")
    disposable = income - expenses - debt
    if disposable < 0:
        return _result("affordability", "manual_review", "negative_disposable_income", {"income": income, "debt_flags": ["negative_disposable_income"], "disposable_income": disposable, "affordability_result": "not_affordable"})
    return _result("affordability", "pass", "affordable", {"income": income, "debt_flags": [], "disposable_income": disposable, "affordability_result": "affordable"})


def credit(data):
    scenario = str(data.get("credit_scenario", "good")).lower()
    try:
        income = float(data.get("monthly_income", 0))
        housing = float(data.get("housing_cost", data.get("monthly_expenses", 0)))
        debt = float(data.get("monthly_debt_payments", 0))
    except (ValueError, TypeError):
        return _result("credit", "fail", "invalid_financials", {"affordability_result": "invalid"})
    disposable = income - housing - debt
    affordability_result = "affordable" if disposable >= 0 else "not_affordable"
    if scenario in {"fail", "bad"}:
        return _result("credit", "fail", "debt_flags", {"score": 420, "debt_flags": ["high_debt"], "income": income, "disposable_income": disposable, "affordability_result": affordability_result, "decision_reason": "Credit bureau returned high debt flags"})
    if scenario in {"manual_review", "manual"}:
        return _result("credit", "manual_review", "borderline_score", {"score": 610, "debt_flags": ["borderline_debt_to_income"] if debt > income * 0.35 else [], "income": income, "disposable_income": disposable, "affordability_result": affordability_result, "decision_reason": "Borderline bureau score requires manual review"})
    if disposable < 0:
        return _result("credit", "manual_review", "negative_disposable_income", {"score": 760, "debt_flags": ["negative_disposable_income"], "income": income, "disposable_income": disposable, "affordability_result": affordability_result, "decision_reason": "Affordability rules require manual review"})
    return _result("credit", "pass", "credit_and_affordability_ok", {"score": 760, "debt_flags": [], "income": income, "disposable_income": disposable, "affordability_result": "affordable", "decision_reason": "Credit bureau and affordability passed"})


def registry(data):
    raw = " ".join(str(v).lower() for v in data.values())
    if any(x in raw for x in ("dissolved", "fail")):
        return _result("registry", "fail", "dissolved", {"active": False, "company_status": "dissolved"})
    if any(x in raw for x in ("unknown", "manual")):
        return _result("registry", "manual_review", "unknown_representative", {"active": True, "company_status": "unknown"})
    return _result("registry", "pass", "active_company", {"active": True, "company_status": "active_company", "directors": ["Demo Director"]})


def representative(data):
    representative_id = str(data.get("representative_id", "")).lower()
    if "fail" in representative_id or "expired" in representative_id:
        return _result("representative", "fail", "representative_identity_failed", {"identity": "failed", "signatory_authority": "unknown"})
    if "manual" in representative_id or data.get("authority") == "unknown":
        return _result("representative", "manual_review", "unknown_representative", {"identity": "manual_review", "signatory_authority": "unknown"})
    return _result("representative", "pass", "authorised", {"identity": "verified", "signatory_authority": "authorised"})


def ubo_kyc_sanctions(data):
    try:
        ownership = float(data.get("ubo_ownership", 0))
    except (ValueError, TypeError):
        ownership = 0
    if ownership <= 0:
        return _result("ubo_kyc_sanctions", "manual_review", "missing_ubo", {"ubo_risk": "missing_ubo"})
    if ownership > 100:
        return _result("ubo_kyc_sanctions", "fail", "invalid_ubo_ownership", {"ubo_risk": "invalid_ownership"})
    if str(data.get("pep_declared", "no")).lower() == "yes":
        return _result("ubo_kyc_sanctions", "manual_review", "possible_pep_hit", {"ubo_risk": "pep_review", "ownership": ownership})
    return _result("ubo_kyc_sanctions", "pass", "ubo_verified", {"ubo_risk": "low", "ownership": ownership, "kyc": "verified", "sanctions": "no_hit"})


def business_profile(data):
    if data.get("vat_status") == "invalid":
        return _result("business_profile", "fail", "invalid_tax_status", {"tax_flags": ["invalid_vat"]})
    if data.get("vat_status") == "manual":
        return _result("business_profile", "manual_review", "tax_status_manual_review", {"tax_flags": ["tax_review"]})
    return _result("business_profile", "pass", "profile_ok", {"business_activity": data.get("activity") or data.get("sector"), "tax_flags": []})


def business_credit(data):
    scenario = str(data.get("business_risk", "good")).lower()
    if scenario in {"bad", "fail"}:
        return _result("business_credit", "fail", "business_credit_failure", {"score": 350, "debt_flags": ["default"], "decision_reason": "Business credit risk failed"})
    if scenario in {"manual", "manual_review"}:
        return _result("business_credit", "manual_review", "business_risk_review", {"score": 590, "decision_reason": "Business risk requires manual review"})
    return _result("business_credit", "pass", "business_credit_ok", {"score": 780, "decision_reason": "Business credit and risk passed"})


def bank_account(data):
    scenario = str(data.get("bank_scenario", "verified")).lower()
    if scenario == "name_mismatch":
        return _result("bank_account", "manual_review", "name_mismatch", {"iban_verified": True})
    if scenario == "unreachable":
        return _result("bank_account", "manual_review", "unreachable", {"iban_verified": None, "retryable": True})
    return _result("bank_account", "pass", "iban_verified", {"iban_verified": True})


def business_final(data):
    """Composite final check for markets where business credit + IBAN are one step.

    It preserves separate result details while returning one deterministic outcome.
    """
    credit_result = business_credit(data)
    if credit_result["status"] != "pass":
        return credit_result
    return bank_account(data)


INTEGRATIONS: dict[str, Callable[[dict], dict]] = {
    "identity": identity,
    "address": address,
    "sanctions": sanctions,
    "affordability": affordability,
    "credit": credit,
    "registry": registry,
    "representative": representative,
    "ubo_kyc_sanctions": ubo_kyc_sanctions,
    "business_profile": business_profile,
    "business_credit": business_credit,
    "bank_account": bank_account,
    "business_final": business_final,
}


def run_integration(name, data):
    if name not in INTEGRATIONS:
        return _result(name, "fail", "integration_not_configured")
    try:
        return INTEGRATIONS[name](data)
    except Exception:
        return _result(name, "manual_review", "integration_error", {"decision_reason": "External check could not be completed"})
