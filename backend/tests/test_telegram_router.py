import types
import pytest
from backend.routers import telegram


class FakeRequest:
    def __init__(self, data):
        self._data = data

    async def json(self):
        return self._data


@pytest.mark.asyncio
async def test_handle_webhook_unsupported(monkeypatch):
    monkeypatch.setattr(telegram.db, "get_bot_token", lambda bot_id: "token")
    monkeypatch.setattr(telegram.db, "get_bot_locale", lambda bot_id: "en")
    request = FakeRequest({"unknown": {}})
    resp = await telegram.handle_webhook(1, request)
    assert resp.status_code == 200
    assert resp.body
