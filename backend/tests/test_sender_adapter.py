import types
import pytest

from backend.services import sender_adapter


class FakeResponse:
    def __init__(self, data=None, status_code=200, content=b"", headers=None):
        self._data = data or {}
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


class FakeAsyncClient:
    def __init__(self, get_resp=None, post_resp=None):
        self.get_resp = get_resp
        self.post_resp = post_resp
        self.last_post = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, *args, **kwargs):
        return self.get_resp

    async def post(self, url, json=None, data=None, files=None):
        self.last_post = {"url": url, "json": json, "data": data, "files": files}
        return self.post_resp


@pytest.mark.asyncio
async def test_send_message(monkeypatch):
    client = FakeAsyncClient(post_resp=FakeResponse({"ok": True}, 200))
    monkeypatch.setattr(
        sender_adapter,
        "httpx",
        types.SimpleNamespace(AsyncClient=lambda *a, **k: client),
    )
    res = await sender_adapter.send_message("token", 1, "hello")
    assert res["status_code"] == 200
    assert client.last_post["json"]["text"] == "hello"


@pytest.mark.asyncio
async def test_send_media(monkeypatch):
    get_resp = FakeResponse(content=b"data", headers={"Content-Disposition": 'attachment; filename="f.txt"'})
    post_resp = FakeResponse({"ok": True}, 200)
    client = FakeAsyncClient(get_resp=get_resp, post_resp=post_resp)
    monkeypatch.setattr(
        sender_adapter,
        "httpx",
        types.SimpleNamespace(AsyncClient=lambda *a, **k: client),
    )
    res = await sender_adapter.send_media(
        "token",
        1,
        "Image",
        "http://example.com/f.txt",
        "text/plain",
        "caption",
    )
    assert res["status_code"] == 200
    assert "photo" in client.last_post["files"]
