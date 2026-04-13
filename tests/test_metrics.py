from zbills.metrics import (
    ALL_METRICS,
    cost_llm_value_consistent,
    fields_dict_for,
    is_valid_metric,
    suggestion_code,
)


def test_all_metrics_count():
    assert len(ALL_METRICS) == 9


def test_is_valid_metric():
    assert is_valid_metric("time_saved")
    assert is_valid_metric("cost_llm")
    assert not is_valid_metric("unknown")


def test_cost_llm_value_consistent():
    assert cost_llm_value_consistent(1.0, 0.6, 0.4)
    assert cost_llm_value_consistent(1.01, 0.5, 0.5, tol=0.02)
    assert not cost_llm_value_consistent(2.0, 0.5, 0.5)


def test_fields_dict_for_cost_llm():
    fd = fields_dict_for("cost_llm")
    assert "provider" in fd["required"]
    assert "tokens_input" in fd["required"]
    assert "price_input_token" in fd["optional"]


def test_suggestion_code_contains_track():
    s = suggestion_code("cost_api", "my_agent")
    assert "zbills.track" in s
    assert "cost_api" in s
    assert "my_agent" in s
