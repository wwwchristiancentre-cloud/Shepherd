from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pathlib import Path
from ..services.transcription import transcript_audio
from ..services.segmentation import SermonSegmenter
import shutil
import tempfile
import os
import json
import hashlib
import aiosqlite

router = APIRouter(prefix="/transcription")

@router.post("/", response_model=dict)
async def transcribe_audio(
    file: UploadFile = File(...),
    project_id: int = Form(None),
    language: str = Form("english")  # Default to English
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
        # Check if we have a cached result
        file_hash = get_file_hash(temp_audio_path)
        cache_result = await check_transcription_cache(file_hash, project_id)
        if cache_result:
            print(f"Using cached transcription for {file.filename}")
            return cache_result

        # Transcribe the audio (pass language parameter)
        result = await transcribe_audio_with_language(temp_audio_path, language)

        # If project_id provided, save audio file to project and cache results
        saved_audio_path = None
        if project_id:
            print(f"[AUDIO SAVE] Saving audio file to project {project_id}: {file.filename}")
            saved_audio_path = await save_audio_to_project(project_id, temp_audio_path, file.filename)
            if saved_audio_path:
                print(f"[SUCCESS] Saved audio: {saved_audio_path}")
            else:
                print(f"[FAILED] Audio file save failed!")
            await save_transcription_cache(file_hash, project_id, result, file.filename, saved_audio_path)
            # Save as segmentation-only file for later retrieval
            segmentation_only_result = {
                "segments": [],
                "audio_duration": result.get("audio_duration", 0),
                "total_segments": 0,
                "average_segment_duration": 0.0,
                "processing_time": result.get("processing_time", 0),
                "confidence_threshold": 0.3,
                "source": "transcription_only",
                "_saved_audio_path": saved_audio_path
            }
            await save_transcript_to_project(project_id, segmentation_only_result, file.filename)

        # Add saved file info to response
        if saved_audio_path:
            result["_saved_audio_path"] = saved_audio_path

        return result

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_audio_path)
        except:
            pass

@router.post("/segment", response_model=dict)
async def segment_audio(
    file: UploadFile = File(...),
    include_transcription: bool = True,
    project_id: int = Form(None)
):
    """
    Upload and segment an audio file to identify sermon parts
    Optionally includes transcription in the response
    Returns sermon segments with timestamps and classification
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
        # Initialize segmenter
        segmenter = SermonSegmenter()

        transcript_segments = None
        if include_transcription:
            # Get transcription first
            transcription_result = transcript_audio(temp_audio_path)
            if transcription_result.get("segments"):
                transcript_segments = transcription_result["segments"]

        # Perform segmentation
        segmentation_result = segmenter.segment_audio(
            temp_audio_path,
            transcript_segments=transcript_segments
        )

        # Convert to API response format
        response = {
            "segments": [
                {
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "duration": seg.duration,
                    "segment_type": seg.segment_type.value,
                    "confidence": seg.confidence,
                    "text": seg.text,
                    "energy_level": seg.energy_level,
                    "silence_duration": seg.silence_duration
                }
                for seg in segmentation_result.segments
            ],
            "audio_duration": segmentation_result.audio_duration,
            "total_segments": segmentation_result.total_segments,
            "average_segment_duration": segmentation_result.average_segment_duration,
            "processing_time": segmentation_result.processing_time,
            "confidence_threshold": segmentation_result.confidence_threshold
            # Removed audio_features to make it JSON serializable
        }

        # Include transcription if requested and available
        if include_transcription:
            response["transcription"] = transcription_result

        # If project_id is provided, save audio file and segmentation result to project directory
        saved_audio_path = None
        if project_id:
            saved_audio_path = await save_audio_to_project(project_id, temp_audio_path, file.filename)
            if saved_audio_path:
                print(f"[SUCCESS] Saved segmentation audio: {saved_audio_path}")

            # Save segmentation result as JSON file
            segmentation_data = response.copy()
            segmentation_data["_saved_audio_path"] = saved_audio_path
            segmentation_data["source"] = "segmentation_only"
            await save_transcript_to_project(project_id, segmentation_data, file.filename)

        # Add saved file info to response
        if saved_audio_path:
            response["_saved_audio_path"] = saved_audio_path

        return response

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_audio_path)
        except:
            pass

@router.post("/transcribe-and-segment", response_model=dict)
async def transcribe_and_segment_audio(
    file: UploadFile = File(...),
    project_id: int = Form(None)
):
    """
    Combined endpoint: Upload, transcribe, and segment an audio file
    Returns both transcription and segmentation results
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
        # Initialize segmenter
        segmenter = SermonSegmenter()

        # Transcribe the audio first
        transcription_result = transcript_audio(temp_audio_path)

        # Perform segmentation with transcription alignment
        transcript_segments = transcription_result.get("segments", []) if not transcription_result.get("error") else None
        segmentation_result = segmenter.segment_audio(
            temp_audio_path,
            transcript_segments=transcript_segments
        )

        # Combine results
        response = {
            "transcription": transcription_result,
            "segmentation": {
                "segments": [
                    {
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "duration": seg.duration,
                        "segment_type": seg.segment_type.value,
                        "confidence": seg.confidence,
                        "text": seg.text,
                        "energy_level": seg.energy_level,
                        "silence_duration": seg.silence_duration
                    }
                    for seg in segmentation_result.segments
                ],
                "audio_duration": segmentation_result.audio_duration,
                "total_segments": segmentation_result.total_segments,
                "average_segment_duration": segmentation_result.average_segment_duration,
                "processing_time": segmentation_result.processing_time,
                "confidence_threshold": segmentation_result.confidence_threshold
            }
        }

        # If project_id is provided, save audio file and combined result to project's directory
        saved_audio_path = None
        if project_id and not transcription_result.get("error"):
            saved_audio_path = await save_audio_to_project(project_id, temp_audio_path, file.filename)
            await save_transcript_to_project(project_id, response, file.filename)

        # Add saved file info to response
        if saved_audio_path:
            response["_saved_audio_path"] = saved_audio_path

        return response

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_audio_path)
        except:
            pass

