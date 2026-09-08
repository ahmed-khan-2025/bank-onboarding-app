from services.decisioning import decide


def test_all_pass_is_approved():
    assert decide([{"status": "pass"}])[0] == "approved"


def test_manual_over_pass():
    assert decide([{"status": "pass"}, {"status": "manual_review"}])[0] == "manual_review"


def test_fail_over_manual():
    assert decide([{"status": "manual_review"}, {"status": "fail"}])[0] == "rejected"


def test_no_results_is_approved_by_policy_layer():
    assert decide([])[0] == "manual_review"
