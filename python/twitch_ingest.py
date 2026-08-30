"""
Real-time anonymous Twitch IRC Chat Ingestion Client for Sieve Moderation Pipeline.
Connects to Twitch IRC (irc.chat.twitch.tv:6667) using read-only anonymous credentials,
streams live chat messages from any public channel, and feeds them into the Sieve moderation engine.
"""

import random
import re
import socket
import threading
import time
from typing import Callable, Optional


class TwitchLiveIngestClient:
    def __init__(self, moderation_callback: Callable):
        self.moderation_callback = moderation_callback
        self.sock: Optional[socket.socket] = None
        self.is_running = False
        self.current_channel = ""
        self.thread: Optional[threading.Thread] = None
        self.messages_ingested = 0
        self.connected_at = 0.0

    def connect(self, channel: str):
        self.disconnect()

        # Clean channel name (e.g. "#tarik" or "tarik" -> "tarik")
        clean_channel = channel.strip().lower().lstrip("#")
        if not clean_channel:
            raise ValueError("Channel name cannot be empty")

        self.current_channel = clean_channel
        self.is_running = True
        self.messages_ingested = 0
        self.connected_at = time.time()

        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"Twitch Ingest thread started for #{self.current_channel}")

    def disconnect(self):
        self.is_running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.current_channel = ""

    def get_status(self):
        return {
            "connected": self.is_running and self.sock is not None,
            "channel": self.current_channel,
            "messages_ingested": self.messages_ingested,
            "uptime_seconds": round(time.time() - self.connected_at, 1) if self.is_running else 0
        }

    def _run_loop(self):
        host = "irc.chat.twitch.tv"
        port = 6667
        anon_nick = f"justinfan{random.randint(10000, 99999)}"

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((host, port))

            self.sock.send(f"PASS SCHMOOPIE\r\n".encode("utf-8"))
            self.sock.send(f"NICK {anon_nick}\r\n".encode("utf-8"))
            self.sock.send(f"JOIN #{self.current_channel}\r\n".encode("utf-8"))

            buffer = ""
            while self.is_running:
                try:
                    data = self.sock.recv(4096).decode("utf-8", errors="ignore")
                    if not data:
                        time.sleep(0.1)
                        continue
                    buffer += data
                    lines = buffer.split("\r\n")
                    buffer = lines.pop()

                    for line in lines:
                        if not line:
                            continue

                        # Handle Twitch PING heartbeat
                        if line.startswith("PING"):
                            pong_resp = line.replace("PING", "PONG") + "\r\n"
                            self.sock.send(pong_resp.encode("utf-8"))
                            continue

                        # Parse PRIVMSG chat messages
                        # Format: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message text
                        if "PRIVMSG" in line:
                            match = re.match(r"^:([^!]+)![^@]+@[^\s]+\s+PRIVMSG\s+#[^\s]+\s+:(.*)$", line)
                            if match:
                                username, message = match.groups()
                                self.messages_ingested += 1
                                if self.moderation_callback:
                                    self.moderation_callback(
                                        source="twitch",
                                        username=username,
                                        channel=self.current_channel,
                                        text=message
                                    )
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        print(f"Twitch socket error: {e}")
                    break
        except Exception as e:
            print(f"Failed to connect to Twitch IRC #{self.current_channel}: {e}")
        finally:
            self.disconnect()
