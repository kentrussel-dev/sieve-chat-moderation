"""
CONDA In-Game Live Match Replay Engine.
Streams real in-game Dota 2 chat events from the CONDA dataset into the Sieve moderation pipeline
with conversational context, match timestamps, player slots, and token slot tags.
"""

import json
import os
import threading
import time
from typing import Callable, Dict, List, Optional

CONDA_TEST_PATH = os.path.join(os.path.dirname(__file__), "..", "evaluation", "conda_test_dataset.json")


class CondaMatchReplayer:
    def __init__(self, moderation_callback: Optional[Callable] = None):
        self.callback = moderation_callback
        self.is_running = False
        self.rate_per_sec = 20
        self.worker_thread: Optional[threading.Thread] = None
        self.dataset: List[Dict] = []
        self.current_index = 0
        self.total_replayed = 0
        self._load_dataset()

    def _load_dataset(self):
        if os.path.exists(CONDA_TEST_PATH):
            with open(CONDA_TEST_PATH, "r", encoding="utf-8") as f:
                self.dataset = json.load(f)
            print(f"Loaded {len(self.dataset):,} in-game CONDA messages for replay.")
        else:
            print(f"Notice: CONDA dataset not found at {CONDA_TEST_PATH}")

    def start(self, rate_per_sec: int = 20):
        if not self.dataset:
            self._load_dataset()
        if not self.dataset:
            return

        self.rate_per_sec = max(1, min(150, rate_per_sec))
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._replay_loop, daemon=True)
        self.worker_thread.start()
        print(f"Started CONDA match replay at {self.rate_per_sec} msgs/sec.")

    def stop(self):
        self.is_running = False
        print("Stopped CONDA match replay.")

    def _replay_loop(self):
        delay = 1.0 / self.rate_per_sec
        n = len(self.dataset)

        while self.is_running and n > 0:
            item = self.dataset[self.current_index]
            self.current_index = (self.current_index + 1) % n
            self.total_replayed += 1

            if self.callback:
                user = item.get("player_id", "Player")
                chan = f"match-{item.get('conversation_id', 'lobby')}"
                text = item.get("text", "")
                self.callback("conda_dota2", user, chan, text)

            time.sleep(delay)

    def get_status(self) -> Dict:
        return {
            "is_running": self.is_running,
            "rate_per_sec": self.rate_per_sec,
            "messages_replayed": self.total_replayed,
            "total_available": len(self.dataset)
        }
