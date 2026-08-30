package main

import (
	"context"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"sort"
	"sync"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
	"github.com/sieve-moderation/sieve/pkg/llm"
	"github.com/sieve-moderation/sieve/pkg/model"
)

type MockClassifier struct {
	BaseLatency time.Duration
}

func (m *MockClassifier) Classify(ctx context.Context, req *model.ClassificationRequest) (*model.ClassificationResponse, error) {
	time.Sleep(m.BaseLatency)
	score := rand.Float64()
	return &model.ClassificationResponse{
		EventID:         req.EventID,
		IsToxic:         score > 0.5,
		ToxicityScore:   score,
		InferenceTimeMs: float64(m.BaseLatency.Microseconds()) / 1000.0,
		ModelVersion:    "distilbert-toxic-v1",
	}, nil
}

func main() {
	var (
		totalItems  = flag.Int("n", 1000, "Number of items to process")
		concurrency = flag.Int("c", 16, "Concurrency level")
		tauLow      = flag.Float64("tau-low", 0.20, "Lower confidence threshold")
		tauHigh     = flag.Float64("tau-high", 0.80, "Upper confidence threshold")
	)
	flag.Parse()

	fmt.Printf("Running Sieve Pipeline Benchmark: N=%d, Concurrency=%d, tau=[%.2f, %.2f]\n", *totalItems, *concurrency, *tauLow, *tauHigh)

	classifierClient := &MockClassifier{BaseLatency: 3 * time.Millisecond}
	llmClient := llm.NewDeterministicSimulator(200*time.Millisecond, 20*time.Millisecond)

	ctx := context.Background()
	var wg sync.WaitGroup

	latencies := make([]float64, 0, *totalItems)
	var latMu sync.Mutex

	var tier1Count uint64
	var tier2Count uint64
	var passedCount uint64
	var flaggedCount uint64

	itemChan := make(chan int, *totalItems)
	for i := 0; i < *totalItems; i++ {
		itemChan <- i
	}
	close(itemChan)

	startOverall := time.Now()

	for w := 0; w < *concurrency; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			localLatencies := make([]float64, 0, *totalItems / *concurrency + 10)

			for range itemChan {
				itemStart := time.Now()
				eventID := uuid.New().String()

				res, err := classifierClient.Classify(ctx, &model.ClassificationRequest{
					EventID: eventID,
					Text:    "Benchmark test message payload",
				})
				if err != nil {
					continue
				}

				decision := model.EvaluateThresholds(res.ToxicityScore, *tauLow, *tauHigh)

				if decision == model.RoutePassed {
					atomic.AddUint64(&tier1Count, 1)
					atomic.AddUint64(&passedCount, 1)
				} else if decision == model.RouteFlagged {
					atomic.AddUint64(&tier1Count, 1)
					atomic.AddUint64(&flaggedCount, 1)
				} else {
					// Escalation to Tier 2
					atomic.AddUint64(&tier2Count, 1)
					llmResp, err := llmClient.Moderate(ctx, &model.LLMModerationRequest{
						EventID: eventID,
						Text:    "Benchmark test message payload",
					})
					if err == nil {
						if llmResp.IsToxic {
							atomic.AddUint64(&flaggedCount, 1)
						} else {
							atomic.AddUint64(&passedCount, 1)
						}
					}
				}

				durMs := float64(time.Since(itemStart).Microseconds()) / 1000.0
				localLatencies = append(localLatencies, durMs)
			}

			latMu.Lock()
			latencies = append(latencies, localLatencies...)
			latMu.Unlock()
		}()
	}

	wg.Wait()
	totalElapsed := time.Since(startOverall)

	sort.Float64s(latencies)
	p50 := latencies[len(latencies)*50/100]
	p90 := latencies[len(latencies)*90/100]
	p95 := latencies[len(latencies)*95/100]
	p99 := latencies[len(latencies)*99/100]

	var sum float64
	for _, l := range latencies {
		sum += l
	}
	avg := sum / float64(len(latencies))

	escalationRate := (float64(tier2Count) / float64(*totalItems)) * 100.0
	throughput := float64(*totalItems) / totalElapsed.Seconds()

	fmt.Println("\n=== BENCHMARK RESULTS ===")
	fmt.Printf("Total Items:      %d\n", *totalItems)
	fmt.Printf("Elapsed Time:     %v\n", totalElapsed)
	fmt.Printf("Throughput:       %.2f items/sec\n", throughput)
	fmt.Printf("Tier 1 Resolved:  %d (%.1f%%)\n", tier1Count, (float64(tier1Count)/float64(*totalItems))*100.0)
	fmt.Printf("Tier 2 Escalated: %d (%.1f%%)\n", tier2Count, escalationRate)
	fmt.Printf("Passed:           %d\n", passedCount)
	fmt.Printf("Flagged:          %d\n", flaggedCount)
	fmt.Println("\nLatency Distribution (ms):")
	fmt.Printf("  Avg: %.2f ms\n", avg)
	fmt.Printf("  P50: %.2f ms\n", p50)
	fmt.Printf("  P90: %.2f ms\n", p90)
	fmt.Printf("  P95: %.2f ms\n", p95)
	fmt.Printf("  P99: %.2f ms\n", p99)

	_ = os.Stdout.Sync()
}
