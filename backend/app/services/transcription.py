def transcript_audio(audio_path: str) -> dict:
    # Stub: Mock transcript since models not loaded yet
    # TODO: Load Whisper model and transcribe
    return {
        "transcripts": [{"start": 0, "end": 10, "text": f"Mock transcript for {audio_path}"}],
        "segments": []
    }
