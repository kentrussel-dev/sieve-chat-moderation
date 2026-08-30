import urllib.request, json

messages = [
    "10 MINUTES???",
    "10 minutes",
    "you can do it",
    "im not even gonna jynxzi",
    "god",
    "@drakuscs",
    "",
    "j ynxzi i love you",
    "stop trying to igl",
    "Jynxzi that was ur fault chud u little crybaby",
    "jynxi you dog",
    "jynxi you dog KEKW",
    "jynxi you dog Pepega",
    "RIOT",
    "RIOT KEKW"
]

print("=" * 105)
print(f"{'Message':<35} {'Tier':<8} {'RawScore':<10} {'ToxScore':<10} {'Level':<8} {'Status':<8} {'Reasoning'}")
print("-" * 105)

for msg in messages:
    req = urllib.request.Request(
        "http://localhost:8000/api/moderate",
        data=json.dumps({"text": msg}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    tier = res.get("resolved_by_tier", "TIER_1")
    raw = res.get("raw_score", res.get("tier1_score", 0.0))
    score = res.get("toxicity_score", 0.0)
    level = res.get("toxicity_level", 1)
    status = res.get("status", "PASSED")
    reasoning = res.get("reasoning", "")[:45]
    print(f"{msg:<35} {tier:<8} {raw:<10.3f} {score:<10.3f} L{level:<7} {status:<8} {reasoning}...")
print("=" * 105)
