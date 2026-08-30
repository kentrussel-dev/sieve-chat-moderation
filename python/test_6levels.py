import json
import urllib.request

samples = [
    ("hello everyone, have a great game glhf!", "Level 1 (Clean)"),
    ("bro you completely murdered that enemy tower", "Level 2 (Gaming Slang)"),
    ("what a masterclass in gameplay truly brilliant", "Level 3 (Ambiguous/Sarcastic)"),
    ("people like you really struggle with basic logic", "Level 4 (Subtle Hostility)"),
    ("you are such a complete brainless idiot", "Level 5 (Direct Toxic)"),
    ("kill yourself right now", "Level 6 (Severe/Deterministic)")
]

print("=== VERIFYING 6-LEVEL CALIBRATED ROUTING PIPELINE ===")
for text, desc in samples:
    req = urllib.request.Request(
        "http://localhost:8000/api/moderate",
        data=json.dumps({"text": text, "username": "TestUser", "channel": "qa"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    res = json.loads(resp.read().decode("utf-8"))
    print(f"[{desc}]")
    print(f"  Utterance:        \"{text}\"")
    print(f"  Toxicity Level:   Level {res.get('toxicity_level')} -> {res.get('level_label')}")
    print(f"  Toxicity Score:   {res.get('toxicity_score')} (Mesh 1 raw: {res.get('tier1_score')})")
    print(f"  Verdict Status:   {res.get('status')} [Resolved by: {res.get('resolved_by_tier')}]")
    print(f"  Review Queue:     {res.get('flagged_for_review')}")
    print(f"  Reasoning:        {res.get('reasoning')}")
    print()
