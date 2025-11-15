from fastapi import APIRouter, HTTPException
from ..models.project import Project, ProjectCreate
import aiosqlite
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/projects")

@router.post("/", response_model=Project)
async def create_project(project: ProjectCreate):
    # Create folders
    home = Path.home()
    shepherd_projects = home / "ShepherdProjects"
    shepherd_projects.mkdir(exist_ok=True)
    project_dir = shepherd_projects / project.name
    if project_dir.exists():
        raise HTTPException(status_code=400, detail="Project folder already exists")
    project_dir.mkdir()
    (project_dir / "Audio").mkdir()
    (project_dir / "Video").mkdir()
    (project_dir / "Exports").mkdir()
    (project_dir / "Transcripts").mkdir()

    # Save to DB
    async with aiosqlite.connect("shepherd.db") as db:
        try:
            cursor = await db.execute("INSERT INTO projects (name) VALUES (?)", (project.name,))
            await db.commit()
            project_id = cursor.lastrowid
        except aiosqlite.IntegrityError:
            raise HTTPException(status_code=400, detail="Project name already exists")

    return Project(id=project_id, name=project.name, created_at=datetime.now())

@router.get("/", response_model=list[Project])
async def get_projects():
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT id, name, created_at FROM projects ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        projects = [Project(id=row[0], name=row[1], created_at=datetime.fromisoformat(row[2])) for row in rows]
    return projects
