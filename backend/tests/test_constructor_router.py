import types
import asyncio
import pytest
from backend.routers import constructor
from backend.constants.request_models import (
    SendTextMessageRequest,
    SendSystemMessageRequest,
    Chat,
)


@pytest.mark.asyncio
async def test_get_schema(monkeypatch):
    monkeypatch.setattr(constructor, "SCHEME", {"a": 1})
    resp = await constructor.get_schema()
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_messengers(monkeypatch):
    monkeypatch.setattr(constructor.db, "get_all_bot_users", lambda: [(1, 2, "n", "s")])
    result = await constructor.list_messengers()
    assert result["items"][0]["externalType"] == "employees"


@pytest.mark.asyncio
async def test_send_message(monkeypatch):
    req = SendTextMessageRequest(chat=Chat(externalId="1", messengerInstance="1", contact="1", messengerId="1"), text="hi")
    monkeypatch.setattr(constructor.db, "get_bot_token", lambda bot_id: "token")
    async def fake_send(*args, **kwargs):
        return {"status_code": 200, "body": {}}
    monkeypatch.setattr(constructor.sa, "send_message", fake_send)
    result = await constructor.send_message(req)
    assert result["externalId"] == "1"


@pytest.mark.asyncio
async def test_send_system_message_with_media(monkeypatch):
    req = SendSystemMessageRequest(
        chat=Chat(externalId="1", messengerInstance="1", contact="1", messengerId="1"),
        text="{\"event\": \"started\", \"req_id\": \"5\"}"
    )

    monkeypatch.setattr(constructor.db, "get_selected_project_id", lambda *a, **k: None)

    monkeypatch.setattr(
        constructor.rdb.Message,
        "get",
        staticmethod(lambda *a, **k: ("text", "user", [{"type": "Image", "url": "u", "mime": "m"}], "photo")),
    )
    monkeypatch.setattr(constructor.rdb.Message, "delete", lambda *a, **k: None)

    captured = {}

    async def fake_forward(body):
        captured["body"] = body

    monkeypatch.setattr(constructor.sa, "_forward_message", fake_forward)

    result = await constructor.send_system_message(req)
    await asyncio.sleep(0)

    assert captured["body"]["message"]["attachments"][0]["type"] == "Image"
    assert captured["body"]["externalItem"]["extraData"]["messageType"] == "photo"
    assert result["messengerId"] == "1"
