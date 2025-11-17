#!/usr/bin/env python3
"""
Test script for sermon segmentation functionality
Use this to validate that the audio segmentation is working correctly
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.segmentation import SermonSegmenter
from app.services.transcription import transcript_audio

def test_segmentation():
    """Test segmentation with a sample audio file"""
    print("Testing Sermon Segmentation...")

    # Check for test audio file
    test_audio_paths = [
        "test_audio.wav",
        "sample_sermon.wav",
        "test_sermon.mp3",
        "backend/test_audio.wav"
    ]

    audio_file = None
    for path in test_audio_paths:
        if os.path.exists(path):
            audio_file = path
            break

    if not audio_file:
        print("No test audio file found. Please create one of:")
        print("  - test_audio.wav")
        print("  - sample_sermon.wav")
        print("  - test_sermon.mp3")
        print("  - backend/test_audio.wav")
        return

    print(f"Using audio file: {audio_file}")

    try:
        # Initialize segmenter
        segmenter = SermonSegmenter(
            min_sermon_duration=10.0,  # Lower threshold for testing
            confidence_threshold=0.3   # Lower threshold for testing
        )

        # Test 1: Segmentation only
        print("\n--- Test 1: Audio Segmentation ---")
        result = segmenter.segment_audio(audio_file)
        print(f"Audio duration: {result.audio_duration:.2f} seconds")
        print(f"Detected {result.total_segments} segments")
        print(f"Processing time: {result.processing_time:.2f} seconds")

        if result.segments:
            print("\nDetected segments:")
            for i, seg in enumerate(result.segments, 1):
                print(f"  {i}. {seg.segment_type.value}")
                print("3.1f"
                      ".1f"
                      ".2f")
                if seg.text:
                    print(f"     Text preview: {seg.text[:100]}...")
        else:
            print("No segments detected")

        # Test 2: Segmentation with transcription alignment
        print("\n--- Test 2: Segmentation with Transcription ---")
        transcription_result = transcript_audio(audio_file)
        if transcription_result.get("segments"):
            transcript_segments = transcription_result["segments"]
            print(f"Transcription has {len(transcript_segments)} segments")

            # Align with transcription
            aligned_result = segmenter.segment_audio(audio_file, transcript_segments=transcript_segments)

            print(f"Aligned segmentation found {aligned_result.total_segments} segments")
            for i, seg in enumerate(aligned_result.segments[:3], 1):  # Show first 3
                print(f"  Segment {i}: {seg.segment_type.value} ({seg.start_time:.1f}-{seg.end_time:.1f}s)")
                if seg.text:
                    print(f"    Text: {seg.text[:80]}...")
        else:
            print("Transcription failed or no segments found")

        # Test 3: Show audio features
        print("\n--- Test 3: Audio Features Analysis ---")
        if result.audio_features:
            features = result.audio_features
            print(f"Sample rate: {features.get('sample_rate', 'N/A')} Hz")
            print(f"Channels: {features.get('channels', 'N/A')}")
            print(f"Silence gaps: {len(features.get('silence_gaps', []))}")
            print(f"BPM estimate: {features.get('bpm_estimate', 'N/A')}")

            energy_levels = features.get('energy_levels', [])
            if energy_levels:
                print(".1f")
                print(".1f")
                print(f"Average energy: {sum(energy_levels)/len(energy_levels):.1f} dB")

        print("\n--- Segmentation Test Complete ---")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_segmentation()
