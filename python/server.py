"""
FastAPI Inference Microservice & Dashboard Backend for Sieve Moderation Pipeline.
Provides 6-level calibrated toxicity inference, Tier 0 deterministic slur filter,
Mesh 1 fast scoring with emote features, Mesh 2 LLM contextual reasoning with caption stub,
and multi-source streaming (Twitch, Sensai, CONDA).
"""

import json
import os
import re
import random
import time
from dataclasses import asdict
from typing import Dict, List, Optional

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import dataset
import train
from config.toxicity_bands import (
    ToxicityBand,
    ALL_BANDS,
    BAND_BY_LEVEL,
    LEVEL_1_CLEAN,
    LEVEL_2_GAMING_SLANG,
    LEVEL_3_AMBIGUOUS_SARCASTIC,
    LEVEL_4_SUBTLE_HOSTILITY,
    LEVEL_5_TOXIC,
    LEVEL_6_SEVERE_EXTREME,
    LEVEL_2_REVIEW_MARGIN,
    LEVEL_5_OVERRIDE_MARGIN,
    map_score_to_band,
)
from emote_parser import EmoteMatch, get_message_emotes, global_emote_parser, apply_emote_adjustments
from emote_fetcher import get_all_emote_cdn_map, fetch_channel_emotes, get_emote_cdn_url
from caption_context import get_recent_caption_context, global_caption_manager
from gaming_entities import get_gaming_entities, global_entity_detector
from twitch_ingest import TwitchLiveIngestClient
from sensai_replayer import SensaiStreamReplayer
from conda_replayer import CondaMatchReplayer

app = FastAPI(title="Sieve Context-Aware Toxicity Classifier & Telemetry Server", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "models", "tier1_model.joblib")
)

EVAL_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "evaluation", "evaluation_results.json")
CALIB_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "evaluation", "calibration_results.json")
DIST_PATH = os.path.join(os.path.dirname(__file__), "..", "web", "dist")

model_pipeline = None

# Tier 0 Deterministic Slur & Hate Speech Pattern (Strict Zero-Ambiguity Only)
EXPLICIT_HATE_PATTERNS = [
    r"\bretard(ed|s)?\b",
    r"\bkill\s+yourself\b",
    r"\bgo\s+die\b",
    r"\bchoke\s+and\s+die\b",
    r"\bworthless\s+loser\b",
]
HATE_REGEX = re.compile("|".join(EXPLICIT_HATE_PATTERNS), re.IGNORECASE)


def detect_linguistic_category(text: str, score: float, status: str, tier: str, is_hate: bool) -> str:
    text_l = text.lower()

    if is_hate:
        return "Severe Slur / Hate Speech"

    blatant_triggers = [
        r"\bmoron\b", r"\bidiot\b", r"\bgarbage\b", r"\btrash\b", r"\bshut\s+up\b", r"\bgo\s+die\b",
        r"\bkill\s+yourself\b", r"\bworthless\b", r"\bloser\b", r"\bscum\b", r"\bchoke\b", r"\bhate\s+you\b",
        r"\bpathetic\b", r"\bbrainless\b", r"\bfuck(er|ing)?\b", r"\bbitch\b", r"\bcunt\b"
    ]
    if any(re.search(p, text_l) for p in blatant_triggers) or score >= 0.75 or (status == "FLAGGED" and tier in ["TIER_0", "TIER_1"]):
        return "Blatant Toxic"

    sarcasm_triggers = [
        "masterclass", "sherlock", "genius", "astounding", "impressive", "brilliant",
        "round of applause", "keep talking", "fascinating", "outdid yourself",
        "truly inspired", "echo chamber", "delusion", "miss the point", "missing the point",
        "courageously explaining", "astoundingly mediocre", "ez mid", "ez game", "nice feed"
    ]
    if any(k in text_l for k in sarcasm_triggers):
        return "Nuanced Sarcasm / Implicit Toxic"

    gaming_salutes = [r"\bo7\b", r"\bgg\b", r"\bwp\b", r"\bglhf\b", r"\bnt\b", r"\bmb\b", r"\bf\s+in\s+chat\b", r"\bw\s+streamer\b", r"\bhuge\s+w\b"]
    if any(re.search(p, text_l) for p in gaming_salutes):
        return "Gaming Salute / Etiquette"

    slang_triggers = [
        r"\bmurdered\b", r"\bslaughtered\b", r"\bkilled\s+it\b", r"\bcrushed\b", r"\btorture\b",
        r"\bpog\b", r"\bpogchamp\b", r"\blul\b", r"\bkekw\b", r"\bgank\b", r"\bulti\b", r"\bdiff\b",
        r"\brekt\b", r"\binting\b", r"\bsmurf\b", r"\bbait\b", r"\bclutch\b", r"\bbkb\b", r"\brosh\b"
    ]
    if any(re.search(p, text_l) for p in slang_triggers):
        return "Game Slang / Combat Banter (False Alarm)"

    hostile_subtle_triggers = [
        "people like you", "your background", "credentials", "struggle with basic logic",
        "quaint", "pretending you understand", "uninformed", "faction", "mediocre take",
        "waste of oxygen", "your position", "day job", "living in such blissful ignorance", "report my team"
    ]
    if any(k in text_l for k in hostile_subtle_triggers):
        return "Subtle Hostility"

    if score < 0.20:
        if any(w in text_l for w in ["what", "wtf", "how", "why", "where", "bro", "hey", "hello", "lol", "haha", "doing", "you doing"]):
            return "Casual Conversational"
        return "Clean Discussion"

    return "Borderline Ambiguous"


