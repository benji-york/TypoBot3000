# TypoBot3000 Design Spec

## Overview

A Slack bot that takes typo reports from users and autonomously fixes them by creating a tested PR. User @-mentions the bot with a description of the typo, and the bot finds the file, writes a failing test, fixes the typo, verifies the test passes, and opens a PR.

## Target Repo

`client-apps` (frontend) — this repo has a rich history of typo fixes in user-facing text and is where visible typos are most commonly reported.

## Architecture

```
User @-mentions TypoBot3000 in Slack
  -> Bolt app (Python, Railway) parses message
  -> Triggers workflow_dispatch on client-apps GHA
    -> claude-code-action: find file, write failing test, fix typo, verify test passes
    -> If success: push branch + open PR, post PR link to Slack thread
    -> If failure: post failure summary to Slack thread (no PR)
```

### Components

1. **Slack Bolt app** — Python, deployed on Railway. Event listener + GitHub/Slack API glue.
2. **GHA workflow** — `typobot.yml` in `client-apps`. Runs `claude-code-action`.
3. **Slack callback step** — Final step in the GHA workflow. Posts result back to Slack thread.

## Component Details

### 1. Slack Bolt App

**Location:** `/Users/benji/work/TypoBot3000/1`

**Behavior:**
- Listens for `app_mention` events
- Replies in-thread immediately: "On it -- I'll post the PR here when it's ready."
- Calls `POST /repos/{owner}/client-apps/actions/workflows/typobot.yml/dispatches` with inputs:
  - `typo_description`: raw Slack message text (with bot mention stripped)
  - `slack_channel`: channel ID for reply
  - `slack_thread_ts`: thread timestamp for reply
- No database, no persistent state

**Dependencies:**
- `slack-bolt` (Slack framework)
- `requests` or `httpx` (GitHub API call)

**Deploy:** Railway via MCP tooling. Single always-on service (socket mode requires a persistent WebSocket connection).

### 2. GHA Workflow (`typobot.yml`)

**Location:** `client-apps/1/.github/workflows/typobot.yml`

**Trigger:** `workflow_dispatch`

**Inputs:**
- `typo_description` (string, required) — the user's typo report
- `slack_channel` (string, required) — channel ID for Slack callback
- `slack_thread_ts` (string, required) — thread timestamp for Slack callback

**Steps:**

1. **Checkout** `client-apps` repo
2. **Run claude-code-action** with prompt:
   ```
   A user reported the following typo: {typo_description}

   Your task:
   1. Find the file containing the incorrect text
   2. Write a test that asserts the correct text is present (this test should FAIL against the current code)
   3. Verify the test fails
   4. Fix the typo
   5. Verify the test passes
   6. Open a PR with the fix
   ```
3. **On success:** Post to Slack thread with PR URL
4. **On failure:** Post to Slack thread with failure summary

### 3. Slack Callback (GHA steps)

The final steps of the GHA workflow handle Slack notification directly using `curl` and the Slack API (`chat.postMessage`). The channel and thread_ts are passed as workflow inputs from the Bolt app, so no state management is needed.

**Success message:** "PR ready: {pr_url}"

**Failure message:** "I couldn't fix this one. Here's what happened: {error_summary}"

## Secrets & Config

### Railway (Bolt app)
- `SLACK_BOT_TOKEN` — Bot User OAuth Token (xoxb-...)
- `SLACK_SIGNING_SECRET` — For verifying Slack request signatures
- `SLACK_APP_TOKEN` — App-level token for socket mode (xapp-...), if using socket mode
- `GITHUB_PAT` — Personal access token with `actions:write` scope on client-apps

### GHA (client-apps)
- `ANTHROPIC_API_KEY` — For claude-code-action
- `SLACK_BOT_TOKEN` — For the callback step to post to Slack

## Slack App Configuration

### Required Bot Token Scopes
- `app_mentions:read` — receive @-mention events
- `chat:write` — post messages/replies

### Event Subscriptions
- `app_mention` — triggers when someone @-mentions the bot

### Socket Mode vs HTTP
For v1, use **socket mode** (`SLACK_APP_TOKEN`). This avoids needing a public URL for event subscriptions and simplifies the Railway setup. The Bolt app opens a WebSocket to Slack rather than exposing an HTTP endpoint.

## Data Flow (detailed)

1. User posts in Slack: `@TypoBot3000 on the pricing page it says "recieve" instead of "receive"`
2. Slack sends `app_mention` event to Bolt app (via socket mode)
3. Bolt app:
   a. Replies in thread: "On it -- I'll post the PR here when it's ready."
   b. Strips bot mention from message text
   c. POSTs to GitHub API: `workflow_dispatch` with `typo_description`, `slack_channel`, `slack_thread_ts`
4. GHA workflow starts on a runner
5. `claude-code-action` receives the prompt, searches the repo, writes a test, fixes the typo, opens a PR
6. GHA success step: calls Slack `chat.postMessage` with PR URL in the original thread
7. (Or) GHA failure step: calls Slack `chat.postMessage` with error summary in the original thread

## Scope

### In Scope (v1)
- Single repo: `client-apps`
- @-mention interaction model
- Autonomous test-write-fix-PR cycle via claude-code-action
- Success/failure notification back to Slack thread
- Socket mode (no public URL needed)

### Out of Scope (v1)
- Multi-repo support
- CLAUDE.md repo guidance
- PR reviewer auto-assignment
- Rate limiting, queuing, deduplication
- Slash commands
- Draft PRs on failure
