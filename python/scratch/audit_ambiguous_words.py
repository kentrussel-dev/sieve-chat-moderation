import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import joblib
from config.toxicity_bands import map_score_to_band

model_path = os.path.join(os.path.dirname(__file__), "..", "models", "tier1_model.joblib")
model = joblib.load(model_path)

words = [
    "riot", "RIOT", "Riot", "Riot Games", "RIOT KEKW", "we riot if he loses",
    "blitz", "blitzcrank", "overwatch", "valorant", "savage", "trash", "garbage",
    "complete trash", "piece of garbage", "nice feed", "diff", "mid diff", "kill", "murdered that play",
    "gank", "smurf", "bait", "bkb", "rosh", "torture", "ez mid", "report my team"
]

print("=" * 80)
print(f"{'Token / Phrase':<30} {'Mesh 1 Prob (p)':<18} {'Level':<8} {'Band Label'}")
print("-" * 80)
for w in words:
    p = float(model.predict_proba([w])[0][1])
    band = map_score_to_band(p)
    print(f"{w:<30} {p:<18.4f} L{band.level:<7} {band.label}")
print("=" * 80)