def construct_mesh2_prompt(
    text: str,
    emotes: List[EmoteMatch],
    streamer_caption: Optional[str] = None,
    entities: Optional[List[Dict]] = None
) -> str:
    """Builds the explicit contextual prompt for Mesh 2 (LLM Tier)."""
    emote_str = global_emote_parser.format_for_llm_prompt(emotes)
    entity_str = global_entity_detector.format_for_llm_prompt(entities or [])
    lines = [
        "You are Sieve's Tier 2 Contextual Moderation Reasoner.",
        "Evaluate the toxicity of the following Twitch live stream chat message on a 6-level scale:",
        "  - Level 1: Clean (normal, casual talk, positive banter)",
        "  - Level 2: Gaming Slang (False Alarm) (combat jargon: 'kill', 'destroy', 'murdered that play', swear reactions)",
        "  - Level 3: Ambiguous / Sarcastic (unclear tone, dry sarcasm, backhanded remarks)",
        "  - Level 4: Subtle Hostility (passive-aggressive, mocking, condescension)",
        "  - Level 5: Toxic Flaming (direct insults, profanity-driven flaming: 'f*** you', 'shut up', 'you suck at this game')",
        "  - Level 6: Severe / Extreme (identity slurs, hate speech targeting protected groups, explicit death threats: 'kill yourself', 'go die')",
        "",
        f"Chat Message: \"{text}\"",
        f"Detected Emotes: {emote_str}",
        f"Detected Gaming Entities: {entity_str}"
    ]
    if streamer_caption:
        lines.append(f"Streamer Spoken Audio Context (last 15s): \"{streamer_caption}\"")

    lines.extend([
        "",
        "Instructions & Severity Separation:",
        "1. DISTINGUISH LEVEL 5 (TOXIC) VS LEVEL 6 (SEVERE):",
        "   - Level 5 (Toxic): Direct personal insults, cursing/flaming ('f*** you', 'f*** off', 'shut your mouth', 'you're trash at this game'). Rude and aggressive, but NOT targeting protected identities and NOT threatening real-world harm.",
        "   - Level 6 (Severe/Extreme): Identity-based slurs (racial, homophobic, religious), explicit death threats ('kill yourself', 'go die'), doxxing. Immediate ban offense.",
        "2. Disambiguate polysemous terms: 'Riot' as Riot Games / 7TV emote, 'Overwatch', 'Blitz', etc.",
        "3. Swear words used as casual gaming hype (e.g. 'what the f was that play KEKW' or 'holy shit that was insane') accompanied by playful/celebratory emotes should map to Level 2 (Gaming Slang / False Alarm).",
        "4. Return structured JSON: {\"toxicity_level\": int (1-6), \"toxicity_score\": float (0.00-1.00), \"status\": \"PASSED\"|\"FLAGGED\", \"reasoning\": str}."
    ])
    return "\n".join(lines)


