from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sys
import json
import uuid
from typing import Optional, List, Dict
from datetime import datetime
import asyncio

# Add parent directory to path to import create_map_poster
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import create_map_poster as cmp

app = FastAPI(title="Map Poster Generator API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount posters directory for serving generated images
POSTERS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "posters")
os.makedirs(POSTERS_DIR, exist_ok=True)
app.mount("/posters", StaticFiles(directory=POSTERS_DIR), name="posters")

# In-memory job storage (in production, use Redis or a database)
jobs = {}

class PosterRequest(BaseModel):
    city: str
    country: str
    theme: str = "feature_based"
    distance: int = 29000

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    message: str
    file_url: Optional[str] = None
    progress: int = 0

class ThemeInfo(BaseModel):
    name: str
    display_name: str
    description: str
    colors: Dict[str, str]

@app.get("/")
async def root():
    return {"message": "Map Poster Generator API", "version": "1.0.0"}

@app.get("/api/themes", response_model=List[ThemeInfo])
async def get_themes():
    """Get all available themes."""
    themes = []
    themes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "themes")

    if not os.path.exists(themes_dir):
        raise HTTPException(status_code=500, detail="Themes directory not found")

    for file in sorted(os.listdir(themes_dir)):
        if file.endswith('.json'):
            theme_name = file[:-5]
            theme_path = os.path.join(themes_dir, file)
            try:
                with open(theme_path, 'r') as f:
                    theme_data = json.load(f)
                    themes.append(ThemeInfo(
                        name=theme_name,
                        display_name=theme_data.get('name', theme_name),
                        description=theme_data.get('description', ''),
                        colors={
                            'bg': theme_data.get('bg', '#FFFFFF'),
                            'text': theme_data.get('text', '#000000'),
                            'water': theme_data.get('water', '#C0C0C0'),
                            'parks': theme_data.get('parks', '#F0F0F0'),
                            'road_motorway': theme_data.get('road_motorway', '#0A0A0A'),
                            'road_primary': theme_data.get('road_primary', '#1A1A1A'),
                        }
                    ))
            except Exception as e:
                print(f"Error loading theme {theme_name}: {e}")
                continue

    return themes

@app.post("/api/generate", response_model=JobStatus)
async def generate_poster(request: PosterRequest, background_tasks: BackgroundTasks):
    """Generate a map poster. Returns a job ID to track progress."""
    # Validate theme
    available_themes = cmp.get_available_themes()
    if request.theme not in available_themes:
        raise HTTPException(status_code=400, detail=f"Theme '{request.theme}' not found")

    # Validate distance
    if request.distance < 1000 or request.distance > 50000:
        raise HTTPException(status_code=400, detail="Distance must be between 1000 and 50000 meters")

    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "message": "Job queued for processing",
        "progress": 0,
        "request": request.dict()
    }

    # Add background task
    background_tasks.add_task(process_poster_generation, job_id, request)

    return JobStatus(
        job_id=job_id,
        status="queued",
        message="Job queued for processing",
        progress=0
    )

async def process_poster_generation(job_id: str, request: PosterRequest):
    """Background task to generate poster."""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Looking up coordinates..."
        jobs[job_id]["progress"] = 10

        # Load theme
        cmp.THEME = cmp.load_theme(request.theme)

        # Get coordinates
        coords = cmp.get_coordinates(request.city, request.country)
        jobs[job_id]["progress"] = 30
        jobs[job_id]["message"] = "Downloading map data..."

        # Generate output filename
        output_file = cmp.generate_output_filename(request.city, request.theme)
        jobs[job_id]["progress"] = 50
        jobs[job_id]["message"] = "Rendering map..."

        # Create poster
        cmp.create_poster(request.city, request.country, coords, request.distance, output_file)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Poster generated successfully"
        jobs[job_id]["file_url"] = f"/posters/{os.path.basename(output_file)}"

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Error: {str(e)}"
        jobs[job_id]["progress"] = 0
        print(f"Job {job_id} failed: {e}")
        import traceback
        traceback.print_exc()

@app.get("/api/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a poster generation job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        message=job["message"],
        file_url=job.get("file_url"),
        progress=job["progress"]
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
