# app/main.py
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

log = logging.getLogger("uvicorn.error")

app = FastAPI(title="Gym Planner")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
try:
    from app.database import init_db
    init_db()
    log.info("Database initialized successfully.")
except Exception as e:
    log.exception("init_db failed: %s", e)

# Routers with safe loading
try:
    from app.routers import logs as logs_router
    app.include_router(logs_router.router)
except Exception:
    log.exception("Failed to include logs router")

try:
    from app.routers import meals as meals_router
    app.include_router(meals_router.router)
except Exception:
    log.exception("Failed to include meals router")

try:
    from app.routers import workouts as workouts_router
    app.include_router(workouts_router.router)
except Exception:
    log.exception("Failed to include workouts router")

try:
    from app.routers import templates as templates_router
    app.include_router(templates_router.router)
except Exception:
    log.exception("Failed to include templates router")

# Serve static frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Redirect root → frontend UI
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/frontend/index.html")