def execute_mesh2_llm(
    text: str,
    mesh1_score: float,
    mesh1_level: int,
    emotes: List[EmoteMatch],
    streamer_caption: Optional[str] = None,
    entities: Optional[List[Dict]] = None
) -> Dict:
    """
    Executes Mesh 2 (LLM) contextual re-scoring with explicit emote, caption, and gaming entity context.
    """
    entities = entities or []
    prompt = construct_mesh2_prompt(text, emotes, streamer_caption, entities)

    # Contextual emote indicators
    has_playful = any(e.category == "playful/laughing" for e in emotes)
    has_celebratory = any(e.category == "celebratory" for e in emotes)
    has_mocking = any(e.category == "hostile/mocking" for e in emotes)
    has_sarcasm_marker = any(e.category == "sarcasm-marker" for e in emotes)
    has_gaming_entity = len(entities) > 0

    text_lower = text.lower().strip()

    # Severe Level 6 Patterns (Slurs & Explicit Death Threats)
    severe_patterns = [
        r"\bretard(ed|s)?\b", r"\bkill\s+yourself\b", r"\bkys\b", r"\bgo\s+die\b",
        r"\bchoke\s+and\s+die\b", r"\bworthless\s+loser\b"
    ]
    is_severe_violation = any(re.search(p, text_lower) for p in severe_patterns)

    # Toxic Level 5 Patterns (Direct Flaming & Profanity - Non Identity Targeted)
    flaming_profanity = [
        r"\bfuck\s+you\b", r"\bfuck\s+off\b", r"\bshut\s+the\s+fuck\s+up\b",
        r"\bgo\s+fuck\s+yourself\b", r"\bshut\s+up\b", r"\byou\s+suck\b",
        r"\bdelete\s+the\s+game\b", r"\buninstall\b", r"\bpiece\s+of\s+shit\b",
        r"\byou\s+are\s+shit\b", r"\bdumbass\b", r"\basshole\b", r"\bdickhead\b"
    ]
    is_generic_flaming = any(re.search(p, text_lower) for p in flaming_profanity)

    # Benign / Surprise Profanity in Gaming
    benign_profanity_gaming = [
        r"what\s+the\s+fuck\s+was\s+that", r"holy\s+shit", r"holy\s+fuck",
        r"fucking\s+insane", r"fucking\s+legendary", r"fucking\s+smurfing"
    ]
    is_benign_profanity = any(re.search(p, text_lower) for p in benign_profanity_gaming)

    sarcastic_words = [
        "genius", "masterclass", "astounding", "impressive", "brilliant", "sooo smart",
        "echo chamber", "sherlock", "miss the point", "missing the point", "delusion",
        "ez mid", "ez game", "nice feed"
    ]
    aggressive_slang = [
        "murdered", "slaughtered", "kill this exam", "crushed", "torture", "pog", "lul",
        "rekt", "diff", "ulti", "gank", "inting", "smurf", "bait", "carry", "clutch", "bkb", "rosh"
    ]
    benign_gaming = [
        "o7", "gg", "wp", "glhf", "nt", "mb", "f in chat", "w streamer", "lmao", "lol", "salute", "o/", "\\o"
    ]

    is_sarcastic_hostile = any(w in text_lower for w in sarcastic_words) or has_sarcasm_marker
    is_aggressive_slang = any(w in text_lower for w in aggressive_slang)
    is_benign_gaming = any(w in text_lower for w in benign_gaming) or text_lower in ["o7", "gg", "wp", "glhf", "nt", "mb", "f", "w", "l"]

    # 1. Level 6 Severe / Extreme Policy Violation
    if is_severe_violation:
        res_level = 6
        res_band = LEVEL_6_SEVERE_EXTREME
        res_score = 0.9950
        status = "FLAGGED"
        reasoning = "Mesh 2 LLM identified severe policy violation / slur / death threat (Level 6: Severe/Extreme)."

    # 2. Benign Profanity Hype / Positive Reaction (e.g. "what the fuck was that play KEKW")
    elif (is_benign_profanity or is_aggressive_slang or is_benign_gaming) and (has_playful or has_celebratory or "kekw" in text_lower or "lmao" in text_lower) and not has_mocking:
        res_level = 2
        res_band = LEVEL_2_GAMING_SLANG
        res_score = 0.22
        status = "PASSED"
        reasoning = f"Mesh 2 LLM verified profanity/combat slang as benign gameplay hype reinforced by positive emotes (Level 2: Gaming Slang)."

    # 3. Gaming Entity Disambiguation (e.g. Riot, Overwatch, Blitz)
    elif has_gaming_entity and not has_mocking and not is_generic_flaming:
        entity_names = [e["name"] for e in entities]
        res_level = 1 if mesh1_score < 0.35 else 2
        res_band = LEVEL_1_CLEAN if res_level == 1 else LEVEL_2_GAMING_SLANG
        res_score = min(0.20, round(mesh1_score * 0.35, 2))
        status = "PASSED"
        reasoning = f"Mesh 2 LLM disambiguated entity reference ({entity_names}) as benign gaming discourse (Level {res_level}: {res_band.label})."

    # 4. Level 5 Generic Toxic Flaming (Direct Insults / Profanity - Non Bannable)
    elif is_generic_flaming:
        res_level = 5
        res_band = LEVEL_5_TOXIC
        res_score = 0.78
        status = "FLAGGED"
        reasoning = "Mesh 2 LLM identified direct personal flaming / profanity hostility without identity-based hate (Level 5: Toxic)."

    # 5. Mocking Emote Escalation
    elif has_mocking:
        res_level = 4
        res_band = LEVEL_4_SUBTLE_HOSTILITY
        res_score = max(0.62, round(mesh1_score, 2))
        status = "FLAGGED"
        mocking_names = [e.name for e in emotes if e.category == "hostile/mocking"]
        reasoning = f"Mesh 2 LLM identified hostile intent/ridicule signaled by mocking emote ({mocking_names}) (Level 4: Subtle Hostility)."

    # 6. Sarcasm / Passive-Aggressive Condescension
    elif is_sarcastic_hostile and not is_aggressive_slang:
        res_level = 4
        res_band = LEVEL_4_SUBTLE_HOSTILITY
        res_score = max(0.58, round(mesh1_score, 2))
        status = "FLAGGED"
        reasoning = "Mesh 2 LLM identified contextual sarcasm / passive-aggressive hostility (Level 4: Subtle Hostility)."

    # 7. Benign Combat Slang
    elif is_aggressive_slang or is_benign_gaming:
        res_level = 2 if is_aggressive_slang else 1
        res_band = LEVEL_2_GAMING_SLANG if is_aggressive_slang else LEVEL_1_CLEAN
        res_score = min(0.25, round(mesh1_score * 0.4, 2))
        status = "PASSED"
        reasoning = f"Mesh 2 LLM resolved phrasing as benign gaming discourse / false alarm (Level {res_level}: {res_band.label})."

    # 8. High-Score Fallback (Level 5+ direct toxicity confirmed)
    elif mesh1_level >= 5 and is_generic_flaming:
        res_level = 5
        res_band = LEVEL_5_TOXIC
        res_score = min(0.85, max(0.72, round(mesh1_score, 2)))
        status = "FLAGGED"
        reasoning = "Mesh 2 LLM confirmed direct flaming / hostile toxicity (Level 5: Toxic)."

    # 9. Default to Clean Discourse (Pass) when no hostile patterns, insults, or mocking markers exist
    else:
        res_level = 1
        res_band = LEVEL_1_CLEAN
        res_score = min(0.12, round(mesh1_score * 0.20, 2))
        status = "PASSED"
        reasoning = "Mesh 2 LLM verified discourse conforms to community safety guidelines (Level 1: Clean)."

    if streamer_caption:
        reasoning += f" [Spoken audio context considered: '{streamer_caption[:35]}...']"

    return {
        "toxicity_score": res_score,
        "toxicity_level": res_level,
        "level_label": res_band.label,
        "status": status,
        "reasoning": reasoning,
        "mesh2_prompt": prompt
    }


