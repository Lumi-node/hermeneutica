# Research

Papers, notes, methodology documentation, and figures for the Hermeneutica project.

## Structure

```
research/
├── papers/           # Formal writeups and draft publications
│   └── hermeneutica-v1.md    # Main paper draft
├── notes/            # Working notes, observations, ideas
│   ├── methodology.md        # How the pipeline works end-to-end
│   ├── related-work.md       # Literature review
│   └── observations.md       # Interesting findings during development
├── figures/          # Charts, diagrams, visualizations
│   ├── architecture.png      # System architecture diagram
│   ├── knowledge-graph.png   # Graph visualization
│   └── results-comparison.png
└── README.md
```

## Core Thesis

Raw scripture injection into LLM system prompts is noise, not signal. Biblical text
contains implicit moral teachings that require interpretive work (hermeneutics) to
extract. The correct approach is:

1. **Extract** structured theological meaning (hermeneutics engine)
2. **Embed** it in a shared semantic space (Qwen3 multilingual embeddings)
3. **Connect** it through a knowledge graph (Strong's + cross-refs + Nave's + similarity)
4. **Train** on the structured meaning at the weight level (LoRA)
5. **Evaluate** against the same benchmark as prompt-injection approaches (Hendrycks ETHICS)

If LoRA fine-tuning on distilled theological principles outperforms raw text injection,
that demonstrates the model has *internalized* the ethical framework — not just read it.
