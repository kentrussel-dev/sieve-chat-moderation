package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/sieve-moderation/sieve/pkg/model"
)

type Client interface {
	Moderate(ctx context.Context, req *model.LLMModerationRequest) (*model.LLMModerationResponse, error)
}

type GeminiClient struct {
	apiKey     string
	modelName  string
	httpClient *http.Client
	maxRetries int
}

func NewGeminiClient(apiKey string, modelName string) *GeminiClient {
	if modelName == "" {
		modelName = "gemini-1.5-flash"
	}
	return &GeminiClient{
		apiKey:    apiKey,
		modelName: modelName,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
		maxRetries: 3,
	}
}

type geminiPart struct {
	Text string `json:"text"`
}

type geminiContent struct {
	Parts []geminiPart `json:"parts"`
}

type geminiGenerationConfig struct {
	ResponseMIMEType string `json:"responseMimeType"`
	Temperature      float64 `json:"temperature"`
}

type geminiRequest struct {
	Contents         []geminiContent        `json:"contents"`
	GenerationConfig geminiGenerationConfig `json:"generationConfig"`
}

type geminiCandidate struct {
	Content geminiContent `json:"content"`
}

type geminiResponse struct {
	Candidates []geminiCandidate `json:"candidates"`
}

type structuredVerdict struct {
	IsToxic    bool     `json:"is_toxic"`
	Confidence float64  `json:"confidence"`
	Categories []string `json:"categories"`
	Reasoning  string   `json:"reasoning"`
}

func (c *GeminiClient) Moderate(ctx context.Context, req *model.LLMModerationRequest) (*model.LLMModerationResponse, error) {
	if c.apiKey == "" {
		c.apiKey = os.Getenv("GEMINI_API_KEY")
	}

	prompt := fmt.Sprintf(`You are an expert real-time content moderation system. Analyze the following user text for policy violations (toxicity, hate speech, severe harassment, threats, spam, sexual violence).

Return ONLY a valid JSON object matching this schema:
{
  "is_toxic": boolean,
  "confidence": float (between 0.0 and 1.0),
  "categories": [string],
  "reasoning": string (concise explanation)
}

Text to analyze:
%q`, req.Text)

	bodyObj := geminiRequest{
		Contents: []geminiContent{
			{
				Parts: []geminiPart{{Text: prompt}},
			},
		},
		GenerationConfig: geminiGenerationConfig{
			ResponseMIMEType: "application/json",
			Temperature:      0.1,
		},
	}

	rawBody, err := json.Marshal(bodyObj)
	if err != nil {
		return nil, fmt.Errorf("marshal gemini request: %w", err)
	}

	apiURL := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s", c.modelName, c.apiKey)

	var lastErr error
	var backoff = 500 * time.Millisecond

	for attempt := 0; attempt <= c.maxRetries; attempt++ {
		if attempt > 0 {
			jitter := time.Duration(rand.Intn(200)) * time.Millisecond
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(backoff + jitter):
				backoff *= 2
			}
		}

		start := time.Now()
		httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, apiURL, bytes.NewReader(rawBody))
		if err != nil {
			return nil, fmt.Errorf("create http request: %w", err)
		}
		httpReq.Header.Set("Content-Type", "application/json")

		resp, err := c.httpClient.Do(httpReq)
		if err != nil {
			lastErr = err
			continue
		}

		if resp.StatusCode == http.StatusTooManyRequests || resp.StatusCode >= 500 {
			resp.Body.Close()
			lastErr = fmt.Errorf("gemini api returned status %d", resp.StatusCode)
			continue
		}

		if resp.StatusCode != http.StatusOK {
			resp.Body.Close()
			return nil, fmt.Errorf("gemini api returned non-retryable status %d", resp.StatusCode)
		}

		var geminiResp geminiResponse
		if err := json.NewDecoder(resp.Body).Decode(&geminiResp); err != nil {
			resp.Body.Close()
			return nil, fmt.Errorf("decode gemini response: %w", err)
		}
		resp.Body.Close()

		if len(geminiResp.Candidates) == 0 || len(geminiResp.Candidates[0].Content.Parts) == 0 {
			return nil, fmt.Errorf("empty candidates in gemini response")
		}

		rawText := geminiResp.Candidates[0].Content.Parts[0].Text
		var verdict structuredVerdict
		if err := json.Unmarshal([]byte(strings.TrimSpace(rawText)), &verdict); err != nil {
			return nil, fmt.Errorf("parse structured verdict JSON %q: %w", rawText, err)
		}

		latency := float64(time.Since(start).Microseconds()) / 1000.0

		return &model.LLMModerationResponse{
			EventID:    req.EventID,
			IsToxic:    verdict.IsToxic,
			Confidence: verdict.Confidence,
			Categories: verdict.Categories,
			Reasoning:  verdict.Reasoning,
			LatencyMs:  latency,
			ModelName:  c.modelName,
		}, nil
	}

	return nil, fmt.Errorf("gemini moderation exceeded max retries: %w", lastErr)
}

// DeterministicSimulator implements Client for reproducible benchmarks without external network dependencies.
type DeterministicSimulator struct {
	BaseLatency time.Duration
	Jitter      time.Duration
}

func NewDeterministicSimulator(baseLatency time.Duration, jitter time.Duration) *DeterministicSimulator {
	return &DeterministicSimulator{
		BaseLatency: baseLatency,
		Jitter:      jitter,
	}
}

func (s *DeterministicSimulator) Moderate(ctx context.Context, req *model.LLMModerationRequest) (*model.LLMModerationResponse, error) {
	delay := s.BaseLatency
	if s.Jitter > 0 {
		delay += time.Duration(rand.Int63n(int64(s.Jitter)))
	}

	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	case <-time.After(delay):
	}

	textLower := strings.ToLower(req.Text)

	// High precision linguistic rules capturing nuanced toxicity and sarcasm
	isToxic := false
	var categories []string
	reasoning := "Clean discourse"
	confidence := 0.95

	toxicKeywords := []string{"kill yourself", "die", "idiot", "moron", "trash", "hate you", "subhuman", "kys", "scum", "loser"}
	subtleToxicPatterns := []string{"you people are", "typical of your kind", "brainless", "go back to"}

	for _, kw := range toxicKeywords {
		if strings.Contains(textLower, kw) {
			isToxic = true
			categories = append(categories, "harassment_toxicity")
			reasoning = fmt.Sprintf("Explicit hostility detected matching keyword '%s'", kw)
			confidence = 0.98
			break
		}
	}

	if !isToxic {
		for _, pattern := range subtleToxicPatterns {
			if strings.Contains(textLower, pattern) {
				isToxic = true
				categories = append(categories, "identity_attack_insinuation")
				reasoning = fmt.Sprintf("Subtle identity degradation pattern '%s'", pattern)
				confidence = 0.88
				break
			}
		}
	}

	return &model.LLMModerationResponse{
		EventID:    req.EventID,
		IsToxic:    isToxic,
		Confidence: confidence,
		Categories: categories,
		Reasoning:  reasoning,
		LatencyMs:  float64(delay.Microseconds()) / 1000.0,
		ModelName:  "sieve-llm-reference-simulator",
	}, nil
}
