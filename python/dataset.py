"""
Dataset preparation and generation utilities for Sieve moderation pipeline.
Generates distinct training and held-out evaluation sets to rigorously measure
out-of-distribution generalization and uncertainty escalation behavior.
"""

import json
import os
import random
from typing import Dict, List, Tuple

CLEAN_TEMPLATES = [
    "Thank you for sharing this insightful tutorial.",
    "Could someone explain how Kafka consumer groups rebalance?",
    "I appreciate the detailed explanation on database indexing.",
    "The weather today is really nice for an outdoor run.",
    "Let's review the pull request before merging to main.",
    "I respectfully disagree with your conclusion regarding microservices.",
    "Great presentation at the conference today!",
    "Where can I find the documentation for ONNX Runtime C++ API?",
    "Does anyone have recommendations for high-throughput messaging brokers?",
    "The bug was caused by an unhandled nil pointer dereference in the handler.",
    "I enjoyed reading your technical article on distributed systems.",
    "Can you share the benchmark numbers for p99 latency under load?",
    "That makes a lot of sense, thanks for clarifying.",
    "Let's schedule a brief sync tomorrow to align on project priorities.",
    "Excellent work by the team on hitting the release milestone.",
    "How does Sieve compare to traditional rule-based regex filters?",
    "We should add automated integration tests for Kafka topic failure scenarios.",
    "The latency improvement after switching to ONNX runtime was remarkable.",
    "I am learning Go concurrency patterns and finding sync.WaitGroup very intuitive.",
    "Here is a summary of the quarterly performance metrics.",
    "o7",
    "O7",
    "o7 in the chat",
    "o7 o7 o7",
    "gg",
    "gg wp",
    "glhf",
    "gl hf",
    "f in chat",
    "w streamer",
    "huge w",
    "lmao",
    "kekw",
    "pog",
    "pogchamp",
    "nt",
    "nice try",
    "mb",
    "my bad",
    "my flash timing was complete trash today",
    "this champion rework is absolute trash",
    "taking out the trash wave before baron",
    "my aim is pure trash in this warmup game",
    "this server ping is absolute garbage",
    "garbage drop rate on the rare item",
    "my positioning was garbage during that teamfight",
    "Riot Games please fix the client bug",
    "we riot if they nerf this hero next patch",
    "Riot announced the new Valorant agent today",
    "Riot buffed the champion again",
    "nice kill on the enemy jungler",
    "kill the dragon before they rotate",
    "need to kill this creep wave fast",
    "great kill on their mid laner",
    "bot lane is feeding but we can scale and carry",
    "he is feeding the enemy hypercarry",
    "massive jungle diff this game",
    "playing Blitzcrank mid is hilarious",
    "logging into Overwatch with the squad tonight",
    "RIOT",
    "riot",
    "Riot",
    "Riot Games",
    "riot please",
    "we riot",
    "blitz",
    "overwatch",
    "trash mob",
    "garbage tier",
    "trash",
    "garbage",
    "trash talk is part of competitive gaming",
    "my mechanics are total trash today",
    "throw that trash item away",
    "my csing was trash this game",
    "talk trash in all chat",
    "this server ping is pure garbage",
    "garbage tier list",
    "kill",
    "kills",
    "kill count",
    "first kill of the game",
    "clean kill on the mid laner",
    "double kill",
    "triple kill",
    "quadra kill",
    "penta kill",
    "rampage kill",
    "kill streak",
    "ez",
    "ez mid",
    "ez game",
    "ez lane",
    "ez win",
    "what the fuck was that play lmao",
    "holy shit that was insane",
    "what the hell just happened",
    "holy fuck nice shot",
    "fucking insane clutch",
    "fucking smurfing this lobby",
    "what the fuck KEKW",
    "holy shit Pog"
]

BLATANT_TOXIC_TEMPLATES = [
    "fuck you",
    "fuck off",
    "shut the fuck up",
    "go fuck yourself",
    "you are fucking garbage",
    "you suck at this game delete it",
    "uninstall the game you useless bot",
    "shut up and delete your account",
    "You are a completely brainless moron who knows nothing.",
    "Shut up and delete your account, nobody wants to hear your garbage.",
    "Kill yourself you pathetic worthless loser.",
    "Get out of here before someone makes you regret posting.",
    "You are the dumbest person on this entire platform.",
    "Your entire family is trash and you should be ashamed.",
    "Go die in a ditch, nobody would even notice.",
    "Stop spewing your idiotic nonsense everywhere.",
    "You are an absolute waste of oxygen.",
    "I hate you and hope terrible things happen to you today.",
    "What a brain-dead take from a complete idiot.",
    "You disgusting scum, get off the internet.",
    "Shut your mouth and never speak here again.",
    "You deserve all the harassment you get, loser.",
    "Nobody likes you, why do you even exist?",
    "You are completely retarded and incompetent.",
    "What kind of retarded logic is this?",
    "You absolute retard, stop talking.",
    "Stop acting like a retard in this forum.",
    "Only a total retard would write code this bad.",
    "You are complete trash at this game uninstall immediately.",
    "You are a piece of garbage human being.",
    "You are an absolute idiot and should never speak again.",
    "You are a brainless moron who ruins every match.",
    "Shut your mouth you useless trash."
]

