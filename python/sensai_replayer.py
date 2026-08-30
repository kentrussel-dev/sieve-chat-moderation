"""
Sensai Live Stream Chat Replayer for Sieve.
Replays archived Sensai live stream chat events at configurable speeds (10 - 500 msgs/sec)
to benchmark throughput, latency percentiles, and tiered resolution under heavy load.
"""

import json
import os
import random
import threading
import time
from typing import Callable, List, Optional


SENSAI_TEST_PATH = os.path.join(os.path.dirname(__file__), "..", "evaluation", "sensai_test_dataset.json")


class SensaiStreamReplayer:
    def __init__(self, moderation_callback: Callable):
        self.moderation_callback = moderation_callback
        self.is_running = False
        self.rate_per_sec = 25
        self.thread: Optional[threading.Thread] = None
        self.messages_replayed = 0
        self.items: List[dict] = []
        self._load_dataset()

    def _load_dataset(self):
        if os.path.exists(SENSAI_TEST_PATH):
            try:
                with open(SENSAI_TEST_PATH, "r", encoding="utf-8") as f:
                    self.items = json.load(f)
            except Exception as e:
                print(f"Error loading Sensai dataset for replay: {e}")

    def start(self, rate_per_sec: int = 25):
        self.stop()
        if not self.items:
            self._load_dataset()
        if not self.items:
            print("No Sensai items available for replay.")
            return

        self.rate_per_sec = max(1, min(500, rate_per_sec))
        self.is_running = True
        self.messages_replayed = 0
        self.thread = threading.Thread(target=self._replay_loop, daemon=True)
        self.thread.start()
        print(f"Sensai Replayer started at {self.rate_per_sec} msgs/sec.")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def get_status(self):
        return {
            "is_running": self.is_running,
            "rate_per_sec": self.rate_per_sec,
            "messages_replayed": self.messages_replayed,
            "total_available": len(self.items)
        }

    def _replay_loop(self):
        idx = 0
        num_items = len(self.items)

        while self.is_running and num_items > 0:
            start_batch = time.perf_counter()
            item = self.items[idx % num_items]
            idx += 1

            # Fabricate realistic chat username
            usernames = ["PogChamp99", "Gamer_Zero", "NightFox", "AquaFan", "PixelRider", "CyberSamurai", "ChatterBox"]
            user = random.choice(usernames)

            if self.moderation_callback:
                self.moderation_callback(
                    source="sensai_replay",
                    username=user,
                    channel="Sensai Live Stream",
                    text=item["text"]
                )
                self.messages_replayed += 1

            delay = 1.0 / self.rate_per_sec
            elapsed = time.perf_counter() - start_batch
            sleep_time = max(0.0, delay - elapsed)
            time.sleep(sleep_time)
