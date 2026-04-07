import os
from unittest.mock import MagicMock, patch

# Set a dummy SLACK_BOT_TOKEN before app.py is imported during test collection.
# app.py creates a slack_bolt.App at module level which requires this env var
# and calls auth.test. We patch App to avoid the network call.
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test-token")

# Create a mock App instance where @app.event(...) acts as an identity decorator,
# so that handle_mention remains the real function after import/reload.
_mock_app_instance = MagicMock()
_mock_app_instance.event.return_value = lambda f: f

_app_patcher = patch("slack_bolt.App", return_value=_mock_app_instance)
_app_patcher.start()
