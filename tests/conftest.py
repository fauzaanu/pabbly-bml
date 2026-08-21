"""Shared fixtures.

`app.py` performs a Telegram call at import time, so the environment is pinned and
`requests.post` is patched before the module is first imported.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ENV = {
    "BML_API_KEY": "test-bml-key",
    "PABBLY_USERNAME": "test-user",
    "PABBLY_PASSWORD": "test-pass",
    "DEFAULT_REDIRECT_URL": "https://example.com/fallback",
    "TELEGRAM_BOT_TOKEN": "test-token",
    "TELEGRAM_CHAT_ID": "test-chat",
    "DOMAIN": "https://pay.example.com",
}
os.environ.update(ENV)

with patch("requests.post"):
    import app as app_under_test


def make_response(status_code: int = 200, json_body: object = None, text: str = "") -> MagicMock:
    """Build a stand-in for a requests.Response."""
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.json.return_value = {} if json_body is None else json_body
    return response


@pytest.fixture(autouse=True)
def env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Pin the environment every test runs against."""
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    return dict(ENV)


@pytest.fixture(autouse=True)
def telegram():
    """Never let a test reach the real Telegram API."""
    with patch("app.requests.post") as mocked:
        mocked.return_value = make_response(200)
        yield mocked


@pytest.fixture
def app_module():
    return app_under_test


@pytest.fixture
def client(app_module):
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


@pytest.fixture
def bml_api(app_module):
    """Patch the BML client the app holds; yields the mock."""
    with patch.object(app_under_test, "bml_instance") as mocked:
        yield mocked


@pytest.fixture
def pabbly_api(app_module):
    """Patch the Pabbly client the app holds; yields the mock."""
    with patch.object(app_under_test, "pabbly_instance") as mocked:
        yield mocked


@pytest.fixture
def pabbly():
    from Subscriptions.subscription import Subscription

    return Subscription("test-user", "test-pass")


@pytest.fixture
def bml():
    from bankofmaldives.bankofmaldives import BankofmaldivesAPI

    return BankofmaldivesAPI("test-bml-key")
