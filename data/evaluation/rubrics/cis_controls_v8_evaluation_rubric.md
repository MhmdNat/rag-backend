# CIS Controls v8 — RAG Evaluation Rubric

## Scoring Dimensions

### 1. Faithfulness (0–4)
Does the answer contain only information supported by the source document?

| Score | Criterion |
|-------|-----------|
| 4 | All claims are directly supported; no hallucinations |
| 3 | Minor extrapolation acceptable in context; no factual errors |
| 2 | One unsupported claim or slight misquotation |
| 1 | Multiple unsupported claims or material factual error |
| 0 | Answer is primarily fabricated or contradicts the document |

**High-risk questions (Q003, Q004, Q005, Q007, Q013, Q041, Q043):** Watch for the model substituting general security knowledge for document-specific thresholds.

---

### 2. Answer Relevance (0–4)
Does the answer address what was asked?

| Score | Criterion |
|-------|-----------|
| 4 | Directly answers the question; no irrelevant content |
| 3 | Answers the question with minor tangential content |
| 2 | Partially answers; missing key components |
| 1 | Addresses a related but different question |
| 0 | Does not answer the question |

---

### 3. Context Recall (0–4)
Did the retriever surface the correct chunks?

| Score | Criterion |
|-------|-----------|
| 4 | All relevant chunks retrieved; no important chunks missing |
| 3 | Most relevant chunks retrieved; one minor gap |
| 2 | Key chunk retrieved but supporting context missing |
| 1 | Only tangentially related chunks retrieved |
| 0 | No relevant chunks retrieved |

**Multi-hop questions (Q029–Q033, Q048):** Require chunks from multiple sections; score 4 only if all referenced sections appear in context.

---

### 4. Context Precision (0–4)
Are retrieved chunks relevant, or does the context include too much noise?

| Score | Criterion |
|-------|-----------|
| 4 | All retrieved chunks are relevant to the answer |
| 3 | One irrelevant chunk included but doesn't distort answer |
| 2 | Noisy retrieval but answer still correct |
| 1 | Most retrieved chunks are off-topic |
| 0 | Retrieved context is entirely irrelevant |

---

## Question Category Weights

For overall RAG system scoring, weight by question type:

| Type | Count | Weight per Q | Notes |
|------|-------|-------------|-------|
| Factual | 20 | 1.0× | Baseline |
| Definition | 5 | 1.0× | Glossary retrieval |
| List | 5 | 1.2× | Completeness matters |
| Comparison | 5 | 1.5× | Multi-chunk synthesis |
| Multi-hop | 7 | 2.0× | Cross-section reasoning |
| Procedural | 4 | 1.5× | Order and completeness |
| Negative | 5 | 1.5× | Hallucination resistance |

---

## Failure Mode Taxonomy

| Code | Description | Example Questions |
|------|-------------|-------------------|
| F1 | **Threshold substitution** — uses common security values instead of document-specific ones | Q003, Q004, Q007, Q013 |
| F2 | **IG over-generalization** — applies IG3 requirements to all IGs | Q021, Q022, Q032, Q038 |
| F3 | **Scope inflation** — claims document covers topics it defers to companion guides | Q039 |
| F4 | **Terminology drift** — uses old terms (Sub-Controls) or confuses Safeguard/Control | Q020 |
| F5 | **Incompleteness** — correct but missing required list items | Q008, Q024, Q025 |
| F6 | **Positive bias** — fails to retrieve explicit negative recommendations | Q037, Q040, Q041 |
| F7 | **Procedural reordering** — steps listed out of sequence | Q034, Q049 |
| F8 | **Version confusion** — mixes v7 and v8 content | Q050 |

---

## Difficulty Distribution

| Level | Count | IDs |
|-------|-------|-----|
| Easy | 13 | Q001–Q007, Q016–Q017, Q037 |
| Medium | 22 | Q008–Q015, Q018–Q019, Q021–Q023, Q026–Q028, Q035, Q042, Q046–Q047 |
| Hard | 15 | Q024–Q025, Q029–Q034, Q036, Q040–Q041, Q043–Q045, Q048–Q050 |

---

## Recommended Test Splits

- **Smoke test (10 Q):** Q001, Q003, Q007, Q018, Q021, Q022, Q029, Q037, Q040, Q043
- **IG filtering test (12 Q):** Q002, Q008, Q021, Q022, Q024, Q029, Q032, Q038, Q041, Q048, Q022, Q039
- **Hallucination stress test (10 Q):** Q037, Q038, Q039, Q040, Q041, Q003, Q004, Q013, Q007, Q005

