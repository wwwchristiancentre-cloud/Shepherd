from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
from ..services.transcription import transcript_audio
import shutil
import tempfile
import os

router = APIRouter(prefix="/transcription")

@router.post("/", response_model=dict)
async def transcribe_audio(
    file: UploadFile = File(...),
    project_id: int = None
):
    """
    Upload and transcribe an audio file using local Whisper model
    Returns transcript with timestamps and segments
    """
    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Use MP3, WAV, M4A, FLAC, or OGG"
        )

    # Create temp file for uploaded audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_audio_path = temp_file.name

    try:
        # Transcribe the audio
        result = transcript_audio(temp_audio_path)

        # If project_id is provided, save transcript to project's Transcripts folder
        if project_id and not result.get("error"):
            await save_transcript_to_project(project_id, result, file.filename)

        return result

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_audio_path)
        except:
            pass

async def save_transcript_to_project(project_id: int, transcript_data: dict, original_filename: str):
    """
    Save transcript JSON to project's Transcripts folder
    """
    try:
        # Get project directory (implement based on your project structure)
        home = Path.home()
        projects_dir = home / "ShepherdProjects"

        # For now, we'll just store transcripts in a general location
        # In a full implementation, you'd look up the project by ID from DB
        transcripts_dir = projects_dir / "Transcripts"
        transcripts_dir.mkdir(exist_ok=True)

        # Save as JSON file
        transcript_filename = f"{Path(original_filename).stem}_transcript.json"
        transcript_path = transcripts_dir / transcript_filename

        import json
        with open(transcript_path, 'w') as f:
            json.dump(transcript_data, f, indent=2)

    except Exception as e:
        print(f"Failed to save transcript: {e}")
        # Don't fail the transcription if saving fails
