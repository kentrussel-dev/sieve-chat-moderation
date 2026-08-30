import json
import urllib.request

test_cases = [
    {
        "desc": "Combat Slang + Playful Emote (Reinforced Suppression)",
        "payload": {
            "text": "Bro you completely destroyed and murdered him KEKW PogChamp",
            "username": "Chatter1",
            "channel": "caedrel"
        }
    },
    {
        "desc": "Slang/Banter + Mocking Emote (Do NOT Suppress -> Hostility)",
        "payload": {
            "text": "Nice flash into the wall Pepega BabyRage",
            "username": "Chatter2",
            "channel": "caedrel"
        }
    },
    {
        "desc": "Ambiguous Message + Streamer Spoken Audio Context",
        "payload": {
            "text": "14.4k LO that lead is crazy",
            "username": "Chatter3",
            "channel": "caedrel",
            "streamer_caption_context": "we are so far ahead right now, fourteen thousand gold lead"
        }
    }
]

print("=== VERIFYING EMOTE & CAPTION CONTEXTUAL MODERATION ===")
for case in test_cases:
    req = urllib.request.Request(
        "http://localhost:8000/api/moderate",
        data=json.dumps(case["payload"]).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    res = json.loads(resp.read().decode("utf-8"))
    emote_labels = [f"{e['name']} ({e['category']})" for e in res.get('emotes', [])]
    print(f"[{case['desc']}]")
    print(f"  Utterance:        \"{res.get('text')}\"")
    print(f"  Detected Emotes:  {emote_labels}")
    print(f"  Caption Context:  \"{res.get('streamer_caption_context')}\"")
    print(f"  Verdict:          {res.get('status')} [Level {res.get('toxicity_level')}: {res.get('level_label')}] via {res.get('resolved_by_tier')}")
    print(f"  Reasoning:        {res.get('reasoning')}")
    print()
