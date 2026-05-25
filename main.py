"""
Minimal entry point for Render deployment
Starts uvicorn immediately without loading app2.py module-level code
"""
import os
import sys

# Use PORT from environment variable (Render sets this)
port = int(os.environ.get("PORT", 8000))

print(f"Starting FastAPI server on port {port}...")
print(f"Host: 0.0.0.0")
print(f"Environment: {'Render' if os.environ.get('RENDER') else 'Local'}")

# Import uvicorn first
import uvicorn

# Now import the app from app2.py
from app2 import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
