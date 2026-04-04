# About Hermeneutica

Hermeneutica is a research project studying how biblical moral teachings can be computationally extracted, structured, and explored. The name comes from **hermeneutics** — the art and science of interpretation.

## Research Goals

1. **Extract** moral principles from scripture using AI classification (genre, themes, ethics dimensions)
2. **Structure** those principles in a knowledge graph connecting verses, themes, and words
3. **Embed** the entire Bible in semantic space to reveal meaning-level structure
4. **Train** language models on distilled biblical ethics (LoRA fine-tuning)
5. **Evaluate** whether biblical training improves LLM ethical alignment

## The Experiment

The core research question: *Does training a language model on structured biblical moral teachings improve its ethical reasoning?*

### Methodology

1. Classify ~1,200 Bible chapters by genre, themes, teaching type, and ethics relevance
2. Distill actionable moral principles from each chapter
3. Generate training data pairing ethical scenarios with biblically-grounded responses
4. Fine-tune Qwen3-4B via QLoRA on this data
5. Evaluate on the Hendrycks ETHICS benchmark (5 dimensions)
6. Evaluate on a custom "Fruits of the Spirit" alignment benchmark

### Results So Far

- LoRA v3: +9.1% average improvement on ETHICS benchmark over base model
- Balanced training across all 5 ethics dimensions eliminates utilitarianism regression
- Custom Fruits of the Spirit benchmark shows +0.67 average improvement (with self-judge caveat)

## Why a 3D Explorer?

The explorer exists because the database we built for this research is genuinely interesting to navigate. 549,000 edges connecting 31,000 verses reveal the Bible's internal structure in a way that reading linearly never could.

The cross-reference threads — 55,000 golden arcs from OT promises to NT fulfillment — are the most visually compelling expression of what the data contains.

## Contact

Made by [Automate Capture, LLC](https://www.automate-capture.com)

- LinkedIn: [Andrew Young](https://www.linkedin.com/in/andrew-young-executive)
- GitHub: [Lumi-node/hermeneutica](https://github.com/Lumi-node/hermeneutica)
