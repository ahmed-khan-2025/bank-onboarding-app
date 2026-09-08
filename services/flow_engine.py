from config import FLOWS


def get_flow(country, customer_type):
    try:
        return FLOWS[country][customer_type]
    except KeyError as exc:
        raise ValueError("Unsupported onboarding flow") from exc


def get_step(country, customer_type, index):
    flow = get_flow(country, customer_type)
    if index < 0 or index >= len(flow["steps"]):
        raise ValueError("Invalid step")
    return flow["steps"][index]


def first_incomplete(total_steps, completed_indices):
    for i in range(total_steps):
        if i not in completed_indices:
            return i
    return total_steps - 1


def validate_flow_definitions():
    assert set(FLOWS) == {"SE", "ES", "PL"}
    for country, customer_types in FLOWS.items():
        assert set(customer_types) == {"private", "business"}
        for flow in customer_types.values():
            assert len(flow["steps"]) == 6
            for step in flow["steps"]:
                assert step.get("title")
                assert step.get("fields")
                for field in step["fields"]:
                    assert field["name"] and field["label"] and field["type"]
