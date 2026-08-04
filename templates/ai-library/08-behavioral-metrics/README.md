---
title: Behavioral metrics — what is written here, and what is deliberately absent
version: 1.0
last_validated: 2026-08-04
official: false
source: agent-generated
tags: [metrics, loop-detection, governance]
applies_when: "Reading the hook-written metric logs, or asking why a v14 metric has no file."
estimated_tokens: 350
---

# Behavioral metrics

Written by the hook; JSONL files appear on first write.

| File | Written by | Status |
|------|-----------|--------|
| `loop_detection.jsonl` | `handle_post_tool_use` when a repeat threshold trips | **live** |
| `self_critique.jsonl` | the agent, during a retrospective | convention |

## What is deliberately absent

The imported framework specifies RAG grounding confidence, attribution completeness, and a
policy-aligned action score. **All three are dropped, not deferred.** Each needs embeddings
and a judge model reached over the API; this runtime is Claude Code on a Claude subscription
with no API key. Recording empty metric files for them would imply a measurement that never
happens.

The five MirrorDNA behavioral metrics (integrity index, drift coefficient, recurrence rate,
verification ratio, stability half-life) are declarative for the same reason - no per-session
scoring infrastructure exists here. `recurrence` is the one signal actually tracked, and it
lives in `docs/RETROSPECTIVE.md` in plain prose.

See `docs/governance-integration-decision.md` section 5.
