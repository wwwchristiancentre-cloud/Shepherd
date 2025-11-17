# FR-003: Sermon Segmentation (Audio-based)

## High-Level Goal

As an editor, I want the system to automatically detect and suggest sermon segments, so that I can quickly isolate the main content. The system analyzes the audio for patterns (silence, energy levels) to propose start/end times for segments like "Sermon".

## Component Breakdown

### Server Components

**Audio Analysis Service** (`backend/app/services/audio_analysis.py`)
- Loads audio files using librosa
- Detects silence gaps based on RMS energy analysis
- Calculates energy levels across audio duration
- Estimates speech probabilities using zero-crossing rate and spectral centroid
- Optional BPM estimation for music detection

**Sermon Segmentation Service** (`backend/app/services/segmentation.py`)
- Core algorithm that identifies sermon segments
- Combines multiple audio features (energy, speech probability, silence gaps)
- Merges nearby segments and classifies them by type
- Integrates with Whisper transcription for text alignment

**Data Models** (`backend/app/models/segmentation.py`)
- `SermonSegment`: Model for individual sermon segments with timestamps and classification
- `SegmentationResult`: Complete segmentation results with metadata
- `SegmentType`: Enum for segment classification (sermon, announcement, music, prayer, other)

### Client Components

**Segmentation UI Components** (`src/features/segmentation/`)
- React components to display segmentation results
- Timeline visualization showing different segment types
- Segment approval/rejection interface

**Segmentation Hooks** (`src/features/segmentation/hooks/`)
- `useSegmentation`: Hook for managing segmentation state
- `useUploadSegmentation`: Hook for uploading and processing audio files

## Logic & Data Breakdown

### API Routes

**POST `/transcription/segment`**
- Accepts audio file upload
- Optional `include_transcription` parameter
- Returns segmentation results with optional transcript alignment

**POST `/transcription/transcribe-and-segment`**
- Combined endpoint for transcription + segmentation
- Accepts audio file and optional project_id
- Returns both transcription and segmentation results

### Backend Services

**AudioAnalyzer Class**
- `load_audio()`: Load and validate audio files
- `detect_silence_gaps()`: Identify silence periods using energy thresholds
- `calculate_energy_levels()`: Compute RMS energy across time windows
- `detect_speech_probability()`: Estimate speech likelihood using audio features
- `detect_music_patterns()`: Optional BPM estimation

**SermonSegmenter Class**
- `segment_audio()`: Main segmentation orchestration
- `_analyze_audio_features()`: Collect all audio analysis data
- `_identify_sermon_segments()`: Apply segmentation algorithm
- `_classify_segments()`: Classify segments by type and confidence
- `_align_with_transcript()`: Match segments with transcript text

### Data Flow

1. Audio file uploaded via API endpoint
2. AudioAnalyzer extracts features (silence, energy, speech probability)
3. SermonSegmenter applies segmentation algorithm to identify candidate segments
4. Segments are classified and filtered by confidence thresholds
5. If transcription is available, text is aligned with time segments
6. Results returned as structured JSON with metadata

## Database Schema Changes

### New Tables (if needed for persistent segmentation)

