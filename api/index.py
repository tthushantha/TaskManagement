"""
Vercel serverless entry point for Task Management Application
"""
import sys
import os
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Set environment variables for serverless
os.environ.setdefault("PYTHONPATH", str(root_dir))

# Create a basic FastAPI app first
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Task Management API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Try to import the main application
try:
    # Import all required modules first
    import database
    import models
    import schemas
    import config
    
    # Now import the main app
    from main import app as main_app
    
    # Copy all routes from main app
    for route in main_app.routes:
        app.router.routes.append(route)
    
    print("Main application loaded successfully")
    
except ImportError as e:
    print(f"Import error: {e}")
    @app.get("/error")
    async def error_info():
        return {"error": "Import failed", "details": str(e)}
        
except Exception as e:
    print(f"General error: {e}")
    @app.get("/error")
    async def error_info():
        return {"error": "Application failed to load", "details": str(e)}

# Vercel handler
handler = app
