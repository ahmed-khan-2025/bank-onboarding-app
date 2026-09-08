from config import FLOWS
from services.flow_engine import first_incomplete, get_flow, validate_flow_definitions


def test_all_six_flows_exist_and_have_six_post_selection_steps():
    validate_flow_definitions()
    assert set(FLOWS) == {"SE", "ES", "PL"}
    for country in FLOWS:
        assert set(FLOWS[country]) == {"private", "business"}
        for flow in FLOWS[country].values():
            assert len(flow["steps"]) == 6


def test_country_specific_requirements_are_configured():
    se_private = get_flow("SE", "private")
    es_private = get_flow("ES", "private")
    pl_private = get_flow("PL", "private")
    assert "tax_residency" in [f["name"] for f in se_private["steps"][2]["fields"]]
    assert "tax_residency" in [f["name"] for f in es_private["steps"][1]["fields"]]
    assert "tax_residency" not in [f["name"] for f in pl_private["steps"][2]["fields"]]

    assert get_flow("SE", "business")["steps"][2]["integration"] == "ubo_kyc_sanctions"
    assert get_flow("ES", "business")["steps"][4]["integration"] == "business_final"
    assert get_flow("PL", "business")["steps"][4]["integration"] == "business_final"


def test_flow_engine():
    assert get_flow("SE", "private")["steps"][0]["integration"] == "identity"
    assert first_incomplete(6, {0, 1, 2}) == 3
    assert first_incomplete(6, set(range(6))) == 5
