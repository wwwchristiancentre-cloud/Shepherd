import librosa
import numpy as np
from typing import List, Dict, Tuple, Optional
import scipy.signal
from sklearn.cluster import KMeans
import time
import logging

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Service for analyzing audio features like silence detection, energy levels, and speech patterns"""

    def __init__(self,
                 silence_threshold: float = -40,  # dBFS threshold for silence
                 min_silence_duration: float = 1.0,  # Minimum silence gap in seconds
                 frame_length: int = 2048,
                 hop_length: int = 512):
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.frame_length = frame_length
        self.hop_length = hop_length

    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return audio data and sample rate"""
        try:
            audio, sr = librosa.load(audio_path, sr=None)  # Preserve original sample rate
            logger.info(f"Loaded audio: {audio_path}, duration: {len(audio)/sr:.2f}s, sample rate: {sr}Hz")
            return audio, sr
        except Exception as e:
            logger.error(f"Failed to load audio {audio_path}: {e}")
            raise ValueError(f"Could not load audio file: {e}")

    def detect_silence_gaps(self, audio_path: str) -> List[Dict]:
        """Detect periods where audio falls below silence threshold"""
        audio, sr = self.load_audio(audio_path)
        hops_per_second = sr / self.hop_length

        # Calculate RMS energy in frames
        rms = librosa.feature.rms(y=audio,
                                frame_length=self.frame_length,
                                hop_length=self.hop_length)[0]

        # Convert to dBFS
        rms_db = librosa.power_to_db(rms, ref=np.max)

        # Find frames below silence threshold
        silence_frames = rms_db < self.silence_threshold

        # Group consecutive silence frames and filter by minimum duration
        silence_gaps = []
        current_gap_start = None
        current_gap_frames = 0

        for frame_idx, is_silent in enumerate(silence_frames):
            if is_silent:
                if current_gap_start is None:
                    current_gap_start = frame_idx
                current_gap_frames += 1
            else:
                if current_gap_start is not None:
                    # End of silence gap
                    gap_duration = current_gap_frames / hops_per_second
                    if gap_duration >= self.min_silence_duration:
                        silence_gaps.append({
                            "start": current_gap_start / hops_per_second,
                            "end": frame_idx / hops_per_second,
                            "duration": gap_duration
                        })
                    current_gap_start = None
                    current_gap_frames = 0

        # Handle silence at end of audio
        if current_gap_start is not None:
            gap_duration = current_gap_frames / hops_per_second
            if gap_duration >= self.min_silence_duration:
                silence_gaps.append({
                    "start": current_gap_start / hops_per_second,
                    "end": len(audio) / sr,
                    "duration": gap_duration
                })

        logger.info(f"Detected {len(silence_gaps)} silence gaps")
        return silence_gaps

    def calculate_energy_levels(self, audio_path: str,
                               window_duration: float = 1.0) -> Tuple[List[float], List[float]]:
        """
        Calculate energy levels across audio in windows
        Returns: (energy_levels, time_stamps)
        """
        audio, sr = self.load_audio(audio_path)
        window_samples = int(window_duration * sr)

        energy_levels = []
        time_stamps = []

        for start_sample in range(0, len(audio), window_samples):
            end_sample = min(start_sample + window_samples, len(audio))
            segment = audio[start_sample:end_sample]

            # Calculate RMS energy
            rms = np.sqrt(np.mean(segment ** 2))
            energy_db = 20 * np.log10(rms + 1e-10)  # Avoid log(0)

            energy_levels.append(float(energy_db))
            time_stamps.append(start_sample / sr)

        logger.info(f"Calculated {len(energy_levels)} energy levels")
        return energy_levels, time_stamps

    def detect_speech_probability(self, audio_path: str) -> Tuple[List[float], List[float]]:
        """
        Estimate speech probability using zero-crossing rate and spectral centroid
        Returns: (speech_probabilities, time_stamps)
        """
        audio, sr = self.load_audio(audio_path)
        window_duration = 0.5  # 500ms windows
        hop_duration = 0.25    # 250ms hop

        zcr = librosa.feature.zero_crossing_rate(y=audio,
                                               frame_length=int(window_duration * sr),
                                               hop_length=int(hop_duration * sr))[0]

        spectral_centroid = librosa.feature.spectral_centroid(y=audio,
                                                            sr=sr,
                                                            n_fft=2048,
                                                            hop_length=int(hop_duration * sr))[0]

        # Normalize features
        zcr_norm = (zcr - np.min(zcr)) / (np.max(zcr) - np.min(zcr) + 1e-10)
        centroid_norm = (spectral_centroid - np.min(spectral_centroid)) / (np.max(spectral_centroid) - np.min(spectral_centroid) + 1e-10)

        # Simple speech probability heuristic: high ZCR and moderate spectral centroid
        speech_prob = zcr_norm * (1 - centroid_norm)  # High ZCR, moderate centroid suggests speech

        time_stamps = librosa.times_like(speech_prob, sr=sr, hop_length=int(hop_duration * sr))

        logger.info(f"Calculated speech probabilities for {len(speech_prob)} frames")
        return speech_prob.tolist(), time_stamps.tolist()

    def detect_music_patterns(self, audio_path: str) -> Optional[float]:
        """Estimate BPM if music is detected"""
        try:
            audio, sr = self.load_audio(audio_path)

            # Use librosa's beat tracking
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            return float(tempo[0]) if len(tempo) > 0 else None
        except Exception as e:
            logger.warning(f"Could not detect music patterns: {e}")
            return None
