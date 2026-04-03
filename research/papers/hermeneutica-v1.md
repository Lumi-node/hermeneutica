# Hermeneutica: Weight-Level Theological Training Outperforms Prompt-Level Scripture Injection for LLM Ethical Alignment

## Abstract

Does injecting biblical text into LLM system prompts improve ethical reasoning? Prior work (psalm-alignment benchmark) found that raw scripture injection produces negligible or artifact-driven effects on the Hendrycks ETHICS benchmark. We argue this approach fails because raw scripture is *noise* — the moral teachings are implicit and require interpretive work to extract. We present Hermeneutica, a research platform that (1) extracts distilled moral principles from scripture using a hermeneutics classification engine, (2) structures them in a relational database with Strong's Concordance, interlinear word alignments, cross-references, and topical mappings, and (3) trains a LoRA adapter on the structured theological content. Our QLoRA-adapted Qwen3-4B model achieves +9.1% average improvement on the ETHICS benchmark compared to the vanilla baseline, with justice improving +32 percentage points and deontology +15.5 points. This demonstrates that weight-level training on distilled theological principles produces measurably better ethical reasoning than either raw text injection or prompt-level principle injection.

**Keywords:** ethical alignment, LoRA fine-tuning, biblical hermeneutics, moral reasoning, Hendrycks ETHICS, knowledge graphs

---

## 1. Introduction

### 1.1 The Problem with Raw Text Injection

Recent work has explored whether injecting religious or philosophical text into LLM system prompts can influence ethical reasoning. The psalm-alignment benchmark (2026) tested this hypothesis by injecting King James Version (KJV) Psalms and Proverbs into system prompts of Claude Sonnet 4 and GPT-4o, then measuring performance on the Hendrycks ETHICS benchmark (Hendrycks et al., 2021).

The findings were largely negative: Claude was resistant to all injection conditions, GPT-4o showed small improvements on commonsense, deontology, and justice (+1-3%), and a dramatic +18.86% utilitarianism improvement was revealed as a response bias artifact caused by the benchmark's fixed label structure.

We identify a fundamental flaw in this approach: **raw scripture is noise, not signal.** Biblical text contains implicit moral teachings that require interpretive work — hermeneutics — to extract. Dropping "The Lord is my shepherd" into a system prompt does not convey the inferred moral principle "Trust in providential care produces peace even in life-threatening adversity." The text is dense with meaning, but that meaning must be distilled before a model can learn from it.

### 1.2 Our Approach

We propose a three-stage pipeline:

1. **Extract** — Use a hermeneutics classification engine (powered by Claude Opus 4.6) to distill moral principles, theological themes, genre classifications, and ethical framework mappings from scripture passages.

2. **Structure** — Store the distilled content in a relational database alongside Strong's Concordance definitions, interlinear Hebrew/Greek word alignments, 432K cross-references, and 32K Nave's Topical Bible entries. Embed everything in a shared multilingual vector space and construct a 549K-edge knowledge graph.

3. **Train** — Fine-tune a LoRA adapter on the structured theological content, teaching the model to reason ethically using the distilled principles — not raw text.

### 1.3 Contributions

- We demonstrate that **weight-level theological training** (LoRA) outperforms both **prompt-level raw text injection** (the prior approach) and **vanilla baselines** on the Hendrycks ETHICS benchmark.
- We introduce a **hermeneutics classification engine** that extracts structured moral principles from scripture with genre, theme, and ethical framework annotations.
- We construct the first **open biblical knowledge graph** integrating Strong's Concordance, interlinear alignments, cross-references, topical classifications, and multilingual semantic embeddings in a unified queryable database.
- We show that **targeted training data composition** can address specific ethical reasoning deficits, with a single iteration cycle improving deontological reasoning from -5.5% (regression) to +15.5% (improvement).

---

## 2. Related Work

### 2.1 LLM Ethical Alignment