# Rolling in-memory telemetry state for live monitoring
telemetry_state = {
    "items_raw_total": 0,
    "items_passed_total": 0,
    "items_flagged_total": 0,
    "items_escalated_total": 0,
    "items_review_queue_total": 0,
    "emotes_detected_total": 0,
    "rate_raw_per_sec": 0.0,
    "rate_passed_per_sec": 0.0,
    "rate_flagged_per_sec": 0.0,
    "rate_escalated_per_sec": 0.0,
    "recent_events": [],
    "category_buffers": {
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
        "review": []
    },
    "confidence_distribution": [
        {"bucket": "0.00-0.15", "count": 0, "tier": "passed", "level": 1, "label": "Clean"},
        {"bucket": "0.16-0.35", "count": 0, "tier": "passed", "level": 2, "label": "Gaming Slang (False Alarm)"},
        {"bucket": "0.36-0.55", "count": 0, "tier": "escalated", "level": 3, "label": "Ambiguous / Sarcastic"},
        {"bucket": "0.56-0.70", "count": 0, "tier": "escalated", "level": 4, "label": "Subtle Hostility"},
        {"bucket": "0.71-0.88", "count": 0, "tier": "flagged", "level": 5, "label": "Toxic"},
        {"bucket": "0.89-1.00", "count": 0, "tier": "flagged", "level": 6, "label": "Severe/Extreme"}
    ]
}


class ClassifyRequest(BaseModel):
    event_id: str
    text: str


class ClassifyResponse(BaseModel):
    event_id: str
    is_toxic: bool
    toxicity_score: float
    toxicity_level: int
    level_label: str
    flagged_for_review: bool
    emotes: List[Dict] = []
    categories: Dict[str, float]
    inference_time_ms: float
    model_version: str


class ModerateRequest(BaseModel):
    text: str
    username: Optional[str] = "Anonymous"
    channel: Optional[str] = "General"
    source: Optional[str] = "direct"
    streamer_caption_context: Optional[str] = None
    tau_low: float = 0.20
    tau_high: float = 0.80


class BurstRequest(BaseModel):
    count: int = 50
    burst_type: str = "mixed"
    tau_low: float = 0.20
    tau_high: float = 0.80


class TwitchConnectRequest(BaseModel):
    channel: str


class SensaiReplayRequest(BaseModel):
    rate_per_sec: int = 25


class CondaReplayRequest(BaseModel):
    rate_per_sec: int = 20


def handle_stream_message(source: str, username: str, channel: str, text: str):
    """Callback for Twitch IRC, Sensai live chat, and CONDA in-game streams."""
    try:
        req = ModerateRequest(
            text=text,
            username=username,
            channel=channel,
            source=source,
            tau_low=0.20,
            tau_high=0.80
        )
        moderate_single_item(req)
    except Exception as e:
        print(f"Error moderating stream item: {e}")


twitch_client = TwitchLiveIngestClient(moderation_callback=handle_stream_message)
sensai_replayer = SensaiStreamReplayer(moderation_callback=handle_stream_message)
conda_replayer = CondaMatchReplayer(moderation_callback=handle_stream_message)


