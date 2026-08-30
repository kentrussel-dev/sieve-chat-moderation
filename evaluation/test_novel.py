import sys
import os
import joblib

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "python"))
model = joblib.load(os.path.join(os.path.dirname(__file__), "..", "python", "models", "tier1_model.joblib"))

categories = {
    "1. Clear Clean": [
        "Can someone review my PR on the Kubernetes ingress controller?",
        "I am organizing a study group on distributed consensus algorithms.",
        "Could you point me to the latest documentation for FastAPI websockets?",
        "The keynote speaker gave a very practical overview of vector databases.",
        "We reduced memory usage by 40% after profiling heap allocations.",
        "Looking forward to collaborating with everyone on the new release.",
        "Does anyone have experience deploying Kafka with Strimzi operator?",
        "Thank you for providing such thorough feedback on my architecture RFC.",
        "Let us schedule our weekly engineering demo for Thursday morning.",
        "I found a clean workaround for the race condition in the worker pool."
    ],
    "2. Blatant Toxic": [
        "You are a total piece of garbage, get off this forum forever.",
        "Nobody asked for your worthless input, shut your mouth.",
        "You are an utterly brainless fool and your code is disgusting trash.",
        "I hope your startup fails and you end up bankrupt you loser.",
        "Delete your repository and leave the tech industry for good, idiot.",
        "You are the most pathetic excuse for an engineer I have ever seen.",
        "Shut up and choke on your nonsense, you repulsive clown.",
        "Nobody respects you and everyone here talks behind your back.",
        "Get lost you arrogant scumbag, nobody wants you around.",
        "You are pure cancer to this developer community."
    ],
    "3. Nuanced Sarcasm": [
        "Oh brilliant deduction Sherlock, must have taken your last two brain cells.",
        "Thank you for courageously explaining the obvious in the most confusing way possible.",
        "Groundbreaking analysis, truly reshaping how humanity understands simple arithmetic.",
        "Your code is so revolutionary that even the compiler gave up trying to understand it.",
        "What an astounding accomplishment to be wrong about every single sentence in one post.",
        "Please write a book so I know exactly what opinions to avoid in life.",
        "I love how you talk with supreme authority on things you learned ten minutes ago.",
        "Truly inspirational how you never let facts get in the way of your grand theories.",
        "A round of applause for solving a problem that literally nobody had.",
        "It is almost artistic how consistently you miss the entire context."
    ],
    "4. Slang / Metaphors": [
        "That new album is absolute fire, they completely killed it on track 4!",
        "Our frontend team totally crushed that refactor before the deadline.",
        "That last boss fight was pure torture, but the victory felt incredible.",
        "Bro your presentation blew everyone away, you destroyed that stage!",
        "We need to terminate the rogue background jobs that are hogging CPU.",
        "I am dying over how funny that commit message was.",
        "Our latency numbers are drop-dead gorgeous after the Redis caching update.",
        "She executed that high-stakes live demo like an absolute assassin.",
        "The query optimizer just slaughtered the slow table join bottleneck.",
        "He has a killer instinct when it comes to finding security vulnerabilities."
    ],
    "5. Subtle Hostility": [
        "It must be exhausting pretending you actually understand this topic.",
        "We should not be surprised someone with your credentials struggled with this.",
        "I suppose that level of output is acceptable for someone in your position.",
        "Maybe leave the complex systems design to people who actually build them.",
        "It is quaint that you thought that argument was compelling.",
        "One can only hope you do not apply this level of rigor in your day job.",
        "You seem very invested in defending mistakes that everyone else recognized immediately.",
        "I admire your unwavering commitment to remaining completely uninformed.",
        "Perhaps spend less time lecturing others and more time reading basic documentation.",
        "We all know what kind of community produced this particular mindset."
    ]
}

print("\n" + "="*80)
print("NOVEL TEST SUITE (50 EXAMPLES - NOT IN TRAINING OR TEST SETS)")
print("="*80 + "\n")

for cat, samples in categories.items():
    print(f"### {cat} (10 Samples)")
    for idx, s in enumerate(samples, 1):
        p = float(model.predict_proba([s])[0][1])
        if p < 0.20:
            route = "Mesh 1 (Passed Clean locally <1ms)"
            tag = "PASSED (LOCAL)"
        elif p > 0.80:
            route = "Mesh 1 (Flagged Toxic locally <1ms)"
            tag = "FLAGGED (LOCAL)"
        else:
            route = "Mesh 2 (Escalated to LLM)"
            tag = "ESCALATED (LLM)"
        print(f"{idx:2d}. [Score: {p:.3f} -> {tag}] \"{s}\"")
    print()
