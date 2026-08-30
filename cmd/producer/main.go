package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/google/uuid"
	"github.com/sieve-moderation/sieve/pkg/kafka"
	"github.com/sieve-moderation/sieve/pkg/model"
)

var samplePhrases = []struct {
	text string
	tag  string
}{
	{"Good morning! Have a great day everyone.", "clean"},
	{"Thank you so much for explaining this clearly.", "clean"},
	{"I think we should reconsider the proposal based on recent metrics.", "clean"},
	{"Can someone help me with this Python syntax error?", "clean"},
	{"The match yesterday was really intense, great sportsmanship.", "clean"},
	{"I respectfully disagree with your conclusion here.", "clean"},
	{"This tutorial was super helpful, thanks!", "clean"},
	{"Where can I find the official documentation for this API?", "clean"},
	{"You are an absolute idiot and should never post here again.", "toxic_blatant"},
	{"Shut up you moron, nobody asked for your opinion.", "toxic_blatant"},
	{"Kill yourself you worthless scum.", "toxic_blatant"},
	{"Go back to where you came from, your kind is ruining this platform.", "toxic_blatant"},
	{"You're completely brainless.", "toxic_blatant"},
	{"Oh brilliant idea, let's just delete the database. Genius move.", "ambiguous_sarcasm"},
	{"Yeah right, you are sooo smart. Everyone is amazed.", "ambiguous_sarcasm"},
	{"I'm going to kill this exam tomorrow!", "ambiguous_false_alarm"},
	{"This bug is cancer to deal with.", "ambiguous_colloquial"},
	{"You people always act like you know everything.", "ambiguous_borderline"},
	{"Why do people like you even try?", "ambiguous_borderline"},
	{"Don't be ridiculous.", "borderline_mild"},
}

func main() {
	var (
		brokers       = flag.String("brokers", getEnv("KAFKA_BROKERS", "localhost:9092"), "Kafka broker addresses")
		topic         = flag.String("topic", getEnv("TOPIC_RAW", "content.raw"), "Kafka raw content topic")
		ratePerSec    = flag.Int("rate", 50, "Target messages per second in steady state")
		burstSize     = flag.Int("burst-size", 100, "Number of messages to inject during a burst")
		burstInterval = flag.Duration("burst-interval", 15*time.Second, "Interval between traffic bursts")
		totalMsgs     = flag.Int("total", 0, "Total messages to emit (0 for continuous)")
	)
	flag.Parse()

	log.Printf("Starting Sieve Producer: target topic=%s, rate=%d msg/s, brokers=%s", *topic, *ratePerSec, *brokers)

	producer := kafka.NewProducer(kafka.ProducerConfig{
		Brokers:      []string{*brokers},
		Topic:        *topic,
		BatchSize:    50,
		BatchTimeout: 10 * time.Millisecond,
	})
	defer producer.Close()

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()

	ticker := time.NewTicker(time.Second / time.Duration(*ratePerSec))
	defer ticker.Stop()

	var burstTicker *time.Ticker
	if *burstSize > 0 && *burstInterval > 0 {
		burstTicker = time.NewTicker(*burstInterval)
		defer burstTicker.Stop()
	}

	emitted := 0

	for {
		select {
		case <-ctx.Done():
			log.Printf("Producer shutting down after %d messages.", emitted)
			return

		case <-burstTicker.C:
			log.Printf("Injecting traffic burst of %d messages...", *burstSize)
			for i := 0; i < *burstSize; i++ {
				emitSample(ctx, producer, &emitted)
				if *totalMsgs > 0 && emitted >= *totalMsgs {
					log.Printf("Completed total quota of %d messages.", *totalMsgs)
					return
				}
			}

		case <-ticker.C:
			emitSample(ctx, producer, &emitted)
			if *totalMsgs > 0 && emitted >= *totalMsgs {
				log.Printf("Completed total quota of %d messages.", *totalMsgs)
				return
			}
		}
	}
}

func emitSample(ctx context.Context, producer *kafka.Producer, counter *int) {
	idx := rand.Intn(len(samplePhrases))
	sample := samplePhrases[idx]

	event := model.ContentEvent{
		ID:        uuid.New().String(),
		SourceID:  fmt.Sprintf("user-%04d", rand.Intn(1000)),
		Text:      sample.text,
		CreatedAt: time.Now().UTC(),
		Metadata: map[string]string{
			"synthetic_label": sample.tag,
		},
	}

	if err := producer.PublishJSON(ctx, event.ID, event); err != nil {
		log.Printf("Failed to publish event %s: %v", event.ID, err)
		return
	}

	*counter++
	if *counter%500 == 0 {
		log.Printf("Emitted %d events to raw queue.", *counter)
	}
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}