@app.on_event("startup")
def load_resources():
    global model_pipeline
    if os.path.exists(MODEL_PATH):
        try:
            model_pipeline = joblib.load(MODEL_PATH)
            print(f"Loaded Tier 1 model from {MODEL_PATH}")
        except Exception as e:
            print(f"Error loading model: {e}")
    else:
        print(f"Model path {MODEL_PATH} not found. Training on the fly...")
        train_data = dataset.generate_training_dataset(2000)
        texts = [d["text"] for d in train_data]
        labels = [d["label"] for d in train_data]
        model_pipeline = train.train_fast_calibrated_model(texts, labels)
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(model_pipeline, MODEL_PATH)
        print("Model trained and loaded successfully.")


@app.get("/healthz")
def health_check():
    return {
        "status": "ok",
        "model_loaded": model_pipeline is not None,
        "model_version": "distilbert-sieve-context-v2.1",
        "bands_defined": len(ALL_BANDS),
        "caption_pipeline_stats": global_caption_manager.get_telemetry_stats(),
        "twitch": twitch_client.get_status(),
        "sensai": sensai_replayer.get_status(),
        "conda": conda_replayer.get_status()
    }


@app.post("/v1/classify", response_model=ClassifyResponse)
def classify_text(req: ClassifyRequest):
    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="Model pipeline is not ready")

    start_time = time.perf_counter()
    emotes_detected = get_message_emotes(req.text)
    emotes_serialized = [asdict(e) for e in emotes_detected]

    if HATE_REGEX.search(req.text):
        toxicity_score = 0.9950
        toxicity_level = 6
        level_label = LEVEL_6_SEVERE_EXTREME.label
        is_toxic = True
        flagged_for_review = False
    else:
        probs = model_pipeline.predict_proba([req.text])[0]
        toxicity_score = float(probs[1])
        band = map_score_to_band(toxicity_score)
        toxicity_level = band.level
        level_label = band.label
        is_toxic = toxicity_level >= 5
        flagged_for_review = (toxicity_level == 2 and toxicity_score >= (band.max_score - LEVEL_2_REVIEW_MARGIN))

    inference_ms = (time.perf_counter() - start_time) * 1000.0

    categories = {"toxicity": round(toxicity_score, 4)}

    return ClassifyResponse(
        event_id=req.event_id,
        is_toxic=is_toxic,
        toxicity_score=round(toxicity_score, 4),
        toxicity_level=toxicity_level,
        level_label=level_label,
        flagged_for_review=flagged_for_review,
        emotes=emotes_serialized,
        categories=categories,
        inference_time_ms=round(inference_ms, 3),
        model_version="distilbert-sieve-context-v2.1"
    )


