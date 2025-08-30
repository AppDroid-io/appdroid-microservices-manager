# app/services/status.py
import asyncio

async def get_environment_status():
    """
    (EN) Simulates checking the development environment.
    (ES) Simula la comprobación del entorno de desarrollo.
    """
    await asyncio.sleep(1) # Simulate network delay
    return {
        "Java": {"name": "Java", "installed": True, "versionDetails": "21.0.8"},
        "Anaconda": {"name": "Anaconda", "installed": True, "versionDetails": "conda 25.5.1"},
        "Node.js": {"name": "Node.js", "installed": False, "versionDetails": "Not Found"},
        "Docker": {"name": "Docker", "installed": True, "versionDetails": "28.3.2"},
        "Git": {"name": "Git", "installed": True, "versionDetails": "2.45.0"}
    }