from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, youtube, videos
from pathlib import Path
import os

app = FastAPI(
    title="YouTube Video Scheduling Automation",
    description="Automate YouTube video uploads and scheduling from Google Drive",
    version="1.0.0"
)

# Add CORS middleware for better compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(youtube.router)
app.include_router(videos.router)

# Serve frontend
frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
async def root():
    """Serve frontend index page"""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "YouTube Video Scheduling Automation API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