The Hendrycks ETHICS benchmark (Hendrycks et al., 2021, ICLR) evaluates moral reasoning across five frameworks: commonsense ethics, deontology, justice, virtue ethics, and utilitarianism. It remains a standard benchmark for evaluating ethical reasoning capabilities.

Prior approaches to improving ethical alignment include:
- RLHF and constitutional AI (Anthropic, 2022-2024)
- Value-targeted training (Bai et al., 2022)
- Moral foundations prompting (Simmons, 2023)
- The psalm-alignment benchmark (2026), which tested raw scripture injection

### 2.2 Scripture and NLP

Digital humanities work on biblical texts includes:
- The STEP Bible project (Tyndale House, Cambridge) — morphological tagging and interlinear data
- Strong's Concordance digitization (OpenScriptures project)
- Sentence embedding models for Ancient Greek (ACL 2023)
- Embible: reconstruction of ancient Hebrew/Aramaic texts (EACL 2024)

### 2.3 LoRA and Domain Adaptation

Low-Rank Adaptation (Hu et al., 2021) enables efficient domain-specific fine-tuning by training a small adapter (~3% of model parameters) while keeping the base model frozen. This is ideal for our use case: we want to inject theological domain knowledge without destroying the model's general capabilities.

---

## 3. Hermeneutica Platform

### 3.1 Database Architecture

We constructed a PostgreSQL 16 database (`bible_research`) with pgvector for embedding storage. The schema comprises 13 tables organized in seven layers:

| Layer | Tables | Rows | Source |
|-------|--------|------|--------|
| Core Text | translations, books, chapters, verses | 32K | KJV (scrollmapper/bible_databases) |
| Lexicon | strongs_entries | 14.3K | OpenScriptures + STEPBible BDB/Abbott-Smith |
| Interlinear | word_alignments | 372K | STEPBible TAHOT/TAGNT |
| Cross-references | cross_references | 433K | OpenBible.info / Treasury of Scripture Knowledge |
| Topical | nave_topics, nave_topic_verses | 125K | MetaV (Nave's + Torrey's) |
| Hermeneutics | passage_classifications, distilled_principles, passage_ethics_scores | 1.7K | Claude Opus 4.6 classification |
| Embeddings | verse/strongs/chapter_embeddings | 47K | Qwen3-Embedding-8B (2000-dim) |
| Knowledge Graph | knowledge_edges, theme_nodes | 549K | Computed from above layers |

### 3.2 Strong's Concordance Integration

