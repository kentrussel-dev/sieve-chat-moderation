package model

import (
	"encoding/json"
	"testing"
	"time"
)

func TestEvaluateThresholds(t *testing.T) {
	tauLow := 0.20
	tauHigh := 0.80

	cases := []struct {
		score    float64
		expected RouteDecision
	}{
		{0.05, RoutePassed},
		{0.19, RoutePassed},
		{0.20, RouteEscalated},
		{0.50, RouteEscalated},
		{0.80, RouteEscalated},
		{0.81, RouteFlagged},
		{0.99, RouteFlagged},
	}

	for _, tc := range cases {
		actual := EvaluateThresholds(tc.score, tauLow, tauHigh)
		if actual != tc.expected {
			t.Errorf("EvaluateThresholds(%.2f, %.2f, %.2f) = %v; expected %v",
				tc.score, tauLow, tauHigh, actual, tc.expected)
		}
	}
}

func TestModerationVerdictSerialization(t *testing.T) {
	verdict := ModerationVerdict{
		EventID:        "evt-1234",
		Text:           "Hello world",
		Status:         VerdictPassed,
		ResolvedByTier: Tier1Local,
		Confidence:     0.98,
		Reasoning:      "Below toxicity threshold",
		Tier1LatencyMs: 2.5,
		TotalLatencyMs: 2.5,
		ResolvedAt:     time.Now().UTC(),
	}

	data, err := json.Marshal(verdict)
	if err != nil {
		t.Fatalf("failed to marshal verdict: %v", err)
	}

	var parsed ModerationVerdict
	if err := json.Unmarshal(data, &parsed); err != nil {
		t.Fatalf("failed to unmarshal verdict: %v", err)
	}

	if parsed.EventID != verdict.EventID || parsed.Status != verdict.Status {
		t.Errorf("parsed verdict mismatch: got %+v, expected %+v", parsed, verdict)
	}
}
