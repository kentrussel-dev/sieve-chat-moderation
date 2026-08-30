"""
Streamer Live Audio Caption Context Interface (Part B Stub).
Provides an opt-in, pluggable interface for streaming automatic speech recognition (STT/ASR).
Maintains a rolling conversational context window of the streamer's spoken dialogue.
"""

import time
from typing import Dict, List, Optional


class LiveCaptionContextManager:
    """
    Pluggable manager for real-time streamer audio transcription buffers.
    
    LATENCY & ARCHITECTURAL CONSIDERATIONS (KNOWN TRADEOFFS):
    --------------------------------------------------------
    1. Streaming STT Delay:
       Real-time speech-to-text engines (e.g. Whisper Streaming, Deepgram Nova-2, Vosk)
       operate on audio chunks (typically 1.5s to 3.0s window + 400ms inference).
       Therefore, spoken caption context is inherently delayed by ~1.5s - 3.5s relative
       to raw broadcast video.
       
    2. Zero Fast-Path Impact:
       Because Mesh 1 evaluates in sub-millisecond time (<1.0ms), audio transcription
       MUST NOT block or run synchronously on Mesh 1. Caption context is maintained
       in an asynchronous rolling buffer and read only when escalating to Mesh 2 (LLM).
       
    3. Production Integration Point:
       To wire real STT in the future, connect your audio worker (e.g., RTMP/HLS audio demuxer)
       to call `push_transcription_chunk(channel_id, text, timestamp)`.
    """

    def __init__(self, is_enabled: bool = False):
        self.is_enabled = is_enabled
        # In-memory rolling buffer: channel_id -> list of (timestamp, text_chunk)
        self.caption_buffers: Dict[str, List[Tuple[float, str]]] = {}
        self.total_queries = 0
        self.available_hits = 0

    def get_recent_caption_context(
        self,
        stream_id: str,
        window_seconds: int = 15
    ) -> Optional[str]:
        """
        Retrieves the rolling transcribed speech from the last `window_seconds`.
        Returns None by default when disabled (zero overhead/latency).
        """
        self.total_queries += 1

        if not self.is_enabled or not stream_id:
            return None

        clean_id = stream_id.strip().lower().replace("#", "")
        buffer = self.caption_buffers.get(clean_id, [])

        now = time.time()
        # Keep only entries within the rolling window
        recent_entries = [text for ts, text in buffer if now - ts <= window_seconds]

        if not recent_entries:
            return None

        self.available_hits += 1
        combined_context = " ".join(recent_entries).strip()
        return combined_context if combined_context else None

    def push_transcription_chunk(self, stream_id: str, text: str):
        """Hook for upstream STT workers (e.g. Whisper WebSocket) to push new transcribed speech."""
        if not text or not stream_id:
            return

        clean_id = stream_id.strip().lower().replace("#", "")
        if clean_id not in self.caption_buffers:
            self.caption_buffers[clean_id] = []

        now = time.time()
        self.caption_buffers[clean_id].append((now, text.strip()))

        # Prune old items (>60s)
        self.caption_buffers[clean_id] = [
            (ts, t) for ts, t in self.caption_buffers[clean_id] if now - ts <= 60
        ]

    def get_telemetry_stats(self) -> Dict:
        """Returns observability stats for how often caption context was available vs null."""
        hit_rate = (self.available_hits / self.total_queries * 100.0) if self.total_queries > 0 else 0.0
        return {
            "is_enabled": self.is_enabled,
            "total_queries": self.total_queries,
            "available_hits": self.available_hits,
            "availability_rate_pct": round(hit_rate, 2),
            "active_channel_buffers": len(self.caption_buffers)
        }


# Global singleton instance (Disabled by default as requested in Part B)
global_caption_manager = LiveCaptionContextManager(is_enabled=False)


def get_recent_caption_context(stream_id: str, window_seconds: int = 15) -> Optional[str]:
    """Convenience accessor for pluggable streamer caption context."""
    return global_caption_manager.get_recent_caption_context(stream_id, window_seconds)
