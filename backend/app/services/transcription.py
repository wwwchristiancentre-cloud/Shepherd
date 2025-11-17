# FR-002: Local Audio Transcription Implementation
# Uses OpenAI's Whisper model for local transcription

try:
    import whisper
    import time
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: OpenAI Whisper not available. Install with: pip install openai-whisper torch numpy")

# Global model instance (loaded once)
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if not WHISPER_AVAILABLE:
        raise Exception("OpenAI Whisper not installed. Run: pip install openai-whisper torch numpy")

    if _whisper_model is None:
        print("Loading Whisper medium model (this may take several minutes on first run)...")
        start_time = time.time()
        try:
            # Download and load medium model locally (balances accuracy vs speed)
            _whisper_model = whisper.load_model("medium", download_root="./backend/models")
            load_time = time.time() - start_time
            print(".2f")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            print("Make sure you have sufficient disk space (~5GB) and a stable internet connection")
            raise
    return _whisper_model

def transcript_audio(audio_path: str, language: str = None) -> dict:
    """
    Transcribe audio file using local OpenAI Whisper model
    Returns transcript with timestamps and segments as required by FR-002
    """
    if not WHISPER_AVAILABLE:
        return {
            "transcripts": [{"text": "OpenAI Whisper not installed. Please install dependencies first."}],
            "segments": [],
            "error": "Missing dependencies: openai-whisper, torch, numpy",
            "metadata": {"model": "unavailable", "processing_time": 0}
        }

    model = get_whisper_model()

    try:
        print(f"Starting transcription for: {audio_path}")
        start_time = time.time()

        # Prepare transcription parameters
        if language and language.lower() == "english":
            # Force English for better accuracy
            result = model.transcribe(audio_path, language="english")
        elif language and language.lower() != "auto":
            # Force specific language
            result = model.transcribe(audio_path, language=language)
        else:
            # Auto-detect language (default behavior)
            result = model.transcribe(audio_path)

        transcription_time = time.time() - start_time
        print(".2f")

        # Format results to match the expected structure for the frontend
        segments = []
        full_text = ""

        for segment in result["segments"]:
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip()
            })
            full_text += segment["text"] + " "

        return {
            "transcripts": [{"text": full_text.strip()}],
            "segments": segments,
            "metadata": {
                "model": "whisper-medium-local",
                "language": result.get("language", "auto-detected"),
                "duration": result.get("duration", 0),
                "processing_time": transcription_time
            }
        }

    except Exception as e:
        print(f"Transcription error for {audio_path}: {str(e)}")
        return {
            "transcripts": [{"text": f"Transcription failed: {str(e)}"}],
            "segments": [],
            "error": str(e),
            "metadata": {"model": "error", "processing_time": 0}
        }
