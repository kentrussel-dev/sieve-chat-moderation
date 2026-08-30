package classifier

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/sieve-moderation/sieve/pkg/model"
)

type Client interface {
	Classify(ctx context.Context, req *model.ClassificationRequest) (*model.ClassificationResponse, error)
}

type HTTPClient struct {
	baseURL    string
	httpClient *http.Client
}

func NewHTTPClient(baseURL string, timeout time.Duration) *HTTPClient {
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 100,
		IdleConnTimeout:     90 * time.Second,
	}

	return &HTTPClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
	}
}

func (c *HTTPClient) Classify(ctx context.Context, req *model.ClassificationRequest) (*model.ClassificationResponse, error) {
	payload, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal classification request: %w", err)
	}

	url := fmt.Sprintf("%s/v1/classify", c.baseURL)
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		return nil, fmt.Errorf("create http request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	start := time.Now()
	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("execute classification request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("classifier returned status %d", resp.StatusCode)
	}

	var res model.ClassificationResponse
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return nil, fmt.Errorf("decode classification response: %w", err)
	}

	if res.InferenceTimeMs == 0 {
		res.InferenceTimeMs = float64(time.Since(start).Microseconds()) / 1000.0
	}

	return &res, nil
}
