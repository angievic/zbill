from zbills.rules import detect_cost_snippet


def test_detect_llm_sdk():
    code = "resp = openai.chat.completions.create(model='gpt-4o', messages=[])"
    sugs = detect_cost_snippet(code, agent="agent")
    metrics = {s.metric for s in sugs}
    assert "cost_llm" in metrics


def test_detect_cost_api_http():
    code = "r = requests.post('https://api.stripe.com/v1/charges', data=payload)"
    sugs = detect_cost_snippet(code, agent="x")
    assert any(s.metric == "cost_api" for s in sugs)


def test_detect_storage():
    code = "s3 = boto3.client('s3'); s3.upload_file('a', 'b', 'c')"
    sugs = detect_cost_snippet(code, agent="x")
    assert any(s.metric == "cost_storage" for s in sugs)
