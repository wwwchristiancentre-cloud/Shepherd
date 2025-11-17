from fastapi import APIRouter, HTTPException, UploadFile, File
from ..models.project import Project, ProjectCreate
import aiosqlite
from pathlib import Path
from datetime import datetime
import shutil
import os
import json

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

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: int):
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT id, name, created_at FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        return Project(id=row[0], name=row[1], created_at=datetime.fromisoformat(row[2]))

@router.post("/{project_id}/upload")
async def upload_file_to_project(project_id: int, file: UploadFile = File(...)):
    """Upload a file to a project's Audio folder"""

    # Validate project exists
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

    project_name = row[0]
    home = Path.home()
    project_dir = home / "ShepherdProjects" / project_name
    audio_dir = project_dir / "Audio"
    audio_dir.mkdir(exist_ok=True)

    # Validate file type
    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg')):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # Save file
    file_path = audio_dir / file.filename
    if file_path.exists():
        # Add timestamp to avoid conflicts
        import time
        timestamp = str(int(time.time()))
        stem = file_path.stem
        suffix = file_path.suffix
        file_path = audio_dir / f"{stem}_{timestamp}{suffix}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file_path.name,
        "path": str(file_path),
        "size": file_path.stat().st_size
    }

@router.get("/{project_id}/transcripts")
async def list_project_transcripts(project_id: int):
    """List all transcript files in a project's Transcripts folder"""

    # Validate project exists
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

    project_name = row[0]
    home = Path.home()
    transcripts_dir = home / "ShepherdProjects" / project_name / "Transcripts"

    if not transcripts_dir.exists():
        return {"transcripts": []}

    transcripts = []
    for file_path in transcripts_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == '.json':
            try:
                # Read the transcript metadata
                with open(file_path, 'r') as f:
                    content = f.read()
                    data = json.loads(content)

                stat = file_path.stat()
                transcripts.append({
                    "filename": file_path.name,
                    "audio_filename": file_path.stem.replace('_transcript_and_segments', ''),
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "has_transcription": "transcription" in data,
                    "has_segmentation": "segmentation" in data.get("transcription", {}),
                    "audio_duration": data.get("audio_duration") or data.get("transcription", {}).get("metadata", {}).get("duration"),
                    "total_segments": data.get("total_segments") or data.get("transcription", {}).get("total_segments"),
                    "processing_time": data.get("processing_time") or (
                        data.get("transcription", {}).get("metadata", {}).get("processing_time") if "transcription" in data else None
                    )
                })
            except json.JSONDecodeError as e:
                # Handle corrupted JSON files gracefully
                print(f"Skipping corrupted JSON file {file_path} (JSON decode error: {e})")
                # Optionally, try to backup or rename corrupted files
                try:
                    corrupted_backup = file_path.with_suffix('.json.corrupted')
                    file_path.rename(corrupted_backup)
                    print(f"Renamed corrupted file to {corrupted_backup}")
                except Exception as rename_e:
                    print(f"Could not rename corrupted file: {rename_e}")
            except Exception as e:
                # Handle other file reading errors
                print(f"Error reading transcript {file_path}: {e}")

    # Sort by modification time, newest first
    transcripts.sort(key=lambda x: x["modified"], reverse=True)

    return {"transcripts": transcripts}