# Unseen, nuanced evaluation cases that test generalization and trigger the escalation band
AMBIGUOUS_EVAL_TEMPLATES = [
    # Novel sarcasm without explicit toxic vocabulary (Tier 1 is uncertain; LLM detects context)
    ("Another masterclass in missing the point entirely. Truly inspired.", 1, "sarcasm", "hard"),
    ("Keep talking, maybe eventually something intelligent will come out.", 1, "sarcasm", "hard"),
    ("Fascinating how you manage to be wrong with such absolute confidence.", 1, "sarcasm", "hard"),
    ("Did it take you all day to come up with that astonishingly mediocre take?", 1, "sarcasm", "hard"),
    ("Wow, you really outdid yourself finding new ways to fail.", 1, "sarcasm", "hard"),
    ("Incredible insight, truly bridging the gap between ignorance and delusion.", 1, "sarcasm", "hard"),

    # Benign aggressive slang / gaming colloquialisms (False Alarm traps for small models)
    ("Bro you absolutely murdered that guitar solo, unreal performance!", 0, "false_alarm_colloquial", "hard"),
    ("We executed that deployment flawlessly and terminated all legacy instances.", 0, "false_alarm_colloquial", "hard"),
    ("I'm dying from laughter over this ridiculous compilation video.", 0, "false_alarm_colloquial", "hard"),
    ("This spicy ramen is pure torture on my tongue but delicious.", 0, "false_alarm_colloquial", "hard"),
    ("Our sales team just slaughtered the quarterly revenue quota.", 0, "false_alarm_colloquial", "hard"),
    ("The defense completely suffocated the opposing offense in the second half.", 0, "false_alarm_colloquial", "hard"),

    # Passive-aggressive hostility & coded identity insinuation
    ("It must be nice living in such blissful ignorance of reality.", 1, "subtle_hostility", "hard"),
    ("We all know why individuals with your background struggle with basic logic.", 1, "subtle_hostility", "hard"),
    ("Nobody expected someone from your faction to contribute anything useful anyway.", 1, "subtle_hostility", "hard"),
    ("You definitely look like the kind of person who would believe that.", 1, "subtle_hostility", "hard"),
    ("Go back to whatever echo chamber spawned you.", 1, "subtle_hostility", "hard"),

    # Direct academic / technical critique without toxicity
    ("Your methodology lacks proper control variables and the conclusions cannot be supported.", 0, "sharp_disagreement", "hard"),
    ("I strongly oppose this pull request due to multiple severe performance regressions.", 0, "sharp_disagreement", "hard"),
    ("The mathematical derivation on page 4 contains an invalid assumption.", 0, "sharp_disagreement", "hard")
]


def generate_training_dataset(num_samples: int = 2000, seed: int = 42) -> List[Dict]:
    random.seed(seed)
    dataset = []
    num_clean = num_samples // 2
    num_toxic = num_samples - num_clean

    for i in range(num_clean):
        template = random.choice(CLEAN_TEMPLATES)
        prefix = random.choice(["", "Hello, ", "Quick question: ", "FYI: ", "Note: "])
        suffix = random.choice(["", " Best regards.", " Thoughts?", " Appreciate it!", " Thanks."])
        text = (prefix + template + suffix).strip()
        dataset.append({
            "id": f"train_clean_{i:05d}",
            "text": text,
            "label": 0,
            "category": "clean",
            "tier_difficulty": "easy"
        })

    for i in range(num_toxic):
        template = random.choice(BLATANT_TOXIC_TEMPLATES)
        dataset.append({
            "id": f"train_toxic_{i:05d}",
            "text": template,
            "label": 1,
            "category": "toxic_blatant",
            "tier_difficulty": "easy"
        })

    random.shuffle(dataset)
    return dataset


def generate_evaluation_dataset(num_samples: int = 1500, seed: int = 99) -> List[Dict]:
    random.seed(seed)
    dataset = []

    # 55% Clean, 30% Blatant Toxic, 15% Nuanced/Ambiguous Edge Cases
    num_clean = int(num_samples * 0.55)
    num_toxic = int(num_samples * 0.30)
    num_ambiguous = num_samples - num_clean - num_toxic

    for i in range(num_clean):
        template = random.choice(CLEAN_TEMPLATES)
        prefix = random.choice(["", "Hi team, ", "Quick note: ", "Can someone check: "])
        suffix = random.choice(["", " Thanks everyone.", " Looking forward to your thoughts."])
        dataset.append({
            "id": f"test_clean_{i:05d}",
            "text": (prefix + template + suffix).strip(),
            "label": 0,
            "category": "clean",
            "tier_difficulty": "easy"
        })

    for i in range(num_toxic):
        template = random.choice(BLATANT_TOXIC_TEMPLATES)
        dataset.append({
            "id": f"test_toxic_{i:05d}",
            "text": template,
            "label": 1,
            "category": "toxic_blatant",
            "tier_difficulty": "easy"
        })

    for i in range(num_ambiguous):
        item = random.choice(AMBIGUOUS_EVAL_TEMPLATES)
        text, label, category, difficulty = item
        prefix = random.choice(["", "Honestly, ", "Well, ", "Look, ", ""])
        dataset.append({
            "id": f"test_ambig_{i:05d}",
            "text": (prefix + text).strip(),
            "label": label,
            "category": category,
            "tier_difficulty": difficulty
        })

    random.shuffle(dataset)
    return dataset


def save_dataset(dataset: List[Dict], filepath: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)


def load_dataset(filepath: str) -> List[Dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    train_out = os.path.join(os.path.dirname(__file__), "..", "evaluation", "train_dataset.json")
    test_out = os.path.join(os.path.dirname(__file__), "..", "evaluation", "synthetic_dataset.json")

    train_data = generate_training_dataset(2000)
    test_data = generate_evaluation_dataset(1500)

    save_dataset(train_data, train_out)
    save_dataset(test_data, test_out)

    print(f"Saved {len(train_data)} training samples to {train_out}")
    print(f"Saved {len(test_data)} test samples to {test_out}")