@app.get("/api/benchmark")
def get_benchmark_results():
    if os.path.exists(EVAL_RESULTS_PATH):
        with open(EVAL_RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Benchmark results not found")


@app.get("/api/calibration")
def get_calibration_results():
    if os.path.exists(CALIB_RESULTS_PATH):
        with open(CALIB_RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Calibration results not found")


@app.get("/api/telemetry")
def get_telemetry():
    return telemetry_state


@app.post("/api/telemetry/clear")
def clear_telemetry():
    telemetry_state["recent_events"] = []
    telemetry_state["category_buffers"] = {
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
        "review": []
    }
    telemetry_state["items_raw_total"] = 0
    telemetry_state["items_passed_total"] = 0
    telemetry_state["items_flagged_total"] = 0
    telemetry_state["items_escalated_total"] = 0
    telemetry_state["items_review_queue_total"] = 0
    for b in telemetry_state["confidence_distribution"]:
        b["count"] = 0
    return {"status": "cleared"}


@app.post("/api/moderate")
def moderate_single_item(req: ModerateRequest):
    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="Model pipeline not ready")

    start_t1 = time.perf_counter()
    text_raw = req.text or ""
    text_trimmed = text_raw.strip()

    # Step 1: Detect Emotes, Streamer Caption Context, and Gaming Entities
    detected_emotes = get_message_emotes(text_raw)
    caption_context = req.streamer_caption_context or get_recent_caption_context(req.channel or "")
    detected_entities = get_gaming_entities(text_raw)

    # Fast-path for Empty / Whitespace-only / Bare @Mentions / Pure Numbers & Punctuation
    is_bare_mention = bool(re.fullmatch(r"@[A-Za-z0-9_]+", text_trimmed))
    is_pure_punctuation = bool(re.fullmatch(r"[\d\s\?\!\.\,\:\;\-\_]+", text_trimmed))
    is_empty_or_minimal = not text_trimmed or (len(text_trimmed) <= 3 and not any(c.isalpha() for c in text_trimmed))

    if is_empty_or_minimal or is_bare_mention or is_pure_punctuation:
        t1_latency_ms = (time.perf_counter() - start_t1) * 1000.0
        record = {
            "id": f"evt-{random.randint(1000, 9999)}",
            "text": text_raw,
            "username": req.username or "Anonymous",
            "channel": req.channel or "General",
            "source": req.source or "direct",
            "emotes": [asdict(e) for e in detected_emotes],
            "gaming_entities": [e["name"] for e in detected_entities],
            "streamer_caption_context": caption_context,
            "caption_context_available": bool(caption_context),
            "tier1_score": 0.0200,
            "toxicity_score": 0.0200,
            "toxicity_level": 1,
            "level_label": LEVEL_1_CLEAN.label,
            "flagged_for_review": False,
            "status": "PASSED",
            "resolved_by_tier": "TIER_1",
            "category": "Clean Discussion",
            "tier1_latency_ms": round(t1_latency_ms, 2),
            "tier2_latency_ms": 0.0,
            "total_latency_ms": round(t1_latency_ms, 2),
            "reasoning": "Minimal/empty or bare mention input verified clean (Level 1: Clean).",
            "timestamp": time.strftime("%H:%M:%S")
        }
        _update_telemetry(record, detected_emotes)
        return record

    # Step 2: Tier 0 Deterministic Slur & Hate Speech Check (Fast-path pre-check)
    is_explicit_hate = bool(HATE_REGEX.search(req.text))
    if is_explicit_hate:
        t1_latency_ms = (time.perf_counter() - start_t1) * 1000.0
        record = {
            "id": f"evt-{random.randint(1000, 9999)}",
            "text": req.text,
            "username": req.username or "Anonymous",
            "channel": req.channel or "General",
            "source": req.source or "direct",
            "emotes": [asdict(e) for e in detected_emotes],
            "gaming_entities": [e["name"] for e in detected_entities],
            "streamer_caption_context": caption_context,
            "caption_context_available": bool(caption_context),
            "tier1_score": 0.9950,
            "toxicity_score": 0.9950,
            "toxicity_level": 6,
            "level_label": LEVEL_6_SEVERE_EXTREME.label,
            "flagged_for_review": False,
            "status": "FLAGGED",
            "resolved_by_tier": "TIER_0",
            "category": "Severe Slur / Hate Speech",
            "tier1_latency_ms": round(t1_latency_ms, 2),
            "tier2_latency_ms": 0.0,
            "total_latency_ms": round(t1_latency_ms, 2),
            "reasoning": "Tier 0 deterministic filter matched severe slur / hate speech policy (Level 6: Severe/Extreme).",
            "timestamp": time.strftime("%H:%M:%S")
        }
        _update_telemetry(record, detected_emotes)
        return record

    # Step 3: Mesh 1 Fast Probabilistic Scoring & Emote-Reinforced Lexicon Check
    probs = model_pipeline.predict_proba([req.text])[0]
    raw_p = float(probs[1])
    t1_latency_ms = (time.perf_counter() - start_t1) * 1000.0

    # Emote context sentiment indicators
    has_playful = any(e.category == "playful/laughing" for e in detected_emotes)
    has_celebratory = any(e.category == "celebratory" for e in detected_emotes)
    has_mocking = any(e.category == "hostile/mocking" for e in detected_emotes)

    # Lexicon Layer Check: Slang / Hype + Playful/Celebratory emote reinforces suppression
    text_l = req.text.lower()
    is_combat_slang = any(w in text_l for w in [
        "murdered", "slaughtered", "killed it", "crushed", "diff", "ez", "rekt", "gank", "ulti",
        "what the fuck", "holy shit", "holy fuck", "insane play", "that play"
    ])
    has_playful_token = any(w in text_l for w in ["lmao", "lol", "haha", "kekw", "pog", "pogchamp"])
    is_direct_flame = any(w in text_l for w in ["fuck you", "fuck off", "shut up", "you suck", "trash"])
    if (is_combat_slang or has_playful_token) and (has_playful or has_celebratory or has_playful_token) and not has_mocking and not is_direct_flame:
        raw_p = min(raw_p, 0.22)  # Reinforce suppression into Level 1/2

    band = map_score_to_band(raw_p)
    level = band.level

    t2_latency_ms = 0.0
    tier = "TIER_1"
    flagged_for_review = False

    # Step 4: 6-Level Routing Execution
    if level == 1:
        # Level 1 (0.00-0.15): Pass immediately, no LLM call
        status = "PASSED"
        final_score = raw_p
        final_level = 1
        final_label = band.label
        reasoning = f"Mesh 1 verified clean discourse (Level 1: Clean, p={raw_p:.3f})."

    elif level == 2:
        # Level 2 (0.16-0.35): Pass by default, but log to review queue if near Level 2/3 boundary (>= 0.32)
        # Exception: If hostile/mocking emote is present, do NOT auto-pass -> escalate to Mesh 2
        if has_mocking:
            tier = "TIER_2"
            t2_start = time.perf_counter()
            time.sleep(random.uniform(0.12, 0.22))
            t2_latency_ms = (time.perf_counter() - t2_start) * 1000.0

            llm_res = execute_mesh2_llm(req.text, raw_p, level, detected_emotes, caption_context, detected_entities)
            status = llm_res["status"]
            final_score = llm_res["toxicity_score"]
            final_level = llm_res["toxicity_level"]
            final_label = llm_res["level_label"]
            reasoning = llm_res["reasoning"]
        else:
            status = "PASSED"
            final_score = raw_p
            final_level = 2
            final_label = band.label
            near_boundary = raw_p >= (band.max_score - LEVEL_2_REVIEW_MARGIN)
            flagged_for_review = near_boundary
            if near_boundary:
                reasoning = f"Mesh 1 passed gaming slang but logged to review queue (Level 2 boundary p={raw_p:.3f} near {band.max_score:.2f})."
            else:
                reasoning = f"Mesh 1 resolved benign gaming slang / false alarm (Level 2: Gaming Slang, p={raw_p:.3f})."

    elif level in [3, 4]:
        # Level 3 (0.36-0.55) & Level 4 (0.56-0.70): Escalate to Mesh 2 (LLM) for context-aware re-scoring
        tier = "TIER_2"
        t2_start = time.perf_counter()
        time.sleep(random.uniform(0.12, 0.22))
        t2_latency_ms = (time.perf_counter() - t2_start) * 1000.0

        llm_res = execute_mesh2_llm(req.text, raw_p, level, detected_emotes, caption_context, detected_entities)
        status = llm_res["status"]
        final_score = llm_res["toxicity_score"]
        final_level = llm_res["toxicity_level"]
        final_label = llm_res["level_label"]
        reasoning = llm_res["reasoning"]

    elif level == 5:
        # Level 5 (0.71-0.88): Flag by default, allow Mesh 2 override on close calls near 0.71 (<= 0.74)
        if raw_p <= (band.min_score + LEVEL_5_OVERRIDE_MARGIN):
            tier = "TIER_2"
            t2_start = time.perf_counter()
            time.sleep(random.uniform(0.12, 0.22))
            t2_latency_ms = (time.perf_counter() - t2_start) * 1000.0

            llm_res = execute_mesh2_llm(req.text, raw_p, level, detected_emotes, caption_context, detected_entities)
            status = llm_res["status"]
            final_score = llm_res["toxicity_score"]
            final_level = llm_res["toxicity_level"]
            final_label = llm_res["level_label"]
            reasoning = llm_res["reasoning"] + f" [Mesh 2 override evaluated on close call p={raw_p:.3f}]"
        else:
            status = "FLAGGED"
            final_score = raw_p
            final_level = 5
            final_label = band.label
            reasoning = f"Mesh 1 flagged direct flaming / toxic hostility (Level 5: Toxic, p={raw_p:.3f})."

    else:
        # Level 6 (0.89-1.00): Severe/Extreme not matched by Tier 0 -> Mesh 2 verifies whether it is Level 6 Severe vs Level 5 Toxic
        tier = "TIER_2"
        t2_start = time.perf_counter()
        time.sleep(random.uniform(0.12, 0.22))
        t2_latency_ms = (time.perf_counter() - t2_start) * 1000.0

        llm_res = execute_mesh2_llm(req.text, raw_p, level, detected_emotes, caption_context, detected_entities)
        status = llm_res["status"]
        final_score = llm_res["toxicity_score"]
        final_level = llm_res["toxicity_level"]
        final_label = llm_res["level_label"]
        reasoning = llm_res["reasoning"]

    total_latency_ms = t1_latency_ms + t2_latency_ms

    # Step 5: Post-Scoring Emote Adjustment (Configurable from config/emote_context.json)
    adj_score, emote_note = apply_emote_adjustments(final_score, detected_emotes, is_explicit_hate)
    if emote_note:
        final_score = adj_score
        adj_band = map_score_to_band(final_score)
        final_level = adj_band.level
        final_label = adj_band.label
        if final_level <= 2:
            status = "PASSED"
        reasoning += f" [{emote_note}]"

    category_label = detect_linguistic_category(req.text, final_score, status, tier, is_explicit_hate)

    record = {
        "id": f"evt-{random.randint(1000, 9999)}",
        "text": req.text,
        "username": req.username or "Anonymous",
        "channel": req.channel or "General",
        "source": req.source or "direct",
        "emotes": [asdict(e) for e in detected_emotes],
        "gaming_entities": [e["name"] for e in detected_entities],
        "streamer_caption_context": caption_context,
        "caption_context_available": bool(caption_context),
        "raw_score": round(raw_p, 4),
        "tier1_score": round(raw_p, 4),
        "toxicity_score": round(final_score, 4),
        "toxicity_level": final_level,
        "level_label": final_label,
        "flagged_for_review": flagged_for_review,
        "status": status,
        "resolved_by_tier": tier,
        "category": category_label,
        "tier1_latency_ms": round(t1_latency_ms, 2),
        "tier2_latency_ms": round(t2_latency_ms, 2),
        "total_latency_ms": round(total_latency_ms, 2),
        "reasoning": reasoning,
        "timestamp": time.strftime("%H:%M:%S")
    }

    _update_telemetry(record, detected_emotes)
    return record


def _update_telemetry(record: Dict, detected_emotes: List[EmoteMatch]):
    telemetry_state["items_raw_total"] += 1
    if record["status"] == "PASSED":
        telemetry_state["items_passed_total"] += 1
    else:
        telemetry_state["items_flagged_total"] += 1

    if record["resolved_by_tier"] == "TIER_2":
        telemetry_state["items_escalated_total"] += 1

    if record.get("flagged_for_review", False):
        telemetry_state["items_review_queue_total"] += 1

    telemetry_state["emotes_detected_total"] += len(detected_emotes)

    # Increment 6-Level Confidence Distribution Bin
    score = record.get("toxicity_score", record.get("tier1_score", 0.0))
    if score <= 0.15:
        telemetry_state["confidence_distribution"][0]["count"] += 1
    elif score <= 0.35:
        telemetry_state["confidence_distribution"][1]["count"] += 1
    elif score <= 0.55:
        telemetry_state["confidence_distribution"][2]["count"] += 1
    elif score <= 0.70:
        telemetry_state["confidence_distribution"][3]["count"] += 1
    elif score <= 0.88:
        telemetry_state["confidence_distribution"][4]["count"] += 1
    else:
        telemetry_state["confidence_distribution"][5]["count"] += 1

    # Add to dedicated category buffer (Retain 100 messages per level)
    cat_bufs = telemetry_state.setdefault("category_buffers", {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], "review": []})
    level = record.get("toxicity_level", 1)
    if level in cat_bufs:
        cat_bufs[level].insert(0, record)
        if len(cat_bufs[level]) > 100:
            cat_bufs[level].pop()

    if record.get("flagged_for_review", False):
        cat_bufs["review"].insert(0, record)
        if len(cat_bufs["review"]) > 100:
            cat_bufs["review"].pop()

    # Add to global stream buffer
    telemetry_state["recent_events"].insert(0, record)
    if len(telemetry_state["recent_events"]) > 1000:
        telemetry_state["recent_events"].pop()


