from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from fastapi import Response, APIRouter
from fastapi.exceptions import HTTPException
from constants.prometheus_models import registry
from constants.request_models import Job
from config.settings import PROMETHEUS_JOBS_PATH
import json
import os

router = APIRouter(prefix="/metrics", tags=['Metrics'])

@router.get("/", description="Prometheus metrics endpoint")
async def metrics():
    """Expose application metrics in Prometheus format."""
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@router.get("/jobs", description="List scraping jobs configured for Prometheus")
async def get_jobs():
    """Return list of configured Prometheus jobs."""
    if not os.path.exists(PROMETHEUS_JOBS_PATH):
        return []

    with open(PROMETHEUS_JOBS_PATH, "r") as f:
        try:
            jobs = json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON format")

    return [
        {
            "job": entry["labels"].get("job"),
            "targets": entry["targets"]
        }
        for entry in jobs
    ]


@router.post("/job", description="Add a new Prometheus scraping job")
async def add_job(job: Job):
    """Add a scraping job to jobs.json if it does not exist."""
    jobs = []

    if os.path.exists(PROMETHEUS_JOBS_PATH):
        with open(PROMETHEUS_JOBS_PATH, "r") as f:
            jobs = json.load(f)

    for entry in jobs:
        if entry["labels"].get("job") == job.job:
            return {"status": "already exists"}

    jobs.append({
        "targets": job.targets,
        "labels": { "job": job.job }
    })

    with open(PROMETHEUS_JOBS_PATH, "w") as f:
        json.dump(jobs, f, indent=2)

    return {"status": "added", "job": job.job}


@router.delete("/job/{name}", description="Delete a Prometheus scraping job")
async def delete_job(name: str):
    """Remove job entry from jobs.json."""
    if not os.path.exists(PROMETHEUS_JOBS_PATH):
        raise HTTPException(status_code=404, detail="jobs.json not found")

    with open(PROMETHEUS_JOBS_PATH, "r") as f:
        jobs = json.load(f)

    original_count = len(jobs)
    jobs = [job for job in jobs if job["labels"].get("job") != name]

    if len(jobs) == original_count:
        raise HTTPException(status_code=404, detail=f"Job '{name}' not found")

    with open(PROMETHEUS_JOBS_PATH, "w") as f:
        json.dump(jobs, f, indent=2)

    return {"status": "deleted", "job": name}
