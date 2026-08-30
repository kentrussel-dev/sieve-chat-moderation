"""
Lightweight False-Positive & Polysemy Mining Tool for Sieve.
Analyzes Level 4+ flagged messages and review queue items from telemetry logs,
extracts high-frequency recurring terms, and surfaces candidate gaming entities/emotes
to catch polysemous false positives before they cause production issues.
"""

import collections
import json
import os
import re
import sys
import urllib.request
from typing import Dict, List

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
GAMING_ENTITIES_FILE = os.path.join(CONFIG_DIR, "gaming_entities.json")
EMOTE_CONTEXT_FILE = os.path.join(CONFIG_DIR, "emote_context.json")
REPORT_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "evaluation", "weekly_polysemy_audit.md")


def load_known_entities() -> set:
    if os.path.exists(GAMING_ENTITIES_FILE):
        with open(GAMING_ENTITIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("entities", {}).keys())
    return set()


def load_known_emotes() -> set:
    if os.path.exists(EMOTE_CONTEXT_FILE):
        with open(EMOTE_CONTEXT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("emotes", {}).keys())
    return set()


def fetch_telemetry_events() -> List[Dict]:
    try:
        req = urllib.request.urlopen("http://localhost:8000/api/telemetry")
        data = json.loads(req.read().decode("utf-8"))
        return data.get("recent_events", [])
    except Exception as e:
        print(f"Notice: Could not fetch from live server: {e}")
        return []


def run_mining_audit(events: List[Dict]) -> str:
    known_entities = {e.lower() for e in load_known_entities()}
    known_emotes = {e.lower() for e in load_known_emotes()}

    # Focus on flagged messages (Level 4, 5, 6) or Review Queue
    flagged_events = [
        e for e in events
        if e.get("toxicity_level", 1) >= 4 or e.get("flagged_for_review")
    ]

    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is",
        "are", "was", "were", "it", "this", "that", "i", "you", "he", "she", "we", "they",
        "my", "your", "his", "her", "their", "of", "so", "just", "be", "do", "not", "have"
    }

    token_counter = collections.Counter()
    bigram_counter = collections.Counter()
    token_examples = collections.defaultdict(list)

    for evt in flagged_events:
        text = evt.get("text", "")
        level = evt.get("toxicity_level", 1)
        tokens = [t for t in re.findall(r"\b[A-Za-z0-9_]+\b", text.lower()) if t not in stop_words and len(t) > 1]

        for t in tokens:
            token_counter[t] += 1
            if len(token_examples[t]) < 3:
                token_examples[t].append((text, level))

        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            bigram_counter[bigram] += 1

    # Generate Markdown Report
    lines = [
        "# Sieve Weekly Polysemy & False-Positive Audit Report",
        "",
        f"- **Total Events Scanned**: {len(events)}",
        f"- **Flagged / Review Events Analyzed**: {len(flagged_events)}",
        "",
        "## Top Recurring Flagged Tokens",
        "",
        "| Rank | Token | Frequency | In Gaming Entities? | In Emote Table? | Sample Context | Action Recommendation |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    rank = 1
    for token, count in token_counter.most_common(15):
        in_entities = "✅ Yes" if token in known_entities else "❌ No"
        in_emotes = "✅ Yes" if token in known_emotes else "❌ No"
        samples = "<br>".join([f"• *\"{txt}\"* (L{lvl})" for txt, lvl in token_examples[token][:2]])
        
        rec = "Monitor"
        if token in known_entities or token in known_emotes:
            rec = "Verify Disambiguation"
        elif count >= 3:
            rec = "Investigate Polysemy / Add Entity"

        lines.append(f"| {rank} | **`{token}`** | {count} | {in_entities} | {in_emotes} | {samples} | {rec} |")
        rank += 1

    if not flagged_events:
        lines.append("\n*No Level 4+ flagged events recorded in the current telemetry window.*")

    lines.extend([
        "",
        "## Top Bigrams in Flagged Contexts",
        "",
        "| Bigram | Frequency |",
        "| :--- | :--- |"
    ])
    for bg, cnt in bigram_counter.most_common(8):
        lines.append(f"| `{bg}` | {cnt} |")

    report_content = "\n".join(lines)

    os.makedirs(os.path.dirname(REPORT_OUTPUT_FILE), exist_ok=True)
    with open(REPORT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Generated weekly polysemy report at: {REPORT_OUTPUT_FILE}")
    return report_content


if __name__ == "__main__":
    evts = fetch_telemetry_events()
    report = run_mining_audit(evts)
    print("Report generated successfully.")
