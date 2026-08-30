import urllib.request, json

test_messages = [
    "RIOT",
    "Riot Games fix the bug please",
    "we riot if he loses KEKW",
    "Overwatch is fun tonight",
    "Blitzcrank hook was insane",
    "my aim is pure trash today",
    "this server ping is absolute garbage",
    "kill the dragon before they rotate",
    "nice kill on the mid laner",
    "you are a worthless loser",
    "kill yourself"
]

print("=" * 90)
print(f"{'Message':<35} {'Tier':<8} {'Score':<8} {'Level':<8} {'Status':<8} {'Reasoning'}")
print("-" * 90)

for msg in test_messages:
    req = urllib.request.Request(
        "http://localhost:8000/api/moderate",
        data=json.dumps({"text": msg}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    tier = res.get("resolved_by_tier", "TIER_1")
    score = res.get("toxicity_score", 0.0)
    level = res.get("toxicity_level", 1)
    status = res.get("status", "PASSED")
    reasoning = res.get("reasoning", "")[:45]
    print(f"{msg:<35} {tier:<8} {score:<8.3f} L{level:<7} {status:<8} {reasoning}...")
print("=" * 90)
