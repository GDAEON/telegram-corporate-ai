import json
import pytest
from backend.routers import metrics
from constants.request_models import Job


@pytest.mark.asyncio
async def test_metrics_returns_response():
    resp = await metrics.metrics()
    assert resp.media_type == metrics.CONTENT_TYPE_LATEST


@pytest.mark.asyncio
async def test_get_jobs_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics, "PROMETHEUS_JOBS_PATH", str(tmp_path / "jobs.json"))
    jobs = await metrics.get_jobs()
    assert jobs == []


@pytest.mark.asyncio
async def test_add_and_delete_job(tmp_path, monkeypatch):
    path = tmp_path / "jobs.json"
    monkeypatch.setattr(metrics, "PROMETHEUS_JOBS_PATH", str(path))

    result = await metrics.add_job(Job(job="test", targets=["localhost"]))
    assert result["status"] == "added"

    result2 = await metrics.add_job(Job(job="test", targets=["localhost"]))
    assert result2["status"] == "already exists"

    delete_res = await metrics.delete_job("test")
    assert delete_res["status"] == "deleted"
    with open(path) as f:
        data = json.load(f)
    assert data == []
