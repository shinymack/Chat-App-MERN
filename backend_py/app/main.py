import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import socketio

from app.core.config import settings
from app.api.routes import auth, messages, friends
from app.db.database import connect_to_mongo, close_mongo_connection
from app.sockets.socket_app import sio
from app.utils.logger import log

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    log.info("Starting up FastAPI application...")
    await connect_to_mongo()
    yield
    # Shutdown actions
    log.info("Shutting down FastAPI application...")
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan)

# Setup CORS mirroring the Node.js setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(friends.router, prefix="/api/friends", tags=["friends"])

# Merge FastAPI Application with Socket.IO ASGI App
sio_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Serve frontend build in production
if settings.node_env == "production":
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    
        @app.get("/{full_path:path}")
        async def catch_all(full_path: str):
            return FileResponse(os.path.join(frontend_dist, "index.html"))

# App needs to be run using `uvicorn app.main:sio_app --port $PORT`
