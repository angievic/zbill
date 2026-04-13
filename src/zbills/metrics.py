"""Catálogo de métricas Zpulse v2: impacto (3) + costo (6)."""

from __future__ import annotations

from typing import Any

IMPACT_METRICS = frozenset({"time_saved", "errors_reduced", "value_generated"})
COST_METRICS = frozenset(
    {
        "cost_llm",
        "cost_compute",
        "cost_api",
        "cost_storage",
        "cost_human",
        "cost_other",
    }
)
ALL_METRICS = IMPACT_METRICS | COST_METRICS


def category_for_metric(metric: str) -> str:
    return "impact" if metric in IMPACT_METRICS else "cost"


# required / optional por métrica (nombres de campo API)
FIELDS_SPEC: dict[str, dict[str, list[str]]] = {
    "time_saved": {
        "required": ["agent", "value", "unit"],
        "optional": ["hourly_rate", "metadata"],
    },
    "errors_reduced": {
        "required": ["agent", "value"],
        "optional": ["unit", "metadata"],
    },
    "value_generated": {
        "required": ["agent", "value"],
        "optional": ["unit", "metadata"],
    },
    "cost_llm": {
        "required": [
            "agent",
            "value",
            "provider",
            "model",
            "tokens_input",
            "tokens_output",
            "cost_input",
            "cost_output",
        ],
        "optional": [
            "price_input_token",
            "price_output_token",
            "is_estimated",
            "metadata",
        ],
    },
    "cost_compute": {
        "required": ["agent", "value"],
        "optional": ["unit", "provider", "hourly_rate", "is_estimated", "metadata"],
    },
    "cost_api": {
        "required": ["agent", "value"],
        "optional": ["unit", "provider", "is_estimated", "metadata"],
    },
    "cost_storage": {
        "required": ["agent", "value"],
        "optional": ["unit", "provider", "is_estimated", "metadata"],
    },
    "cost_human": {
        "required": ["agent", "value"],
        "optional": ["unit", "hourly_rate", "is_estimated", "metadata"],
    },
    "cost_other": {
        "required": ["agent", "value"],
        "optional": ["unit", "provider", "is_estimated", "metadata"],
    },
}


def fields_dict_for(metric: str) -> dict[str, list[str]]:
    spec = FIELDS_SPEC.get(metric, {"required": [], "optional": []})
    return {"required": list(spec["required"]), "optional": list(spec["optional"])}


def suggestion_code(metric: str, agent: str) -> str:
    """Snippet zbills.track(...) representativo por métrica."""
    a = agent
    if metric == "time_saved":
        return (
            f'zbills.track("time_saved", value=minutes, unit="minutes", agent="{a}", hourly_rate=45)'
        )
    if metric == "errors_reduced":
        return f'zbills.track("errors_reduced", value=1, agent="{a}")'
    if metric == "value_generated":
        return f'zbills.track("value_generated", value=amount, unit="usd", agent="{a}")'
    if metric == "cost_llm":
        return (
            f'zbills.track("cost_llm", value=total_cost, agent="{a}", provider="openai", '
            f'model="gpt-4o", tokens_input=usage.prompt_tokens, tokens_output=usage.completion_tokens, '
            f"cost_input=prompt_cost, cost_output=completion_cost)"
        )
    if metric == "cost_compute":
        return (
            f'zbills.track("cost_compute", value=instance_cost, unit="usd", agent="{a}", '
            f'provider="aws", is_estimated=True)'
        )
    if metric == "cost_api":
        return (
            f'zbills.track("cost_api", value=call_cost, unit="usd", agent="{a}", '
            f'provider="stripe", is_estimated=False)'
        )
    if metric == "cost_storage":
        return (
            f'zbills.track("cost_storage", value=gb_month, unit="usd", agent="{a}", '
            f'provider="aws", is_estimated=True)'
        )
    if metric == "cost_human":
        return (
            f'zbills.track("cost_human", value=hours, unit="hours", agent="{a}", '
            f"hourly_rate=75, is_estimated=True)"
        )
    if metric == "cost_other":
        return (
            f'zbills.track("cost_other", value=fee, unit="usd", agent="{a}", '
            f'provider="datadog", is_estimated=True)'
        )
    return f'zbills.track("{metric}", value=..., agent="{a}")'


def is_valid_metric(m: str) -> bool:
    return m in ALL_METRICS


def cost_llm_value_consistent(
    value: float, cost_input: float, cost_output: float, tol: float = 0.01
) -> bool:
    """API: `value` debe alinearse con cost_input + cost_output (tolerancia típica 0.01)."""
    return abs(float(value) - (float(cost_input) + float(cost_output))) <= tol
