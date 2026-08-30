package main

import (
	"context"
	"encoding/json"
	"flag"
	"log"
	"os"
	"os/signal"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/sieve-moderation/sieve/pkg/kafka"
	"github.com/sieve-moderation/sieve/pkg/llm"
	"github.com/sieve-moderation/sieve/pkg/model"
)

type Tier2Handler struct {
	llmClient       llm.Client
	passedProducer  *kafka.Producer
	flaggedProducer *kafka.Producer

	countProcessed uint64
	countPassed    uint64
	countFlagged   uint64
}

func main() {
	var (
		brokers       = flag.String("brokers", getEnv("KAFKA_BROKERS", "localhost:9092"), "Kafka broker addresses")
		escalateTopic = flag.String("escalate-topic", getEnv("TOPIC_ESCALATED", "content.escalated"), "Kafka escalation topic")
		passedTopic   = flag.String("passed-topic", getEnv("TOPIC_PASSED", "content.passed"), "Kafka passed topic")
		flaggedTopic  = flag.String("flagged-topic", getEnv("TOPIC_FLAGGED", "content.flagged"), "Kafka flagged topic")
		llmProvider   = flag.String("provider", getEnv("LLM_PROVIDER", "gemini"), "LLM provider (gemini, simulator)")
		geminiKey     = flag.String("gemini-key", getEnv("GEMINI_API_KEY", ""), "Gemini API key")
		geminiModel   = flag.String("gemini-model", getEnv("GEMINI_MODEL", "gemini-1.5-flash"), "Gemini model name")
		concurrency   = flag.Int("concurrency", 4, "Number of concurrent LLM workers")
	)
	flag.Parse()

	log.Printf("Starting Sieve Tier 2 Consumer: provider=%s, topic=%s", *llmProvider, *escalateTopic)

	var llmClient llm.Client
	if *llmProvider == "gemini" && *geminiKey != "" {
		log.Printf("Initializing Gemini client (model=%s)", *geminiModel)
		llmClient = llm.NewGeminiClient(*geminiKey, *geminiModel)
	} else {
		log.Println("Using deterministic reference LLM simulator (no external API key provided)")
		llmClient = llm.NewDeterministicSimulator(250*time.Millisecond, 50*time.Millisecond)
	}

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

	handler := &Tier2Handler{
		llmClient:       llmClient,
		passedProducer:  passedProd,
		flaggedProducer: flaggedProd,
	}

	consumer := kafka.NewConsumer(kafka.ConsumerConfig{
		Brokers: []string{*brokers},
		Topic:   *escalateTopic,
		GroupID: "sieve-tier2-group",
	})
	defer consumer.Close()

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	go handler.reportTelemetry(ctx, 5*time.Second)

	var wg sync.WaitGroup
	msgChan := make(chan []byte, *concurrency*2)

	for i := 0; i < *concurrency; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for rawMsg := range msgChan {
				handler.processEscalation(ctx, rawMsg)
			}
		}(i)
	}

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
					log.Printf("Error reading escalation message: %v", err)
					time.Sleep(100 * time.Millisecond)
					continue
				}
				msgChan <- msg.Value
			}
		}
	}()

	<-ctx.Done()
	log.Println("Tier 2 consumer stopping...")
	wg.Wait()
	log.Println("Tier 2 consumer shutdown complete.")
}

func (h *Tier2Handler) processEscalation(ctx context.Context, data []byte) {
	var payload model.EscalationPayload
	if err := json.Unmarshal(data, &payload); err != nil {
		log.Printf("Failed to unmarshal escalation payload: %v", err)
		return
	}

	start := time.Now()
	resp, err := h.llmClient.Moderate(ctx, &model.LLMModerationRequest{
		EventID: payload.Event.ID,
		Text:    payload.Event.Text,
	})
	if err != nil {
		log.Printf("LLM escalation failed for %s: %v", payload.Event.ID, err)
		return
	}

	tier2Latency := float64(time.Since(start).Microseconds()) / 1000.0
	totalLatency := payload.Tier1LatencyMs + tier2Latency

	atomic.AddUint64(&h.countProcessed, 1)

	status := model.VerdictPassed
	if resp.IsToxic {
		status = model.VerdictFlagged
		atomic.AddUint64(&h.countFlagged, 1)
	} else {
		atomic.AddUint64(&h.countPassed, 1)
	}

	verdict := model.ModerationVerdict{
		EventID:        payload.Event.ID,
		Text:           payload.Event.Text,
		Status:         status,
		ResolvedByTier: model.Tier2LLM,
		Confidence:     resp.Confidence,
		Reasoning:      resp.Reasoning,
		Categories:     resp.Categories,
		Tier1LatencyMs: payload.Tier1LatencyMs,
		Tier2LatencyMs: tier2Latency,
		TotalLatencyMs: totalLatency,
		ResolvedAt:     time.Now().UTC(),
	}

	if status == model.VerdictPassed {
		if err := h.passedProducer.PublishJSON(ctx, payload.Event.ID, verdict); err != nil {
			log.Printf("Failed to publish tier2 passed verdict: %v", err)
		}
	} else {
		if err := h.flaggedProducer.PublishJSON(ctx, payload.Event.ID, verdict); err != nil {
			log.Printf("Failed to publish tier2 flagged verdict: %v", err)
		}
	}
}

func (h *Tier2Handler) reportTelemetry(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			proc := atomic.LoadUint64(&h.countProcessed)
			if proc == 0 {
				continue
			}
			passed := atomic.LoadUint64(&h.countPassed)
			flagged := atomic.LoadUint64(&h.countFlagged)

			log.Printf("[Telemetry Tier 2] Escalations Handled: %d | Passed: %d | Flagged: %d", proc, passed, flagged)
		}
	}
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}
