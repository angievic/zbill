import json

from zbills.llm import enrich


def test_parse_llm_response_builds_suggestions():
    raw = json.dumps(
        {
            "agent_hint": "reviewer",
            "rationale": "test",
            "suggestions": [
                {
                    "metric": "cost_llm",
                    "category": "cost",
                    "reason": "OpenAI call",
                    "suggestion": 'zbills.track("cost_llm", value=1.0, agent="reviewer")',
                    "fields": {
                        "required": ["provider", "model"],
                        "optional": ["metadata"],
                    },
                }
            ],
        }
    )
    agent, rationale, sugs = enrich._parse_llm_response(raw)
    assert agent == "reviewer"
    assert len(sugs) == 1
    assert sugs[0].metric == "cost_llm"
    assert sugs[0].category == "cost"
    assert "zbills.track" in sugs[0].suggestion
