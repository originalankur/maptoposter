#!/usr/bin/env python3
"""
FastAPI backend server for Map Poster Generator
"""

import os
import json
import base64
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import create_map_poster
from create_map_poster import (
    get_available_themes,
    load_theme,
    get_coordinates,
    create_poster,
    generate_output_filename,
    POSTERS_DIR,
    FONTS
)

app = FastAPI(
    title="Map Poster Generator API",
    description="Generate beautiful, minimalist map posters for any city in the world",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend) in production
frontend_dist = Path(__file__).parent / "webapp" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


class PosterRequest(BaseModel):
    city: str = Field(..., description="City name (used for geocoding)")
    country: str = Field(..., description="Country name (used for geocoding)")
    theme: str = Field(default="terracotta", description="Theme name")
    distance: Optional[int] = Field(default=18000, description="Map radius in meters")
    width: Optional[float] = Field(default=12, description="Image width in inches")
    height: Optional[float] = Field(default=16, description="Image height in inches")
    latitude: Optional[float] = Field(default=None, description="Override latitude center point")
    longitude: Optional[float] = Field(default=None, description="Override longitude center point")
    display_city: Optional[str] = Field(default=None, description="Custom display name for city")
    display_country: Optional[str] = Field(default=None, description="Custom display name for country")
    font_family: Optional[str] = Field(default=None, description="Google Fonts family name")


class ThemeInfo(BaseModel):
    name: str
    description: Optional[str] = None
    preview_colors: Optional[List[str]] = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve frontend in production, API info in development"""
    frontend_dist = Path(__file__).parent / "webapp" / "dist"
    index_file = frontend_dist / "index.html"
    
    if index_file.exists():
        # Serve the frontend index.html
        return HTMLResponse(content=index_file.read_text(), status_code=200)
    else:
        # Development mode - return API info
        return HTMLResponse(
            content="""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5;">
                    <h1>🗺️ Map Poster Generator API</h1>
                    <p>Version: 1.0.0</p>
                    <p><a href="/docs" style="color: #6366f1; text-decoration: none;">📚 API Documentation</a></p>
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="color: #666;">⚠️ Note: Frontend not built. Run <code>cd webapp && npm run build</code> to build the web UI.</p>
                </body>
            </html>
            """,
            status_code=200
        )


@app.get("/api/themes", response_model=List[ThemeInfo])
async def get_themes():
    """Get all available themes"""
    themes = get_available_themes()
    theme_list = []
    
    for theme_name in themes:
        theme = load_theme(theme_name)
        preview_colors = [
            theme.get("bg"),
            theme.get("text"),
            theme.get("water"),
            theme.get("parks"),
            theme.get("road_motorway"),
        ]
        theme_list.append({
            "name": theme_name,
            "description": theme.get("description"),
            "preview_colors": preview_colors
        })
    
    return theme_list


@app.get("/api/posters")
async def list_posters():
    """List all generated posters"""
    if not os.path.exists(POSTERS_DIR):
        return []
    
    posters = []
    for file in sorted(os.listdir(POSTERS_DIR)):
        if file.endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(POSTERS_DIR, file)
            stat = os.stat(file_path)
            posters.append({
                "filename": file,
                "url": f"/api/posters/{file}",
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size_bytes": stat.st_size
            })
    
    return posters


@app.get("/api/posters/{filename}")
async def get_poster(filename: str):
    """Download a generated poster"""
    file_path = os.path.join(POSTERS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Poster not found")
    
    return FileResponse(
        file_path,
        media_type="image/png",
        filename=filename
    )


@app.post("/api/generate")
async def generate_poster(request: PosterRequest, background_tasks: BackgroundTasks):
    """Generate a map poster"""
    try:
        print(f"Generating poster for {request.city}, {request.country} with theme {request.theme}")
        
        if request.latitude and request.longitude:
            from lat_lon_parser import parse
            lat = parse(str(request.latitude))
            lon = parse(str(request.longitude))
            coords = [lat, lon]
        else:
            coords = get_coordinates(request.city, request.country)
        
        # Set the theme in the create_map_poster module
        create_map_poster.THEME = load_theme(request.theme)
        output_file = generate_output_filename(request.city, request.theme, "png")
        
        custom_fonts = None
        if request.font_family:
            from font_management import load_fonts
            custom_fonts = load_fonts(request.font_family)
            if not custom_fonts:
                print(f"⚠ Failed to load '{request.font_family}', falling back to Roboto")
        
        create_poster(
            city=request.city,
            country=request.country,
            point=coords,
            dist=request.distance,
            output_file=output_file,
            output_format="png",
            width=int(request.width) if request.width else 12,
            height=int(request.height) if request.height else 16,
            country_label=request.display_country,
            display_city=request.display_city,
            display_country=request.display_country,
            fonts=custom_fonts or FONTS
        )
        
        filename = os.path.basename(output_file)
        
        return {
            "success": True,
            "filename": filename,
            "url": f"/api/posters/{filename}",
            "message": "Poster generated successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/posters/{filename}")
async def delete_poster(filename: str):
    """Delete a generated poster"""
    file_path = os.path.join(POSTERS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Poster not found")
    
    os.remove(file_path)
    
    return {"success": True, "message": "Poster deleted successfully"}


@app.get("/api/search/cities")
async def search_cities(q: str, lang: str = 'en'):
    """Proxy endpoint for Nominatim city search
    
    Args:
        q: Search query (city name in any language)
        lang: Language for results (en, zh, ja, etc.)
    """
    if len(q) < 2:
        return []
    
    try:
        import requests
        
        # Support multiple languages for better search results
        # Remove language restriction to allow searching in any language
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': q,
                'format': 'json',
                'addressdetails': 1,
                'limit': 15,
                # Don't restrict language to allow searching in Chinese, Japanese, etc.
                # 'accept-language': lang
            },
            headers={
                'User-Agent': 'MapPosterGenerator/1.0 (Map Poster Creator)',
                'Accept': 'application/json',
                'Accept-Language': f'{lang},en;q=0.9'  # Prefer requested language, fallback to English
            },
            timeout=10
        )
        response.raise_for_status()
        
        # Filter to only show cities, towns, villages, and other populated places
        results = response.json()
        filtered_results = []
        
        for item in results:
            # Check if it's a populated place
            item_type = item.get('type', '')
            item_class = item.get('class', '')
            
            # Include various types of populated places
            if (item_type in ['city', 'town', 'village', 'hamlet', 'municipality', 
                             'borough', 'suburb', 'quarter', 'neighbourhood', 'administrative'] or
                item_class in ['place', 'boundary']):
                
                # Add display information for better UI
                address = item.get('address', {})
                display_parts = []
                
                # Try to get the city name
                city_name = (address.get('city') or 
                           address.get('town') or 
                           address.get('village') or
                           address.get('municipality') or
                           address.get('county') or
                           item.get('name'))
                
                if city_name:
                    filtered_results.append(item)
                    
                if len(filtered_results) >= 10:
                    break
        
        return filtered_results
    
    except requests.exceptions.Timeout:
        print(f"Timeout searching cities for query: {q}")
        raise HTTPException(status_code=504, detail="Search timeout - please try again")
    except requests.exceptions.RequestException as e:
        print(f"Request error searching cities: {e}")
        raise HTTPException(status_code=503, detail="City search service unavailable")
    except Exception as e:
        print(f"Error searching cities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search cities: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)