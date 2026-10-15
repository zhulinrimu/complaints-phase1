# Phase 1 — Streaming Complaint Data-Quality Profiler

Course project, Phase 1 report: *Problem & Computational Prototype*.
Dataset: CFPB consumer-complaint database (≈8.9 GB, ~31.7M rows, 16 columns).

This prototype proves the project is (a) a concrete, feasible problem and
(b) representable computationally in Python. It streams the raw complaints
file and produces a data dictionary plus a defect summary **in constant
memory**, so it scales from the 800-row sample to the full 8.9 GB file.

## What it does
- Profiles every column: inferred type, missing count/rate, distinct count, min/max.
- Detects defects: duplicate `Complaint ID`, malformed `Date received`/`Date sent
  to company` (ISO-8601), malformed `ZIP code` (5-digit), and row-width mismatches.
- Emits a Markdown data dictionary and a JSON profile, both reproducible.

## Setup
```bash
cd profiler
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run on the sample (fast)
```bash
python profiler.py ../data/sample_complaints.csv \
    --json ../data/profile_sample.json \
    --dict ../data/data_dictionary.md
```

## Run on the full 8.9 GB archive (streaming, constant memory)
```bash
python profiler.py complaints.csv.zip --dict data_dictionary_full.md
```
Reading from a `.zip` is supported; only the CSV stream is held in memory.

## Tests
```bash
pytest -q
```
Covers: schema/column coverage, missing-value detection, duplicate-ID detection,
date & ZIP validation, row-width mismatch, streaming `--limit`, empty-file safety,
reproducibility, and data-dictionary generation. (≥10 tests, all boundary-focused.)

## Reproduce the sample
```bash
python make_sample.py --source complaints.csv.zip --limit 800
```

## Assumptions & constraints
- Input is UTF-8, comma-delimited, header present (CFPB schema, 16 columns).
- Memory stays O(1) in rows; duplicate-ID tracking uses a set that grows with
  distinct IDs (~31.7M) — acceptable on a server, or swap for an external sort /
  Bloom filter at full scale (noted as a Phase 2 engineering task).
- Full-population statistics are sampled/streamed, not loaded; semantic cleaning,
  narrative NLP, and modeling are out of scope for Phase 1.