```sql
-- Optional: Store segmentation results for later retrieval
CREATE TABLE sermon_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    audio_filename TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    segment_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    transcript_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Optional: Store audio analysis metadata
CREATE TABLE audio_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    audio_duration REAL NOT NULL,
    sample_rate INTEGER NOT NULL,
    silence_gap_count INTEGER,
    energy_stats TEXT,  -- JSON blob with energy statistics
    processing_time REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**Note**: Current implementation saves segmentation results as JSON files alongside transcripts, without additional database tables. Database integration can be added if persistent segmentation storage is required.

## Testing Plan

### Unit Tests (Jest/Python unittest)

**Audio Analysis Service Tests**
- Test silence detection with various audio samples
- Test energy level calculations with known audio signals
- Test speech probability estimation with clean speech vs music
- Edge cases: silent audio, very short audio clips

**Segmentation Algorithm Tests**
- Test segment identification with mock audio features
- Test segment classification with different duration/energy combinations
- Test transcript alignment with overlapping time segments
- Confidence thresholding validation

### Integration Tests (React Testing Library)

**Segmentation UI Components**
- Test audio upload form submission
- Test segmentation results display
- Test segment timeline visualization
- Test user interaction with segment approval/rejection

**API Integration Tests**
- Test successful segmentation with valid audio files
- Test error handling for invalid file formats
- Test combined transcription + segmentation workflow
- Test response parsing and state updates

### E2E Tests (Playwright)

**Critical User Flows**
- Upload audio file and receive segmentation results
- Review and approve/reject suggested segments
- Export segmented content for editing
- Handle large audio files gracefully

**Error Scenarios**
- Invalid file format rejection
- Segmentation timeout/error recovery
- Network interruption handling

## Step-by-Step Implementation Plan

### Phase 1: Core Audio Analysis (✅ Completed)

1. Install audio processing dependencies (librosa, pydub, scipy, scikit-learn)
2. Create audio analysis service with basic feature extraction
3. Implement silence detection algorithm
4. Add energy level and speech probability analysis
5. Create data models for segmentation results

### Phase 2: Segmentation Algorithm (✅ Completed)

6. Implement segment identification logic
7. Add segment merging and classification
8. Integrate confidence scoring system
9. Add transcript alignment capabilities

### Phase 3: API Integration (✅ Completed)

10. Extend transcription API with segmentation endpoints
11. Add combined transcription + segmentation endpoint
12. Implement proper error handling and logging
13. Add API response formatting and metadata

### Phase 4: Testing & Validation (🔄 In Progress)

14. Create test script for segmentation validation
15. Test with sample audio files
16. Verify integration with existing Whisper transcription
17. Document API usage and response formats

### Phase 5: Frontend Integration (📋 Planned)

18. Create React components for segmentation display
19. Implement timeline visualization
20. Add segment approval/rejection interface
21. Integrate with existing project workflow

### Phase 6: Production Readiness (📋 Future)

22. Add performance optimizations for large audio files
23. Implement caching for repeated analysis requests
24. Add comprehensive error monitoring and logging
25. Create backup/recovery mechanisms for segmentation failures

## Technical Details

### Audio Analysis Features

The segmentation system analyzes audio using:

1. **Silence Detection**: RMS energy analysis with configurable thresholds
2. **Energy Contours**: Time-varying energy levels across the audio
3. **Speech Estimation**: Zero-crossing rate and spectral centroid analysis
4. **Music Detection**: Optional BPM estimation using librosa's beat tracking
5. **Temporal Segmentation**: Windowed analysis with configurable overlap

### Algorithm Parameters

```python
# Default segmentation parameters
min_sermon_duration = 30.0      # seconds
max_gap_duration = 5.0         # seconds (max gap between sermon parts)
energy_threshold_db = -25       # dBFS energy threshold
confidence_threshold = 0.6      # minimum confidence for inclusion
silence_threshold = -40         # dBFS silence threshold
min_silence_duration = 1.0      # seconds
```

### Performance Considerations

- Audio analysis is CPU-intensive, scales with audio duration
- Typical processing: ~10-50x real-time depending on audio complexity
- Memory usage: ~50-200MB for typical sermon-length audio
- Uses librosa's efficient STFT-based feature extraction
- Supports parallel processing for multiple requests

### Error Handling

- Invalid audio formats: 400 Bad Request with descriptive message
- Analysis failures: 500 Internal Server Error with error details
- Large files: Timeout handling with configurable limits
- Corrupted audio: Graceful fallback with error logging

## Dependencies

- **librosa**: Core audio feature extraction
- **scipy**: Signal processing and statistical analysis
- **scikit-learn**: Clustering and preprocessing utilities
- **pydub**: Audio format conversions (if needed)
- **numpy**: Numerical computations
- **typing**: Type hints for better code documentation

## Future Enhancements

- **Machine Learning Classification**: Train ML models on sermon data for better accuracy
- **Multi-speaker Detection**: Identify different speakers within segments
- **Language Detection**: Automatic language identification for multilingual content
- **Emotion Analysis**: Detect emotional content within sermon delivery
- **Quality Metrics**: Provide audio quality scores for each segment
