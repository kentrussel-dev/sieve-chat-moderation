package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strconv"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/sieve-moderation/sieve/pkg/classifier"
	"github.com/sieve-moderation/sieve/pkg/kafka"
	"github.com/sieve-moderation/sieve/pkg/model"
)

type Tier1Router struct {
	classifierClient classifier.Client
	passedProducer   *kafka.Producer
	flaggedProducer  *kafka.Producer
	escalateProducer *kafka.Producer
	tauLow           float64
	tauHigh          float64

	countProcessed uint64
	countPassed    uint64
	countFlagged   uint64
	countEscalated uint64
}

func main() {
	var (
		brokers       = flag.String("brokers", getEnv("KAFKA_BROKERS", "localhost:9092"), "Kafka broker addresses")
		rawTopic      = flag.String("raw-topic", getEnv("TOPIC_RAW", "content.raw"), "Kafka raw content topic")
		passedTopic   = flag.String("passed-topic", getEnv("TOPIC_PASSED", "content.passed"), "Kafka passed topic")
		flaggedTopic  = flag.String("flagged-topic", getEnv("TOPIC_FLAGGED", "content.flagged"), "Kafka flagged topic")
		escalateTopic = flag.String("escalate-topic", getEnv("TOPIC_ESCALATED", "content.escalated"), "Kafka escalation topic")
		classifierURL = flag.String("classifier-url", getEnv("CLASSIFIER_URL", "http://localhost:8000"), "Tier 1 classifier base URL")
		tauLow        = flag.Float64("tau-low", getEnvFloat("TAU_LOW", 0.20), "Lower confidence threshold (below is passed)")
		tauHigh       = flag.Float64("tau-high", getEnvFloat("TAU_HIGH", 0.80), "Upper confidence threshold (above is flagged)")
		concurrency   = flag.Int("concurrency", 8, "Number of concurrent processing workers")
	)
	flag.Parse()

	log.Printf("Starting Sieve Tier 1 Consumer: tau_low=%.2f, tau_high=%.2f, classifier=%s", *tauLow, *tauHigh, *classifierURL)

	classifierCli := classifier.NewHTTPClient(*classifierURL, 200*time.Millisecond)

	passedProd := kafka.NewProducer(kafka.ProducerConfig{
		Brokers: []string{*brokers},
		Topic:   *passedTopic,
	})
	defer passedProd.Close()

	flaggedProd := kafka.NewProducer(kafka.ProducerConfig{
		Brokers: []string{*brokers},
		Topic:   *flaggedTopic,
	})
	defer flaggedProd.Close()

	escalateProd := kafka.NewProducer(kafka.ProducerConfig{
		Brokers: []string{*brokers},
		Topic:   *escalateTopic,
	})
	defer escalateProd.Close()

	router := &Tier1Router{
		classifierClient: classifierCli,
		passedProducer:   passedProd,
		flaggedProducer:  flaggedProd,
		escalateProducer: escalateProd,
		tauLow:           *tauLow,
		tauHigh:          *tauHigh,
	}

	consumer := kafka.NewConsumer(kafka.ConsumerConfig{
		Brokers: []string{*brokers},
		Topic:   *rawTopic,
		GroupID: "sieve-tier1-group",
	})
	defer consumer.Close()

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	// Periodic telemetry reporting
	go router.reportTelemetry(ctx, 5*time.Second)

	var wg sync.WaitGroup
	msgChan := make(chan []byte, *concurrency*4)

	// Worker pool
	for i := 0; i < *concurrency; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for rawMsg := range msgChan {
				router.routeItem(ctx, rawMsg)
			}
		}(i)
	}

	// Ingestion loop
	go func() {
		defer close(msgChan)
		for {
			select {
			case <-ctx.Done():
				return
			default:
				msg, err := consumer.ReadMessage(ctx)
				if err != nil {
					if ctx.Err() != nil {
						return
					}
					log.Printf("Error reading raw message: %v", err)
					time.Sleep(100 * time.Millisecond)
					continue
				}
				msgChan <- msg.Value
			}
		}
	}()

	<-ctx.Done()
	log.Println("Tier 1 consumer stopping...")
	wg.Wait()
	log.Println("Tier 1 consumer shutdown complete.")
}