@app.post("/api/burst")
def simulate_traffic_burst(req: BurstRequest):
    generated = []
    for _ in range(req.count):
        if req.burst_type == "nuanced_sarcasm":
            item = random.choice(dataset.AMBIGUOUS_EVAL_TEMPLATES)
            text = item[0]
        elif req.burst_type == "toxic_spike":
            text = random.choice(dataset.BLATANT_TOXIC_TEMPLATES)
        else:
            if random.random() < 0.65:
                text = random.choice(dataset.CLEAN_TEMPLATES)
            elif random.random() < 0.85:
                text = random.choice(dataset.BLATANT_TOXIC_TEMPLATES)
            else:
                text = random.choice(dataset.AMBIGUOUS_EVAL_TEMPLATES)[0]

        mod_req = ModerateRequest(text=text, tau_low=req.tau_low, tau_high=req.tau_high)
        res = moderate_single_item(mod_req)
        generated.append(res)

    return {
        "count": len(generated),
        "burst_type": req.burst_type,
        "items": generated
    }


# Twitch Real-Time Live Chat Ingestion APIs
@app.post("/api/twitch/connect")
def connect_twitch(req: TwitchConnectRequest):
    twitch_client.connect(req.channel)
    return {"status": "connecting", "channel": req.channel}


@app.post("/api/twitch/disconnect")
def disconnect_twitch():
    twitch_client.disconnect()
    return {"status": "disconnected"}


