import types
import pytest
from backend.routers import api


@pytest.mark.asyncio
async def test_bots_by_owner(monkeypatch):
    monkeypatch.setattr(api.db, "get_bots_by_owner_uuid", lambda owner_uuid: [(1, "Bot", "pass", "url")])
    result = await api.bots_by_owner("owner")
    assert result[0]["botName"] == "Bot"


@pytest.mark.asyncio
async def test_is_bot_verified(monkeypatch):
    monkeypatch.setattr(api.db, "is_bot_verified", lambda bot_id: True)
    assert await api.is_bot_verified(1) is True


@pytest.mark.asyncio
async def test_generate_invite(monkeypatch):
    monkeypatch.setattr(api.db, "bot_exists", lambda bot_id: True)
    monkeypatch.setattr(api.db, "create_pass_token", lambda bot_id: "uuid")
    result = await api.generate_invite(1)
    assert result == {"passUuid": "uuid"}