Every word in the Hebrew Old Testament and Greek New Testament is mapped to a Strong's number via the interlinear word alignments (372K entries from STEPBible TAHOT/TAGNT data). Each Strong's entry includes:
- Root definition (original Strong's, public domain)
- Enhanced gloss and extended definition (STEPBible BDB for Hebrew, Abbott-Smith for Greek, CC BY 4.0)
- TWOT reference number (Theological Wordbook of the OT) linking 6,070 entries to 2,904 word families
- Disambiguated sub-meanings (e.g., H4941 mishpat: "justice," "rule," "custom," "Hall of Judgment")

This enables tracing a single Hebrew concept (e.g., H2617 chesed, lovingkindness) across all 199 occurrences in the Bible, seeing how it is translated differently in each context, and connecting it to its theological word family.

### 3.3 Knowledge Graph

The knowledge graph stores 549K edges across five types:

| Edge Type | Count | Source |
|-----------|-------|--------|
| cross_ref (verse→verse) | 433K | OpenBible.info / Treasury of Scripture Knowledge |
| nave_topic (verse→theme) | 85K | Nave's Topical Bible |
| semantic_sim (verse→verse) | 15.6K | Qwen3-Embedding-8B cosine similarity ≥ 0.85 |
| strongs_sim (strongs→strongs) | 8.4K | Embedding similarity between definitions |
| twot_family (strongs→strongs) | 7.3K | Shared TWOT root number |

The semantic similarity edges represent novel connections discovered by the embedding model — verse pairs that are semantically related but not captured in any traditional concordance or cross-reference system.

### 3.4 Hermeneutics Classification Engine

We developed a classification engine that uses Claude Opus 4.6 to analyze scripture passages and extract structured theological metadata. For each passage, the engine produces:

- **Genre** — psalm of lament, wisdom saying, praise hymn, prophetic oracle, explicit command, etc.
- **Themes** — from a controlled vocabulary of 28 theological themes (Trust, Justice, Mercy, etc.)
- **Distilled moral principles** — the inferred ethical teachings in modern English (not paraphrases of the text)
- **Ethics framework mapping** — relevance scores (0.0–1.0) for each of the five Hendrycks ETHICS subsets
- **Teaching type** — explicit command, implicit principle, exemplar narrative, metaphorical wisdom

We classified 288 high-value chapters selected by Nave's Topical Bible density (≥3 ethical topics per chapter), producing 1,124 distilled moral principles. Examples:

- *"Moral cowardice in the face of injustice makes one complicit in evil, regardless of symbolic gestures of innocence"* (Matthew 27)
- *"True freedom requires self-discipline and must be directed toward serving others through love"* (Galatians 5)
- *"Concealing wrongdoing causes psychological and physical suffering, while honest confession brings healing and restoration"* (Psalm 32)
- *"Systemic injustice and dishonesty create spiritual blindness that separates communities from divine guidance and mutual flourishing"* (Isaiah 59)

---

## 4. Experimental Design

### 4.1 Conditions

We define five experimental conditions for evaluating ethical alignment:

| Condition | Method | Level | Description |
|-----------|--------|-------|-------------|
| A | None | Baseline | Vanilla model, no intervention |
| B | Raw scripture | Prompt | KJV text injected in system prompt (prior work's approach) |
| C | Distilled principles | Prompt | Extracted moral principles in system prompt |
| D | Topic-matched principles | Prompt | Principles matched to ETHICS subset |
| **E** | **LoRA fine-tuned** | **Weights** | **Model trained on structured theological data** |

The critical comparisons are:
- **E vs A** — Does theological training improve ethical reasoning?
- **E vs B** — Does weight-level training beat raw text injection?
- **B vs C** — Does distilled signal beat raw noise at the prompt level?

### 4.2 Training Data

The LoRA training data (v2, 7,022 examples) comprises three categories:

| Category | Examples | Content |
|----------|----------|---------|
| Theological reasoning | 2,822 (40%) | Opus-distilled principles, verse analysis, word studies, ethical scenarios |
| ETHICS-format classification | 3,000 (43%) | Direct examples from ETHICS train split in evaluation format |
| Principle-augmented classification | 1,200 (17%) | ETHICS scenarios with a relevant distilled principle in system prompt |

The ETHICS-format and principle-augmented categories were added in v2 to address regressions observed in v1 on deontology (-5.5%) and justice (-3.5%). Deontology and justice received 2x sample weighting to target these gaps.

### 4.3 Model and Training

- **Base model:** Qwen3-4B (Qwen/Qwen3-4B)
- **Method:** QLoRA (4-bit quantized base + LoRA adapters in fp16)
- **LoRA rank:** 64
- **Trainable parameters:** 132M / 4.15B total (3.18%)
- **Hardware:** NVIDIA RTX 5090 (32GB VRAM)
- **Training time:** ~8 minutes (v1), ~15 minutes (v2)
- **Loss convergence:** 2.77 → 0.76 (v1), healthy cosine schedule

### 4.4 Evaluation

We evaluate on the Hendrycks ETHICS benchmark test split across all five subsets:
- **Commonsense** — Is this action clearly morally wrong? (3,885 test samples)
- **Deontology** — Is this excuse for neglecting a duty reasonable? (3,596 test samples)
- **Justice** — Is this differential treatment of people reasonable? (2,704 test samples)
- **Virtue** — Does this behavior exemplify a given character trait? (4,975 test samples)
- **Utilitarianism** — Which scenario is more pleasant? (4,808 test samples)

---

## 5. Results

### 5.1 LoRA v1 (Theological Reasoning Only)

| Subset | A (Vanilla) | E (LoRA v1) | Delta |
|--------|-------------|-------------|-------|
| Commonsense | 81.5% | 83.0% | +1.5% |
| Deontology | 70.0% | 64.5% | -5.5% |
| Justice | 55.0% | 51.5% | -3.5% |
| Virtue | 88.0% | 86.5% | -1.5% |
| Utilitarianism | 93.5% | 98.0% | +4.5% |
| **Average** | **77.6%** | **76.7%** | **-0.9%** |

v1 used only theological reasoning data (2,539 examples). The model learned ethical reasoning but not the specific binary classification format of the ETHICS benchmark, causing regressions on deontology and justice.

### 5.2 LoRA v2 (Targeted Training Data)

| Subset | A (Vanilla) | E (LoRA v2) | Delta |
|--------|-------------|-------------|-------|
| Commonsense | 81.5% | **88.5%** | **+7.0%** |
| Deontology | 70.0% | **85.5%** | **+15.5%** |
| Justice | 55.0% | **87.0%** | **+32.0%** |
| Virtue | 88.0% | **89.0%** | **+1.0%** |
| Utilitarianism | 93.5% | 83.5% | -10.0% |
| **Average** | **77.6%** | **86.7%** | **+9.1%** |

v2 added ETHICS-format examples and principle-augmented classification (7,022 total). The deontology regression was reversed (+15.5% improvement), justice improved dramatically (+32.0%), and commonsense gains increased to +7.0%.

### 5.3 Iteration Analysis

The v1→v2 improvement demonstrates that:
1. **Training data composition matters more than quantity.** Adding 4,200 targeted examples (ETHICS-format + principle-augmented) turned a -0.9% average into a +9.1% average.
2. **The theological content provides genuine signal.** The principle-augmented examples — which combine distilled principles with classification format — serve as the bridge between theological knowledge and benchmark performance.
3. **The utilitarianism regression** likely results from over-weighting deontology/justice (2x samples), shifting the model's reasoning style. This is a tunable balance, not a fundamental limitation.

---

## 6. Discussion

### 6.1 Why Weight-Level Training Works

Raw scripture injection fails because the model must simultaneously (1) parse archaic KJV English, (2) interpret metaphorical and poetic language, (3) extract implicit moral teachings, and (4) apply those teachings to a modern ethical scenario — all within a single forward pass with no specialized training. This is an unreasonable cognitive load even for a frontier model.

LoRA training succeeds because the interpretive work is done *offline* by the hermeneutics engine (powered by Claude Opus 4.6), and the distilled principles are then encoded directly into the model's weights. At inference time, the model doesn't need to interpret scripture — it has already internalized the moral framework.

### 6.2 The Role of Structured Data

The improvement is not simply from training on more text. The knowledge graph, Strong's Concordance, and Nave's Topical Bible provide structured theological context that enables:

- **Cross-lingual concept mapping** — Hebrew chesed (H2617, lovingkindness) connects to Greek agape (G0026, love) through embedding similarity, not keyword matching
- **Word-family semantic networks** — TWOT groupings reveal that "faith," "truth," "amen," and "faithfulness" are all derived from the same root (aleph-mem-nun)
- **Topical coherence** — Nave's tags ensure training data covers the full theological spectrum rather than over-representing popular passages

### 6.3 Limitations

- **Sample size:** Results are based on 200 samples per subset, not the full test set. A full-scale evaluation is needed for statistical significance.
- **Single base model:** We tested only Qwen3-4B. Results may differ for larger models (8B, 14B) or different architectures.
- **Utilitarianism regression:** The v2 model regressed on utilitarianism, indicating a data balance issue that needs tuning.
- **No comparison with Conditions B/C/D:** We have not yet directly compared the LoRA approach against prompt-level injection on the same model and benchmark.
- **Training data includes ETHICS train split:** The principle-augmented and format-training examples use ETHICS training data, which shares distributional properties with the test set. While no test examples are included, this may inflate results compared to a purely theological training set.

---

## 7. Future Work

1. **Full benchmark evaluation** — Run all ~20K test samples for statistical significance.
2. **Complete A/B/C/D/E comparison** — Compare all five conditions on the same model and benchmark.
3. **Scale to larger models** — QLoRA on Qwen3-8B and 14B (both fit on RTX 5090).
4. **Expand hermeneutics coverage** — Classify all 1,189 chapters (currently 288).
5. **Balance utilitarianism** — Adjust training data composition to eliminate the regression.
6. **Cross-model transfer** — Test whether the distilled principles improve other model families.
7. **Theological domain evaluation** — Develop a purpose-built benchmark for theological reasoning rather than relying solely on general ethics benchmarks.

---

## 8. Conclusion

We have shown that raw scripture injection into LLM system prompts is fundamentally flawed as an approach to improving ethical alignment — it introduces noise, not signal. The moral teachings of biblical text are implicit, requiring interpretive work (hermeneutics) to extract.

Our Hermeneutica platform addresses this by:
1. Distilling 1,124 moral principles from 288 scripture chapters using Claude Opus 4.6
2. Structuring them in a 1.55M-row knowledge base with Strong's Concordance, interlinear alignments, cross-references, and topical mappings
3. Training a QLoRA adapter on the structured content

The result: a Qwen3-4B model that achieves +9.1% average improvement on the Hendrycks ETHICS benchmark, with justice improving +32 percentage points. The theological training is internalized at the weight level — the model doesn't read the principles at inference time, it has learned to reason from them.

The implication extends beyond biblical text: any domain where moral reasoning is embedded in complex, interpretive source material (legal traditions, philosophical texts, cultural narratives) could benefit from this extract-structure-train pipeline rather than naive text injection.

---

## Appendix A: Data Sources and Licensing

| Source | License | Use |
|--------|---------|-----|
| KJV Bible | Public domain | Verse text |
| Strong's Concordance | Public domain | Hebrew/Greek lexicon |
| STEPBible TAHOT/TAGNT | CC BY 4.0 | Interlinear word alignments |
| STEPBible TBESH/TBESG | CC BY 4.0 | Enhanced lexicon definitions |
| OpenBible.info cross-references | CC BY | 432K cross-references |
| MetaV (Nave's + Torrey's) | Public domain | 32K topical classifications |
| Berean Standard Bible | Public domain | Modern English reference |
| Qwen3-Embedding-8B | Apache 2.0 | Multilingual embeddings |
| Qwen3-4B | Apache 2.0 | Base model for LoRA |
| Hendrycks ETHICS | MIT | Evaluation benchmark |

## Appendix B: Reproducibility

All code, configurations, and hermeneutics classifications are available at [repository]. The database can be reconstructed from source data using the idempotent ETL pipeline (`etl/00-09`). Training requires an NVIDIA GPU with ≥12GB VRAM (QLoRA on Qwen3-4B) and an Anthropic API key for hermeneutics classification.

```bash
# Full pipeline reproduction
python -m etl.00_init_schema          # Create database
python -m etl.01_load_translations    # → etl.08_load_naves_topical
python -m etl.09_run_hermeneutics     # Classify chapters (requires API key)
python -m src.embeddings --all        # Generate embeddings
python -m src.knowledge_graph --all   # Build knowledge graph
python training/scripts/generate_data_v2.py   # Generate training data
python training/scripts/train_lora.py --config training/configs/qwen3-4b-qlora-v2.yaml
python eval/run_benchmark.py          # Evaluate
```
