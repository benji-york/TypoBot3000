import httpx
import pytest
import respx

from github_dispatch import trigger_workflow


@respx.mock
def test_trigger_workflow_sends_correct_request():
    route = respx.post(
        "https://api.github.com/repos/test-org/client-apps/actions/workflows/typobot.yml/dispatches"
    ).mock(return_value=httpx.Response(204))

    trigger_workflow(
        owner="test-org",
        repo="client-apps",
        token="ghp_fake",
        typo_description="on pricing page recieve should be receive",
        slack_channel="C123ABC",
        slack_thread_ts="1234567890.123456",
    )

    assert route.called
    request = route.calls[0].request
    import json
    body = json.loads(request.content)
    assert body["ref"] == "main"
    assert body["inputs"]["typo_description"] == "on pricing page recieve should be receive"
    assert body["inputs"]["slack_channel"] == "C123ABC"
    assert body["inputs"]["slack_thread_ts"] == "1234567890.123456"
    assert request.headers["authorization"] == "Bearer ghp_fake"


@respx.mock
def test_trigger_workflow_raises_on_failure():
    respx.post(
        "https://api.github.com/repos/test-org/client-apps/actions/workflows/typobot.yml/dispatches"
    ).mock(return_value=httpx.Response(403, json={"message": "forbidden"}))

    with pytest.raises(httpx.HTTPStatusError):
        trigger_workflow(
            owner="test-org",
            repo="client-apps",
            token="ghp_fake",
            typo_description="some typo",
            slack_channel="C123",
            slack_thread_ts="123.456",
        )
