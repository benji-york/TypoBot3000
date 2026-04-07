import os
import re

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from github_dispatch import trigger_workflow

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

GITHUB_PAT = os.environ.get("GITHUB_PAT", "")
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "TypoBot3000")


def typos_fixed() -> str:
    return "Number of typos fixed: 0"


def strip_mention(text: str) -> str:
    return re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()


@app.event("app_mention")
def handle_mention(event, say):
    channel = event["channel"]
    thread_ts = event["ts"]
    raw_text = event["text"]

    say(
        text="On it -- I'll post the PR here when it's ready.",
        thread_ts=thread_ts,
    )

    typo_description = strip_mention(raw_text)

    try:
        trigger_workflow(
            owner=GITHUB_REPO_OWNER,
            repo=GITHUB_REPO_NAME,
            token=GITHUB_PAT,
            typo_description=typo_description,
            slack_channel=channel,
            slack_thread_ts=thread_ts,
        )
    except Exception as e:
        say(
            text=f"Failed to dispatch workflow: {e}",
            thread_ts=thread_ts,
        )


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
