package model

import (
	"time"
)

type VerdictStatus string

const (
	VerdictPassed  VerdictStatus = "PASSED"
	VerdictFlagged VerdictStatus = "FLAGGED"
)

type TierLevel string

const (
	Tier0Deterministic TierLevel = "TIER_0"
	Tier1Local         TierLevel = "TIER_1"
	Tier2LLM           TierLevel = "TIER_2"
)

type RouteDecision string

const (
	RoutePassed    RouteDecision = "PASSED"
	RouteFlagged   RouteDecision = "FLAGGED"
	RouteEscalated RouteDecision = "ESCALATED"
)

// 6-Level Toxicity Band Constants
const (
	Level1Clean              int = 1 // 0.00 - 0.15
	Level2GamingSlang        int = 2 // 0.16 - 0.35 (False Alarm)
	Level3AmbiguousSarcastic int = 3 // 0.36 - 0.55
	Level4SubtleHostility    int = 4 // 0.56 - 0.70
	Level5Toxic              int = 5 // 0.71 - 0.88
	Level6SevereExtreme      int = 6 // 0.89 - 1.00
)

// EmoteMatch represents a detected Twitch / 7TV / BTTV emote and its verified sentiment category.
type EmoteMatch struct {
	Name     string `json:"name"`
	Category string `json:"category"` // playful/laughing, celebratory, sarcasm-marker, hostile/mocking, unclassified
	Source   string `json:"source"`   // 7tv, bttv, ffz, twitch
}

// MessageContext carries multi-signal contextual intelligence for a chat message.
type MessageContext struct {
	Emotes                 []EmoteMatch `json:"emotes,omitempty"`
	GamingEntities         []string     `json:"gaming_entities,omitempty"`
	StreamerCaptionContext *string      `json:"streamer_caption_context,omitempty"` // Rolling spoken caption from streamer audio
	ConversationID         string       `json:"conversation_id,omitempty"`
	PlayerSlot             int          `json:"player_slot,omitempty"`
	MatchTimeSeconds       int          `json:"match_time_seconds,omitempty"`
}

type ContentEvent struct {
	ID        string            `json:"id"`
	SourceID  string            `json:"source_id"`
	Text      string            `json:"text"`
	Context   *MessageContext   `json:"context,omitempty"`
	CreatedAt time.Time         `json:"created_at"`
	Metadata  map[string]string `json:"metadata,omitempty"`
}

type ClassificationRequest struct {
	EventID string          `json:"event_id"`
	Text    string          `json:"text"`
	Context *MessageContext `json:"context,omitempty"`
}

type ClassificationResponse struct {
	EventID          string             `json:"event_id"`
	IsToxic          bool               `json:"is_toxic"`
	ToxicityScore    float64            `json:"toxicity_score"`
	ToxicityLevel    int                `json:"toxicity_level"`
	LevelLabel       string             `json:"level_label"`
	FlaggedForReview bool               `json:"flagged_for_review"`
	Categories       map[string]float64 `json:"categories,omitempty"`
	InferenceTimeMs  float64            `json:"inference_time_ms"`
	ModelVersion     string             `json:"model_version"`
}

type EscalationPayload struct {
	Event            ContentEvent   `json:"event"`
	Context          MessageContext `json:"context"`
	Tier1Score       float64        `json:"tier1_score"`
	ToxicityLevel    int            `json:"toxicity_level"`
	LevelLabel       string         `json:"level_label"`
	Tier1LatencyMs   float64        `json:"tier1_latency_ms"`
	EscalationReason string         `json:"escalation_reason"`
	EscalatedAt      time.Time      `json:"escalated_at"`
}

type LLMModerationRequest struct {
	EventID string          `json:"event_id"`
	Text    string          `json:"text"`
	Context *MessageContext `json:"context,omitempty"`
}

type LLMModerationResponse struct {
	EventID       string   `json:"event_id"`
	IsToxic       bool     `json:"is_toxic"`
	ToxicityScore float64  `json:"toxicity_score"`
	ToxicityLevel int      `json:"toxicity_level"`
	LevelLabel    string   `json:"level_label"`
	Confidence    float64  `json:"confidence"`
	Categories    []string `json:"categories"`
	Reasoning     string   `json:"reasoning"`
	LatencyMs     float64  `json:"latency_ms"`
	ModelName     string   `json:"model_name"`
}

type ModerationVerdict struct {
	EventID          string        `json:"event_id"`
	Text             string        `json:"text,omitempty"`
	Status           VerdictStatus `json:"status"`
	ToxicityScore    float64       `json:"toxicity_score"`
	ToxicityLevel    int           `json:"toxicity_level"`
	LevelLabel       string        `json:"level_label"`
	Confidence       float64       `json:"confidence,omitempty"`
	FlaggedForReview bool          `json:"flagged_for_review"`
	ResolvedByTier   TierLevel     `json:"resolved_by_tier"`
	Categories       []string      `json:"categories,omitempty"`
	Reasoning        string        `json:"reasoning,omitempty"`
	DecisionReason   string        `json:"decision_reason,omitempty"`
	Tier1LatencyMs   float64       `json:"tier1_latency_ms,omitempty"`
	Tier2LatencyMs   float64       `json:"tier2_latency_ms,omitempty"`
	TotalLatencyMs   float64       `json:"total_latency_ms"`
	ResolvedAt       time.Time     `json:"resolved_at,omitempty"`
	EvaluatedAt      time.Time     `json:"evaluated_at"`
}

// EvaluateThresholds determines whether a score passes, flags, or escalates based on confidence margins.
func EvaluateThresholds(score, tauLow, tauHigh float64) RouteDecision {
	if score < tauLow {
		return RoutePassed
	}
	if score > tauHigh {
		return RouteFlagged
	}
	return RouteEscalated
}
