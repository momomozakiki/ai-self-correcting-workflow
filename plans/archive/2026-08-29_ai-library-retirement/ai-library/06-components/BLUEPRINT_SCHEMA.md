---
title: Component blueprint schema
version: 1.0
last_validated: 2026-08-05
official: false
source: agent-generated
tags: [governance, blueprints, components, schema]
applies_when: "Recording a code pattern that has already worked, or reusing one from this folder."
estimated_tokens: 700
---

# Component blueprint schema

A blueprint is a pattern that **has already worked and survived review**, written down so
the next instance costs a configuration change instead of a redesign.

This folder is empty, and that is the point. A blueprint written before the pattern has
been used twice is a guess with a filename — the same error as a rule harvested from
imagination rather than a real mistake (`GROWTH.md`). Write one when a pattern has earned
it, not when you expect it will.

## When a pattern earns a blueprint

All three, not any:

1. It has shipped and been reviewed at least once.
2. You can name what changes between instances and what must not.
3. Someone reimplementing it from scratch would plausibly get it wrong — otherwise the
   blueprint is overhead, and reading the original is cheaper.

## Shape

```json
{
  "id": "blueprint-<slug>",
  "version": "1.0",
  "last_updated": "YYYY-MM-DD",
  "type": "component-blueprint",
  "summary": "<one line: what this builds and when to reach for it>",
  "applies_when": "<the condition under which this is the right pattern>",
  "golden_rules": [
    { "id": "<SLUG>-01", "rule": "<a constraint that must hold>", "enforcement": "MANDATORY | SHOULD" }
  ],
  "mutable": ["<what a new instance is expected to change>"],
  "immutable": ["<what must not change, and the blueprint is void if it does>"],
  "verified_by": ["<test, or the commit where this pattern shipped>"],
  "known_limits": "<where this pattern stops being the right answer>",
  "provenance": {
    "source": "<where the pattern came from; cite official docs where they exist>",
    "authored": "YYYY-MM-DD",
    "basis": "<the task it was harvested from>"
  }
}
```

## The fields that carry the weight

**`immutable`** is the one most often left out and most worth having. A blueprint that
lists only what you may change invites the reader to assume everything else is
negotiable. Say what breaks the pattern.

**`known_limits`** stops a blueprint outliving its context. Every pattern has a scale, a
platform, or a threat model where it stops being right; a blueprint that claims none is
claiming more than it knows.

**`verified_by`** points at the code or test that proves the pattern works here. Without
it, a blueprint asserts a property of the codebase that nothing checks — which is the
failure `tests/test_governance_library.py` exists to catch, in a different file format.

## Enforcement

Blueprints are `convention`. Nothing verifies that code claiming to follow one actually
does, and nothing stops a stale blueprint being applied. Reuse is a decision the agent
makes and the reviewer checks. Do not describe a blueprint as enforced.
