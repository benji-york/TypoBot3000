from app import strip_mention, typos_fixed
from unittest.mock import MagicMock, patch


def test_typos_fixed_returns_one():
    assert typos_fixed() == "Number of typos fixed: 1"


def test_strip_mention_removes_bot_id():
    assert strip_mention("<@U12345> on pricing page recieve") == "on pricing page recieve"


def test_strip_mention_handles_extra_whitespace():
    assert strip_mention("<@U12345>  fix the typo  ") == "fix the typo"


def test_strip_mention_no_mention():
    assert strip_mention("just some text") == "just some text"


def test_handle_mention_replies_and_dispatches(monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "ghp_fake")
    monkeypatch.setenv("GITHUB_REPO_OWNER", "test-org")
    monkeypatch.setenv("GITHUB_REPO_NAME", "TypoBot3000")

    # Re-import to pick up env vars
    import importlib
    import app as app_module
    importlib.reload(app_module)

    event = {
        "text": "<@U12345> on pricing page recieve should be receive",
        "channel": "C999",
        "ts": "111.222",
    }
    say = MagicMock()

    with patch("app.trigger_workflow") as mock_dispatch:
        app_module.handle_mention(event=event, say=say)

    say.assert_called_once_with(
        text="On it -- I'll post the PR here when it's ready.",
        thread_ts="111.222",
    )
    mock_dispatch.assert_called_once_with(
        owner="test-org",
        repo="TypoBot3000",
        token="ghp_fake",
        typo_description="on pricing page recieve should be receive",
        slack_channel="C999",
        slack_thread_ts="111.222",
    )


def test_handle_mention_reports_dispatch_failure(monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "ghp_fake")
    monkeypatch.setenv("GITHUB_REPO_OWNER", "test-org")
    monkeypatch.setenv("GITHUB_REPO_NAME", "TypoBot3000")

    import importlib
    import app as app_module
    importlib.reload(app_module)

    event = {"text": "<@U12345> typo", "channel": "C999", "ts": "111.222"}
    say = MagicMock()

    with patch("app.trigger_workflow", side_effect=Exception("API error")):
        app_module.handle_mention(event=event, say=say)

    assert say.call_count == 2
    say.assert_any_call(
        text="On it -- I'll post the PR here when it's ready.",
        thread_ts="111.222",
    )
    say.assert_any_call(
        text="Failed to dispatch workflow: API error",
        thread_ts="111.222",
    )
