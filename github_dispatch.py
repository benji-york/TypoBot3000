import httpx


def trigger_workflow(
    *,
    owner: str,
    repo: str,
    token: str,
    typo_description: str,
    slack_channel: str,
    slack_thread_ts: str,
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/typobot.yml/dispatches"
    response = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={
            "ref": "main",
            "inputs": {
                "typo_description": typo_description,
                "slack_channel": slack_channel,
                "slack_thread_ts": slack_thread_ts,
            },
        },
    )
    response.raise_for_status()
