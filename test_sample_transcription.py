import requests
import json
import os
from pathlib import Path

# This script shows you how to test the transcription functionality

def test_transcription_api():
    """Test the transcription API endpoint"""

    # Ensure we can find a test file (you can replace this with any audio file you have)
    test_file_path = None

    # Look for common test files in current directory
    current_dir = Path(".")
    test_files = [
        "sample.wav", "sample.mp3", "sample.m4a",
        "test.wav", "test.mp3", "test.m4a"
    ]

    for test_file in test_files:
        if (current_dir / test_file).exists():
            test_file_path = current_dir / test_file
            break

    if not test_file_path:
        print("❌ No test audio file found!")
        print("Create a test_WAV file first, or copy an audio file to this directory.")
        print("Supported formats: MP3, WAV, M4A, FLAC, OGG")
        return

    print(f"📁 Found test file: {test_file_path}")

    # Test the API
    try:
        url = "http://127.0.0.1:8000/transcription"

        with open(test_file_path, 'rb') as audio_file:
            files = {'file': (test_file_path.name, audio_file, 'audio/wav')}
            response = requests.post(url, files=files)

        print(f"📡 API Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Transcription successful!")
            print("💬 Full Transcript:", result['transcripts'][0]['text'][:200] + "..." if len(result['transcripts'][0]['text']) > 200 else result['transcripts'][0]['text'])
            print(f"⏱️  Processing time: {result['metadata']['processing_time']:.2f}s")
            print(f"🎙️  Detected language: {result['metadata']['language']}")
            print(f"📊 Segments: {len(result['segments'])} timestamped segments available")

            # Save results for inspection
            with open('transcription_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            print("💾 Saved detailed results to: transcription_result.json")
        else:
            print("❌ Transcription failed!")
            print("Response:", response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend!")
        print("Make sure to run: uvicorn backend.app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🎙️  Shepherd Transcription API Test")
    print("=" * 50)
    test_transcription_api()
