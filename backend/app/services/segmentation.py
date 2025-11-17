import numpy as np
from typing import List, Optional, Tuple
import time
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .audio_analysis import AudioAnalyzer
from ..models.segmentation import (
    SermonSegment, SegmentationResult, SegmentType,
    AudioAnalysisFeatures
)

logger = logging.getLogger(__name__)


class SermonSegmenter:
    """Service for segmenting sermons based on audio analysis"""

    def __init__(self,
                 min_sermon_duration: float = 3.0,   # Minimum segment duration in seconds (very lenient)
                 max_gap_duration: float = 10.0,     # Maximum gap between parts (allow longer gaps)
                 energy_threshold_db: float = -55,    # Energy threshold for speech (extremely lenient)
                 confidence_threshold: float = 0.1):  # Confidence threshold (extremely lenient)
        self.min_sermon_duration = min_sermon_duration
        self.max_gap_duration = max_gap_duration
        self.energy_threshold_db = energy_threshold_db
        self.confidence_threshold = confidence_threshold
        self.audio_analyzer = AudioAnalyzer()

    def segment_audio(self, audio_path: str,
                     transcript_segments: Optional[List[dict]] = None) -> SegmentationResult:
        """
        Main segmentation method that analyzes audio and creates sermon segments
        """
        start_time = time.time()

        try:
            # Analyze audio features
            audio_features = self._analyze_audio_features(audio_path)

            # Detect potential sermon blocks
            sermon_segments = self._identify_sermon_segments(audio_path, audio_features)

            # Add transcript text to segments if available
            if transcript_segments:
                sermon_segments = self._align_with_transcript(sermon_segments, transcript_segments)

            # Calculate summary statistics
            total_duration = audio_features['audio_duration']
            total_segments = len(sermon_segments)
            avg_duration = np.mean([s.duration for s in sermon_segments]) if sermon_segments else 0.0

            processing_time = time.time() - start_time

            # Add debug info to audio_features
            audio_features['debug_info'] = {
                'energy_levels_count': len(audio_features.get('energy_levels', [])),
                'speech_probabilities_count': len(audio_features.get('speech_probabilities', [])),
                'silence_gaps_count': len(audio_features.get('silence_gaps', [])),
                'min_energy': min(audio_features.get('energy_levels', [0])) if audio_features.get('energy_levels') else 0,
                'max_energy': max(audio_features.get('energy_levels', [0])) if audio_features.get('energy_levels') else 0,
                'avg_speech_prob': np.mean(audio_features.get('speech_probabilities', [0])) if audio_features.get('speech_probabilities') else 0,
                'energy_threshold_used': self.energy_threshold_db,
                'confidence_threshold_used': self.confidence_threshold
            }

            result = SegmentationResult(
                audio_duration=total_duration,
                segments=sermon_segments,
                total_segments=total_segments,
                average_segment_duration=avg_duration,
                processing_time=processing_time,
                confidence_threshold=self.confidence_threshold,
                audio_features=audio_features
            )

            logger.info(f"Completed segmentation: {total_segments} segments in {processing_time:.2f}s")
            logger.info(f"Debug: energy_levels={len(audio_features.get('energy_levels', []))}, speech_probs={len(audio_features.get('speech_probabilities', []))}")

            # Debug: Print what we're returning
            print(f"[DEBUG] Segmentation returning:")
            print(f"  - Total segments: {result.total_segments}")
            print(f"  - Segments list: {[f'{seg.segment_type}({seg.start_time:.1f}-{seg.end_time:.1f})' for seg in result.segments]}")
            print(f"  - Audio duration: {result.audio_duration}")
            print(f"  - Confidence threshold: {result.confidence_threshold}")

            return result

        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            processing_time = time.time() - start_time
            return SegmentationResult(
                audio_duration=0.0,
                segments=[],
                total_segments=0,
                average_segment_duration=0.0,
                processing_time=processing_time,
                error=str(e)
            )

    def _analyze_audio_features(self, audio_path: str) -> dict:
        """Analyze various audio features for segmentation"""
        logger.info("Analyzing audio features...")

        audio, sr = self.audio_analyzer.load_audio(audio_path)
        duration = len(audio) / sr

        # Get silence gaps
        silence_gaps = self.audio_analyzer.detect_silence_gaps(audio_path)

        # Get energy levels
        energy_levels, energy_timestamps = self.audio_analyzer.calculate_energy_levels(audio_path)

        # Get speech probabilities
        speech_probs, speech_timestamps = self.audio_analyzer.detect_speech_probability(audio_path)

        # Check for music
        bpm = self.audio_analyzer.detect_music_patterns(audio_path)

        return {
            'audio_duration': duration,
            'sample_rate': sr,
            'channels': 1 if len(audio.shape) == 1 else audio.shape[1],
            'silence_gaps': silence_gaps,
            'energy_levels': energy_levels,
            'energy_timestamps': energy_timestamps,
            'speech_probabilities': speech_probs,
            'speech_timestamps': speech_timestamps,
            'bpm_estimate': bpm
        }

    def _identify_sermon_segments(self, audio_path: str, audio_features: dict) -> List[SermonSegment]:
        """Identify potential sermon segments based on audio patterns"""
        logger.info("Identifying sermon segments...")

        duration = audio_features['audio_duration']
        energy_levels = np.array(audio_features['energy_levels'])
        energy_timestamps = np.array(audio_features['energy_timestamps'])
        speech_probs = np.array(audio_features['speech_probabilities'])
        silence_gaps = audio_features['silence_gaps']

        # Find speech segments (high energy + speech probability)
        window_duration = 1.0  # 1 second windows
        speech_segments = self._find_speech_segments(
            energy_levels, speech_probs, energy_timestamps,
            window_duration, duration
        )

        # Merge nearby segments and classify them
        merged_segments = self._merge_similar_segments(speech_segments, silence_gaps)

        # Classify segments based on duration, energy, and patterns
        classified_segments = self._classify_segments(merged_segments, audio_features)

        # Multiple fallback strategies for different audio types
        if not classified_segments and audio_features.get('speech_probabilities'):
            speech_probs = np.array(audio_features['speech_probabilities'])
            avg_speech_prob = np.mean(speech_probs)

            logger.info(f"No segments detected, trying fallback strategies. Avg speech prob: {avg_speech_prob:.3f}")

            # Strategy 1: Split into time-based chunks for long audio
            if audio_features['audio_duration'] > 300:  # Over 5 minutes
                logger.info("Creating time-based segments for long audio")
                chunk_duration = 300  # 5-minute chunks
                num_chunks = int(np.ceil(audio_features['audio_duration'] / chunk_duration))

                for i in range(num_chunks):
                    start_time = i * chunk_duration
                    end_time = min((i + 1) * chunk_duration, audio_features['audio_duration'])
                    duration = end_time - start_time

                    if duration >= 60:  # Only chunks longer than 1 minute
                        classified_segments.append(
                            SermonSegment(
                                start_time=start_time,
                                end_time=end_time,
                                duration=duration,
                                segment_type=SegmentType.SERMON,
                                confidence=0.4,
                                energy_level=np.mean(audio_features.get('energy_levels', [0])) if audio_features.get('energy_levels') else 0,
                                silence_duration=None
                            )
                        )

            # Strategy 2: Look for periods with above-average speech activity
            elif avg_speech_prob > 0.05:  # Any measurable speech
                logger.info("Searching for periods with above-average speech activity")
                chunk_size = 60  # 1-minute windows for analysis
                chunks_per_minute = 60 // 5  # 5-second resolution

                for i in range(0, int(audio_features['audio_duration']), chunk_size):
                    start_idx = int(i * len(speech_probs) / audio_features['audio_duration'])
                    end_idx = int((i + chunk_size) * len(speech_probs) / audio_features['audio_duration'])
                    if end_idx <= len(speech_probs):
                        chunk_speech = np.mean(speech_probs[start_idx:end_idx])
                        if chunk_speech > avg_speech_prob * 1.2 and chunk_speech > 0.03:  # Above average
                            classified_segments.append(
                                SermonSegment(
                                    start_time=i,
                                    end_time=min(i + chunk_size, audio_features['audio_duration']),
                                    duration=min(chunk_size, audio_features['audio_duration'] - i),
                                    segment_type=SegmentType.SERMON,
                                    confidence=max(0.2, chunk_speech * 2),
                                    energy_level=np.mean(audio_features.get('energy_levels', [0])) if audio_features.get('energy_levels') else 0,
                                    silence_duration=None
                                )
                            )

            # Strategy 3: Last resort - single segment
            if not classified_segments and audio_features['audio_duration'] > 60:  # Not microscopic audio
                logger.info("Last resort: Creating single segment covering entire audio")
                classified_segments = [
                    SermonSegment(
                        start_time=0,
                        end_time=audio_features['audio_duration'],
                        duration=audio_features['audio_duration'],
                        segment_type=SegmentType.SERMON,
                        confidence=0.3,
                        energy_level=np.mean(audio_features.get('energy_levels', [0])) if audio_features.get('energy_levels') else 0,
                        silence_duration=None
                    )
                ]

        return classified_segments

    def _find_speech_segments(self, energy_levels: np.ndarray,
                            speech_probs: np.ndarray,
                            timestamps: np.ndarray,
                            window_duration: float,
                            audio_duration: float) -> List[dict]:
        """Find segments that are likely to contain speech"""

        # Create a combined score for speech likelihood
        energy_threshold = self.energy_threshold_db
        energy_score = (energy_levels - np.min(energy_levels)) / (np.max(energy_levels) - np.min(energy_levels) + 1e-10)

        # Interpolate speech probabilities to match energy timestamps
        speech_interpolated = np.interp(timestamps, np.linspace(0, audio_duration, len(speech_probs)), speech_probs)

        # Combined speech score
        speech_score = 0.7 * speech_interpolated + 0.3 * energy_score

        # Find segments above threshold
        is_speech = speech_score > 0.35  # Threshold for speech detection (more lenient)
        is_above_energy = energy_levels > energy_threshold

        likely_speech = is_speech & is_above_energy
        likely_speech = self._smooth_binary_array(likely_speech, window_size=3)  # Smooth to avoid noise

        # Convert to time segments
        speech_segments = []
        current_start = None
        min_segment_duration = 5.0  # Minimum 5 seconds for a segment

        for i, is_active in enumerate(likely_speech):
            if is_active and current_start is None:
                current_start = timestamps[i]
            elif not is_active and current_start is not None:
                duration = timestamps[i] - current_start
                if duration >= min_segment_duration:
                    speech_segments.append({
                        'start': current_start,
                        'end': timestamps[i],
                        'duration': duration,
                        'energy_level': np.mean(energy_levels[max(0, i-5):i]),  # Average energy
                        'speech_score': np.mean(speech_score[max(0, i-5):i])   # Average speech score
                    })
                current_start = None

        # Handle last segment
        if current_start is not None:
            end_time = min(timestamps[-1] + window_duration, audio_duration)
            duration = end_time - current_start
            if duration >= min_segment_duration:
                speech_segments.append({
                    'start': current_start,
                    'end': end_time,
                    'duration': duration,
                    'energy_level': np.mean(energy_levels[-5:]),
                    'speech_score': np.mean(speech_score[-5:])
                })

        logger.info(f"Found {len(speech_segments)} potential speech segments")
        return speech_segments

    def _smooth_binary_array(self, arr: np.ndarray, window_size: int = 3) -> np.ndarray:
        """Apply simple smoothing to reduce noise in binary arrays"""
        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(arr.astype(float), kernel, mode='same')
        return smoothed > 0.5

    def _merge_similar_segments(self, segments: List[dict], silence_gaps: List[dict]) -> List[dict]:
        """Merge segments that are close together and separated by short silence"""
        if not segments:
            return segments

        merged = []
        current = segments[0].copy()

        for next_seg in segments[1:]:
            # Check if there's a small gap between segments
            gap = next_seg['start'] - current['end']
            has_small_gap = gap <= self.max_gap_duration

            # Check if silence gap is short enough
            silence_in_gap = any(g['start'] <= next_seg['start'] <= g['end'] and
                               g['duration'] <= self.max_gap_duration
                               for g in silence_gaps)

            if has_small_gap or silence_in_gap:
                # Merge segments
                current['end'] = next_seg['end']
                current['duration'] = current['end'] - current['start']
                current['energy_level'] = (current['energy_level'] + next_seg['energy_level']) / 2
                current['speech_score'] = (current['speech_score'] + next_seg['speech_score']) / 2
            else:
                merged.append(current)
                current = next_seg.copy()

        merged.append(current)
        logger.info(f"Merged to {len(merged)} segments")
        return merged

    def _classify_segments(self, segments: List[dict], audio_features: dict) -> List[SermonSegment]:
        """Classify segments based on duration, energy, and other features"""

        classified_segments = []

        for seg in segments:
            segment_type = self._classify_segment_type(seg, audio_features)
            confidence = self._calculate_confidence(seg, segment_type)

            # Only include segments above confidence threshold and minimum duration
            if confidence >= self.confidence_threshold and seg['duration'] >= self.min_sermon_duration:
                classified_segments.append(
                    SermonSegment(
                        start_time=seg['start'],
                        end_time=seg['end'],
                        duration=seg['duration'],
                        segment_type=segment_type,
                        confidence=confidence,
                        energy_level=seg['energy_level'],
                        silence_duration=None  # Could be calculated from silence gaps
                    )
                )

        logger.info(f"Classified {len(classified_segments)} segments with high confidence")
        return classified_segments

    def _classify_segment_type(self, segment: dict, audio_features: dict) -> SegmentType:
        """Classify a segment based on its characteristics"""

        duration = segment['duration']
        energy = segment['energy_level']

        # Simple heuristics for segment classification
        if duration > 300:  # Long segments likely main sermon
            return SegmentType.SERMON
        elif audio_features.get('bpm_estimate') and energy > self.energy_threshold_db + 5:
            return SegmentType.MUSIC
        elif duration < 60:  # Short segments likely announcements
            return SegmentType.ANNOUNCEMENT
        elif energy < self.energy_threshold_db + 3:  # Lower energy might be prayer
            return SegmentType.PRAYER
        else:
            # Default to sermon for longer segments
            return SegmentType.SERMON

    def _calculate_confidence(self, segment: dict, segment_type: SegmentType) -> float:
        """Calculate confidence score for segment classification"""

        duration = segment['duration']
        energy = segment['energy_level']
        speech_score = segment['speech_score']

        base_confidence = 0.5

        # Duration-based confidence
        if segment_type == SegmentType.SERMON:
            if duration > 600:  # Very long = very likely sermon
                base_confidence += 0.3
            elif duration > 300:  # Long = likely sermon
                base_confidence += 0.2
        elif segment_type == SegmentType.ANNOUNCEMENT and duration < 120:
            base_confidence += 0.2

        # Energy-based confidence
        if segment_type in [SegmentType.SERMON, SegmentType.ANNOUNCEMENT] and energy > self.energy_threshold_db:
            base_confidence += 0.15
        elif segment_type == SegmentType.MUSIC and energy > self.energy_threshold_db + 5:
            base_confidence += 0.2

        # Speech score-based confidence
        if segment_type == SegmentType.SERMON and speech_score > 0.6:
            base_confidence += 0.15

        return min(base_confidence, 1.0)

    def _align_with_transcript(self, sermon_segments: List[SermonSegment],
                              transcript_segments: List[dict]) -> List[SermonSegment]:
        """Add transcript text to segments based on time alignment"""

        for segment in sermon_segments:
            # Find transcript segments that overlap with this sermon segment
            overlapping_text = []
            for transcript_seg in transcript_segments:
                if (transcript_seg['end'] > segment.start_time and
                    transcript_seg['start'] < segment.end_time):
                    overlapping_text.append(transcript_seg['text'])

            if overlapping_text:
                segment.text = ' '.join(overlapping_text)

        return sermon_segments
