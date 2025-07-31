from fastapi import FastAPI
from .routes import health, markers, analyze, analyze_v2
import logging

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')

app = FastAPI(
    title="MarkerEngine Core API",
    description="Zentrales Nervensystem der MarkerEngine zur Übersetzung von Sprache in strukturierte Marker.",
    version="1.0.0"
)

app.include_router(health.router, tags=["Health"])
app.include_router(markers.router, prefix="/markers", tags=["Markers"])
app.include_router(analyze.router, prefix="/analyze", tags=["Analysis"])
app.include_router(analyze_v2.router, prefix="/analyze/v2", tags=["Analysis v2"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the MarkerEngine Core API"}