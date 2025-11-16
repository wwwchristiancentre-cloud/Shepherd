from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import aiosqlite

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    async with aiosqlite.connect("shepherd.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

from .api.projects import router as projects_router
from .api.transcription import router as transcription_router

app.include_router(projects_router)
app.include_router(transcription_router)
