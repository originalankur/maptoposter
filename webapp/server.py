#!/usr/bin/env python3
"""
Web UI backend for the City Map Poster Generator.

Wraps the existing `create_map_poster.py` CLI in a small FastAPI app so the
generator can be driven from a browser: pick a city, a scale (radius) and a
map theme, preview the rendered poster, then download it.

Each generation runs the CLI script as an isolated subprocess (rather than
importing its rendering internals), which sidesteps the module's global,
mutable THEME state and matplotlib's non-thread-safe global figure state
when multiple jobs run concurrently.
"""

import asyncio
import json
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
SCRIPT_PATH = REPO_ROOT / "create_map_poster.py"

sys.path.insert(0, str(REPO_ROOT))

import create_map_poster as cmp  # noqa: E402  (import after sys.path setup)

MEDIA_TYPES = {
    "png": "image/png",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
}

MIN_DISTANCE = 1000
MAX_DISTANCE = 30000
MIN_SIZE = 3.0
MAX_SIZE = 20.0

JOB_TTL_SECONDS = 60 * 60  # jobs older than this are dropped from memory


@dataclass
class Job:
    """In-memory record of a single poster generation run."""

    id: str
    status: Literal["pending", "running", "done", "error"] = "pending"
    message: str = "Queued..."
    log_tail: list = field(default_factory=list)
    result_path: Optional[Path] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


JOBS: dict[str, Job] = {}


def _prune_old_jobs() -> None:
    cutoff = time.time() - JOB_TTL_SECONDS
    stale = [job_id for job_id, job in JOBS.items() if job.created_at < cutoff]
    for job_id in stale:
        JOBS.pop(job_id, None)


class GenerateRequest(BaseModel):
    """Poster generation parameters submitted from the web form."""

    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    country_label: Optional[str] = Field(default=None, max_length=100)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    theme: str = "terracotta"
    distance: int = Field(default=18000, ge=MIN_DISTANCE, le=MAX_DISTANCE)
    width: float = Field(default=12, ge=MIN_SIZE, le=MAX_SIZE)
    height: float = Field(default=16, ge=MIN_SIZE, le=MAX_SIZE)
    output_format: Literal["png", "svg", "pdf"] = Field(default="png", alias="format")

    model_config = ConfigDict(populate_by_name=True)


class GeocodeRequest(BaseModel):
    """City/country pair to resolve into a center point."""

    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)


app = FastAPI(title="City Map Poster Generator")


@app.get("/")
async def index() -> FileResponse:
    """Serve the single-page web UI."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/themes")
async def list_themes() -> list:
    """Return every available theme with the colors needed to render a swatch."""
    themes = []
    for name in cmp.get_available_themes():
        theme_path = REPO_ROOT / cmp.THEMES_DIR / f"{name}.json"
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        themes.append(
            {
                "id": name,
                "name": data.get("name", name),
                "description": data.get("description", ""),
                "bg": data.get("bg", "#FFFFFF"),
                "text": data.get("text", "#000000"),
                "water": data.get("water", "#A8C4C4"),
                "parks": data.get("parks", "#E8E0D0"),
                "road_primary": data.get("road_primary", data.get("road_default", "#000000")),
            }
        )
    return themes


@app.post("/api/geocode")
async def geocode(req: GeocodeRequest) -> dict:
    """Resolve a city/country pair to a center point, so it can be shown and tweaked before generating."""
    try:
        latitude, longitude = await asyncio.to_thread(cmp.get_coordinates, req.city, req.country)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"latitude": latitude, "longitude": longitude}


@app.post("/api/jobs")
async def create_job(req: GenerateRequest) -> dict:
    """Kick off a poster generation job and return its id for polling."""
    available_themes = cmp.get_available_themes()
    if req.theme not in available_themes:
        raise HTTPException(status_code=400, detail=f"Unknown theme '{req.theme}'. Available: {', '.join(available_themes)}")
    if (req.latitude is None) != (req.longitude is None):
        raise HTTPException(status_code=400, detail="Provide both latitude and longitude, or neither.")

    _prune_old_jobs()

    job = Job(id=uuid.uuid4().hex)
    JOBS[job.id] = job
    asyncio.create_task(_run_job(job, req))
    return {"id": job.id}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    """Poll the status of a generation job."""
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "id": job.id,
        "status": job.status,
        "message": job.message,
        "error": job.error,
        "preview_url": None,
        "download_url": None,
    }
    if job.status == "done" and job.result_path is not None:
        response["preview_url"] = f"/api/jobs/{job.id}/preview"
        response["download_url"] = f"/api/jobs/{job.id}/download"
    return response


def _resolved_job_file(job_id: str) -> Path:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "done" or job.result_path is None or not job.result_path.exists():
        raise HTTPException(status_code=409, detail=f"Job is '{job.status}', no file is ready yet")
    return job.result_path


@app.get("/api/jobs/{job_id}/preview")
async def preview(job_id: str) -> FileResponse:
    """Serve the generated poster inline, for display in the browser."""
    path = _resolved_job_file(job_id)
    media_type = MEDIA_TYPES.get(path.suffix.lstrip("."), "application/octet-stream")
    return FileResponse(path, media_type=media_type)


@app.get("/api/jobs/{job_id}/download")
async def download(job_id: str) -> FileResponse:
    """Serve the generated poster as a downloadable attachment."""
    path = _resolved_job_file(job_id)
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


_SAVED_RE = re.compile(r"Poster saved as (?P<path>.+)$")


async def _run_job(job: Job, req: GenerateRequest) -> None:
    """Run `create_map_poster.py` as a subprocess and track its progress on the job."""
    job.status = "running"
    job.message = "Starting..."

    args = [
        sys.executable,
        str(SCRIPT_PATH),
        "--city", req.city,
        "--country", req.country,
        "--theme", req.theme,
        "--distance", str(req.distance),
        "--width", str(req.width),
        "--height", str(req.height),
        "--format", req.output_format,
    ]
    if req.country_label:
        args += ["--country-label", req.country_label]
    if req.latitude is not None and req.longitude is not None:
        args += ["--latitude", str(req.latitude), "--longitude", str(req.longitude)]

    env = {**os.environ, "PYTHONUNBUFFERED": "1"}

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=REPO_ROOT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
    except OSError as exc:
        job.status = "error"
        job.error = f"Failed to start generator process: {exc}"
        return

    saved_path: Optional[str] = None
    clean_error: Optional[str] = None
    assert proc.stdout is not None
    async for raw_line in proc.stdout:
        chunk = raw_line.decode("utf-8", errors="replace")
        for piece in chunk.replace("\r", "\n").split("\n"):
            piece = piece.strip()
            if not piece:
                continue
            job.message = piece
            job.log_tail.append(piece)
            job.log_tail[:] = job.log_tail[-20:]
            match = _SAVED_RE.search(piece)
            if match:
                saved_path = match.group("path").strip()
            if piece.startswith("✗ Error:"):
                clean_error = piece[len("✗ Error:"):].strip()

    returncode = await proc.wait()

    if returncode == 0 and saved_path:
        result_path = (REPO_ROOT / saved_path).resolve()
        if result_path.exists():
            job.result_path = result_path
            job.status = "done"
            job.message = "Done"
            return

    job.status = "error"
    job.error = clean_error or "\n".join(job.log_tail[-10:]) or f"Generator process exited with code {returncode}"


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