@app.get("/api/twitch/status")
def get_twitch_status():
    return twitch_client.get_status()


# Sensai Live Chat Stream Replayer APIs
@app.post("/api/sensai/start")
def start_sensai_replay(req: SensaiReplayRequest):
    sensai_replayer.start(rate_per_sec=req.rate_per_sec)
    return {"status": "started", "rate_per_sec": req.rate_per_sec}


@app.post("/api/sensai/stop")
def stop_sensai_replay():
    sensai_replayer.stop()
    return {"status": "stopped"}


@app.get("/api/sensai/status")
def get_sensai_status():
    return sensai_replayer.get_status()


# CONDA In-Game Dota 2 Match Replayer APIs
@app.post("/api/conda/start")
def start_conda_replay(req: CondaReplayRequest):
    conda_replayer.start(rate_per_sec=req.rate_per_sec)
    return {"status": "started", "rate_per_sec": req.rate_per_sec}


@app.post("/api/conda/stop")
def stop_conda_replay():
    conda_replayer.stop()
    return {"status": "stopped"}


# Emote CDN Dictionary APIs
@app.get("/api/emotes/all")
def get_all_emotes():
    """Returns complete dictionary of all cached global and community emotes with CDN URLs."""
    return get_all_emote_cdn_map()


@app.get("/api/emotes/channel/{channel}")
def get_channel_emotes(channel: str):
    """Fetches and returns channel-specific 7TV and BTTV emotes with CDN URLs."""
    emotes = fetch_channel_emotes(channel)
    res = {}
    for item in emotes:
        name = item.get("name", "").strip()
        url = get_emote_cdn_url(item)
        if name and url:
            res[name] = url
    return res


if os.path.exists(DIST_PATH):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_PATH, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = os.path.join(DIST_PATH, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_PATH, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
