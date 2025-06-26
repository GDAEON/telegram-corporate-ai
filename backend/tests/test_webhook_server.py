import types
import pytest

from backend.services import webhook_server


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.headers = {}
        self.content = b""

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


class FakeAsyncClient:
    def __init__(self, get_resp=None, post_resp=None):
        self.get_resp = get_resp
        self.post_resp = post_resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        return self.get_resp

    async def post(self, *args, **kwargs):
        return self.post_resp


@pytest.mark.asyncio
async def test_get_bot_id(monkeypatch):
    resp = FakeResponse({"ok": True, "result": {"id": 42}})
    monkeypatch.setattr(
        webhook_server,
        "httpx",
        types.SimpleNamespace(AsyncClient=lambda *a, **k: FakeAsyncClient(get_resp=resp)),
    )
    bot_id = await webhook_server.get_bot_id("token")
    assert bot_id == 42


@pytest.mark.asyncio
async def test_get_bot_name(monkeypatch):
    resp = FakeResponse({"ok": True, "result": {"username": "bot"}})
    monkeypatch.setattr(
        webhook_server,
        "httpx",
        types.SimpleNamespace(AsyncClient=lambda *a, **k: FakeAsyncClient(get_resp=resp)),
    )
    name = await webhook_server.get_bot_name("token")
    assert name == "bot"


@pytest.mark.asyncio
async def test_set_webhook(monkeypatch):
    resp = FakeResponse({"ok": True}, status_code=200)
    monkeypatch.setattr(
        webhook_server,
        "httpx",
        types.SimpleNamespace(AsyncClient=lambda *a, **k: FakeAsyncClient(post_resp=resp)),
    )
    result = await webhook_server.set_webhook("token", "http://url")
    assert result["status_code"] == 200
    assert result["body"]["ok"] is True


@pytest.mark.asyncio
async def test_delete_webhook(monkeypatch):
    resp = FakeResponse({"ok": True}, status_code=200)
    monkeypatch.setattr(
        webhook_server,
        "httpx",
        types.SimpleNamespace(AsyncClient=lambda *a, **k: FakeAsyncClient(post_resp=resp)),
    )
    result = await webhook_server.delete_webhook("token")
    assert result["status_code"] == 200
    assert result["body"]["ok"] is True