# Caching and utility functions
async def transcribe_audio_with_language(audio_path: str, language: str = "english"):
    """Transcribe audio with language specification"""
    return transcript_audio(audio_path, language)

async def save_audio_to_project(project_id: int, audio_path: str, original_filename: str):
    """Save uploaded audio file to project's Audio folder"""
    try:
        # Get project name from database
        async with aiosqlite.connect("shepherd.db") as db:
            cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
            row = await cursor.fetchone()
            if not row:
                print(f"Project {project_id} not found for audio saving")
                return None

        project_name = row[0]
        home = Path.home()
        project_dir = home / "ShepherdProjects" / project_name
        audio_dir = project_dir / "Audio"
        audio_dir.mkdir(exist_ok=True)

        # Save file to project folder with unique name
        import time
        stem = Path(original_filename).stem
        suffix = Path(original_filename).suffix
        timestamp = str(int(time.time()))
        unique_filename = f"{stem}_{timestamp}{suffix}"
        permanent_path = audio_dir / unique_filename

        # Copy from temp to permanent location
        shutil.copy2(audio_path, permanent_path)

        print(f"Saved audio to project folder: {permanent_path}")
        print(f"Audio file size: {permanent_path.stat().st_size} bytes")
        return str(permanent_path)

    except Exception as e:
        import traceback
        print(f"Failed to save audio to project: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

def get_file_hash(file_path: str) -> str:
    """Generate hash of file contents for caching"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

async def check_transcription_cache(file_hash: str, project_id: int = None) -> dict | None:
    """Check if transcription result is cached"""
    if not project_id:
        return None

    try:
        home = Path.home()
        cache_dir = home / "ShepherdProjects" / ".cache"
        cache_dir.mkdir(exist_ok=True)

        cache_file = cache_dir / f"{file_hash}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    content = f.read()
                    cached_data = json.loads(content)
                print(f"Found cached transcription for hash {file_hash}")
                # Remove metadata from response but keep saved path if available
                response_data = cached_data.copy()
                if "_metadata" in response_data:
                    if response_data["_metadata"].get("saved_audio_path"):
                        response_data["_saved_audio_path"] = response_data["_metadata"]["saved_audio_path"]
                    del response_data["_metadata"]
                return response_data
            except json.JSONDecodeError as e:
                print(f"Corrupted cache file {cache_file}, ignoring: {e}")
                # Delete corrupted cache file
                try:
                    cache_file.unlink()
                    print(f"Deleted corrupted cache file: {cache_file}")
                except Exception as del_e:
                    print(f"Could not delete corrupted cache file: {del_e}")
                return None
    except Exception as e:
        print(f"Cache check failed: {e}")

    return None

async def save_transcription_cache(file_hash: str, project_id: int, result: dict, filename: str, saved_audio_path: str = None):
    """Save transcription result to cache"""
    try:
        home = Path.home()
        cache_dir = home / "ShepherdProjects" / ".cache"
        cache_dir.mkdir(exist_ok=True)

        cache_data = result.copy()
        cache_data["_metadata"] = {
            "project_id": project_id,
            "filename": filename,
            "saved_audio_path": saved_audio_path,
            "cached_at": json.dumps(None),  # Add timestamp if needed
            "file_hash": file_hash
        }

        cache_file = cache_dir / f"{file_hash}.json"
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"Cached transcription for {filename}")
    except Exception as e:
        print(f"Cache save failed: {e}")

async def save_transcript_to_project(project_id: int, transcript_data: dict, original_filename: str):
    """
    Save transcript JSON to project's Transcripts folder
    """
    try:
        # Get project name from database
        async with aiosqlite.connect("shepherd.db") as db:
            cursor = await db.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
            row = await cursor.fetchone()
            if not row:
                print(f"Project {project_id} not found for transcript saving")
                return

        project_name = row[0]
        home = Path.home()
        project_dir = home / "ShepherdProjects" / project_name
        transcripts_dir = project_dir / "Transcripts"
        transcripts_dir.mkdir(exist_ok=True)

        # Save as JSON file
        transcript_filename = f"{Path(original_filename).stem}_transcript_and_segments.json"
        transcript_path = transcripts_dir / transcript_filename

        import json
        with open(transcript_path, 'w') as f:
            json.dump(transcript_data, f, indent=2)

        print(f"Saved transcript to project folder: {transcript_path}")

    except Exception as e:
        print(f"Failed to save transcript: {e}")
        # Don't fail the transcription if saving fails