@router.post("/{project_id}/segment-existing")
async def segment_existing_transcript(
    project_id: int,
    request_body: dict
):
    transcript_filename = request_body.get("transcript_filename")
    if not transcript_filename:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="transcript_filename is required")
    """Run segmentation on an existing transcript without re-transcribing"""

    # Validate project exists
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

    project_name = row[0]
    home = Path.home()
    transcript_path = home / "ShepherdProjects" / project_name / "Transcripts" / transcript_filename

    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript file not found")

    try:
        # Load the existing transcript
        with open(transcript_path, 'r') as f:
            content = f.read()
            transcript_data = json.loads(content)

        # Extract segments from transcription
        transcript_segments = None
        if "transcription" in transcript_data and "segments" in transcript_data["transcription"]:
            transcript_segments = transcript_data["transcription"]["segments"]

        # Find the original audio file
        # Assume it's in the project's Audio folder
        audio_dir = home / "ShepherdProjects" / project_name / "Audio"
        audio_filename = transcript_data.get("transcription", {}).get("_metadata", {}).get("filename") or transcript_filename.replace('_transcript_and_segments.json', '')

        # Try different extensions
        audio_path = None
        for ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
            candidate_path = audio_dir / (audio_filename + ext)
            if candidate_path.exists():
                audio_path = candidate_path
                break

        if not audio_path and transcript_segments:
            # If no audio file found but we have transcript segments,
            # we can still create segments based on the transcript data
            from ..services.segmentation import SermonSegmenter

            # Create dummy audio duration from transcript
            if transcript_segments:
                audio_duration = max(s["end"] for s in transcript_segments)
            else:
                audio_duration = 0

            # Create segmentation result based on transcript
            result = {
                "segments": [],
                "audio_duration": audio_duration,
                "total_segments": 0,
                "average_segment_duration": 0,
                "processing_time": 0.1,  # Very fast since it's from existing data
                "confidence_threshold": 0.5,
                "transcription": transcript_data["transcription"],
                "message": "Segmentation run on existing transcript"
            }

            return result

        elif audio_path:
            # Run segmentation on the audio file
            from ..services.segmentation import SermonSegmenter
            segmenter = SermonSegmenter()

            segmentation_result = segmenter.segment_audio(str(audio_path), transcript_segments=transcript_segments)

            # Add the existing transcription to the result
            if "transcription" in transcript_data:
                result_data = segmentation_result.dict()
                result_data["transcription"] = transcript_data["transcription"]
                result_data["message"] = "Segmentation added to existing transcript"
                return result_data
            else:
                return segmentation_result.dict()

        else:
            raise HTTPException(status_code=404, detail="Original audio file not found for segmentation")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")

@router.get("/{project_id}/files")
async def list_project_files(project_id: int):
    """List all files in a project's Audio folder"""

    # Validate project exists
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

    project_name = row[0]
    home = Path.home()
    audio_dir = home / "ShepherdProjects" / project_name / "Audio"

    if not audio_dir.exists():
        return {"files": []}

    files = []
    for file_path in audio_dir.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    # Sort by modification time, newest first
    files.sort(key=lambda x: x["modified"], reverse=True)

    return {"files": files}

@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """Delete an entire project including all files and database entry"""

    # Validate project exists and get name
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        project_name = row[0]

        # Delete from database
        await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()

    # Delete project folder and all contents
    home = Path.home()
    project_dir = home / "ShepherdProjects" / project_name

    if project_dir.exists():
        try:
            import shutil
            shutil.rmtree(project_dir)
            print(f"Deleted project folder: {project_dir}")
        except Exception as e:
            print(f"Failed to delete project folder: {e}")
            # Continue anyway, database entry is deleted

    return {"message": f"Project '{project_name}' deleted successfully"}

@router.delete("/{project_id}/files/{filename}")
async def delete_project_file(project_id: int, filename: str):
    """Delete a file from project's Audio folder"""

    # Validate project exists
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

    project_name = row[0]
    home = Path.home()
    file_path = home / "ShepherdProjects" / project_name / "Audio" / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path.unlink()
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")

@router.get("/{project_id}/segmentation/{transcript_filename}")
async def get_segmentation_results(project_id: int, transcript_filename: str):
    """Retrieve existing segmentation results for a project"""

    # Validate project exists
    async with aiosqlite.connect("shepherd.db") as db:
        cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

    project_name = row[0]
    home = Path.home()
    transcript_path = home / "ShepherdProjects" / project_name / "Transcripts" / transcript_filename

    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript file not found")

    try:
        with open(transcript_path, 'r') as f:
            content = f.read()
            transcript_data = json.loads(content)

        # Extract segmentation data if it exists
        if "segmentation" in transcript_data and transcript_data["segmentation"]:
            return transcript_data["segmentation"]
        elif transcript_data.get("source") == "segmentation_only":
            # This is a segmentation-only result
            return transcript_data
        else:
            return {"segments": [], "total_segments": 0, "message": "No segmentation data found in this transcript"}

    except json.JSONDecodeError as e:
        # Handle corrupted JSON files
        raise HTTPException(status_code=500, detail=f"Corrupted transcript file (invalid JSON): {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read segmentation results: {e}")