func (r *Tier1Router) routeItem(ctx context.Context, data []byte) {
	var event model.ContentEvent
	if err := json.Unmarshal(data, &event); err != nil {
		log.Printf("Failed to unmarshal content event: %v", err)
		return
	}

	start := time.Now()
	res, err := r.classifierClient.Classify(ctx, &model.ClassificationRequest{
		EventID: event.ID,
		Text:    event.Text,
	})
	if err != nil {
		// On Tier 1 service failure, escalate conservatively rather than dropping
		log.Printf("Classifier failure for %s, escalating: %v", event.ID, err)
		r.publishEscalation(ctx, event, 0.5, float64(time.Since(start).Milliseconds()), "tier1_inference_error")
		return
	}

	decision := model.EvaluateThresholds(res.ToxicityScore, r.tauLow, r.tauHigh)
	latency := float64(time.Since(start).Microseconds()) / 1000.0

	atomic.AddUint64(&r.countProcessed, 1)

	switch decision {
	case model.RoutePassed:
		atomic.AddUint64(&r.countPassed, 1)
		verdict := model.ModerationVerdict{
			EventID:        event.ID,
			Text:           event.Text,
			Status:         model.VerdictPassed,
			ResolvedByTier: model.Tier1Local,
			Confidence:     1.0 - res.ToxicityScore,
			Reasoning:      fmt.Sprintf("Score %.3f below low threshold %.2f", res.ToxicityScore, r.tauLow),
			Tier1LatencyMs: latency,
			TotalLatencyMs: latency,
			ResolvedAt:     time.Now().UTC(),
		}
		if err := r.passedProducer.PublishJSON(ctx, event.ID, verdict); err != nil {
			log.Printf("Failed to publish passed verdict: %v", err)
		}

	case model.RouteFlagged:
		atomic.AddUint64(&r.countFlagged, 1)
		var cats []string
		for cat := range res.Categories {
			cats = append(cats, cat)
		}
		verdict := model.ModerationVerdict{
			EventID:        event.ID,
			Text:           event.Text,
			Status:         model.VerdictFlagged,
			ResolvedByTier: model.Tier1Local,
			Confidence:     res.ToxicityScore,
			Reasoning:      fmt.Sprintf("Score %.3f exceeded high threshold %.2f", res.ToxicityScore, r.tauHigh),
			Categories:     cats,
			Tier1LatencyMs: latency,
			TotalLatencyMs: latency,
			ResolvedAt:     time.Now().UTC(),
		}
		if err := r.flaggedProducer.PublishJSON(ctx, event.ID, verdict); err != nil {
			log.Printf("Failed to publish flagged verdict: %v", err)
		}

	case model.RouteEscalated:
		atomic.AddUint64(&r.countEscalated, 1)
		r.publishEscalation(ctx, event, res.ToxicityScore, latency,
			fmt.Sprintf("Score %.3f within uncertainty band [%.2f, %.2f]", res.ToxicityScore, r.tauLow, r.tauHigh))
	}
}

func (r *Tier1Router) publishEscalation(ctx context.Context, event model.ContentEvent, score float64, latency float64, reason string) {
	payload := model.EscalationPayload{
		Event:            event,
		Tier1Score:       score,
		Tier1LatencyMs:   latency,
		EscalationReason: reason,
		EscalatedAt:      time.Now().UTC(),
	}
	if err := r.escalateProducer.PublishJSON(ctx, event.ID, payload); err != nil {
		log.Printf("Failed to publish escalation payload: %v", err)
	}
}

func (r *Tier1Router) reportTelemetry(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			proc := atomic.LoadUint64(&r.countProcessed)
			if proc == 0 {
				continue
			}
			passed := atomic.LoadUint64(&r.countPassed)
			flagged := atomic.LoadUint64(&r.countFlagged)
			escalated := atomic.LoadUint64(&r.countEscalated)
			escRate := (float64(escalated) / float64(proc)) * 100.0

			log.Printf("[Telemetry Tier 1] Processed: %d | Passed: %d (%.1f%%) | Flagged: %d (%.1f%%) | Escalated: %d (%.1f%%)",
				proc, passed, (float64(passed)/float64(proc))*100.0, flagged, (float64(flagged)/float64(proc))*100.0, escalated, escRate)
		}
	}
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}

func getEnvFloat(key string, fallback float64) float64 {
	if val := os.Getenv(key); val != "" {
		if f, err := strconv.ParseFloat(val, 64); err == nil {
			return f
		}
	}
	return fallback
}
