from services.mocks import run_integration


def test_identity_success():
    result = run_integration("identity", {"personal_number": "19900101-1234"})
    assert result["status"] == "pass"
    assert result["code"] == "verified"


def test_identity_manual():
    result = run_integration("identity", {"personal_number": "manual"})
    assert result["status"] == "manual_review"


def test_identity_expired():
    result = run_integration("identity", {"personal_number": "expired"})
    assert result["status"] == "fail"
    assert result["code"] == "expired_id"


def test_credit_failure():
    result = run_integration("credit", {"credit_scenario": "bad"})
    assert result["status"] == "fail"


def test_bank_unreachable_is_manual():
    result = run_integration("bank_account", {"bank_scenario": "unreachable"})
    assert result["status"] == "manual_review"


def test_sanctions_pep_is_manual_review():
    result = run_integration("sanctions", {"pep_declared": "yes"})
    assert result["status"] == "manual_review"
    assert result["code"] == "possible_hit"


def test_ubo_missing_is_manual_review():
    result = run_integration("ubo_kyc_sanctions", {"ubo_ownership": "0", "pep_declared": "no"})
    assert result["status"] == "manual_review"
    assert result["code"] == "missing_ubo"


def test_business_credit_fail():
    result = run_integration("business_credit", {"business_risk": "fail"})
    assert result["status"] == "fail"


def test_business_final_uses_credit_before_bank():
    result = run_integration("business_final", {"business_risk": "fail", "bank_scenario": "verified"})
    assert result["status"] == "fail"


def test_business_final_bank_manual():
    result = run_integration("business_final", {"business_risk": "good", "bank_scenario": "unreachable"})
    assert result["status"] == "manual_review"
