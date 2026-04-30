# Layer Playbook Skills

**Date:** 2026-04-29
**Status:** Approved

## Problem

Individual Pulse skills are invocable via `/pulse-extract`, `/pulse-score-signals`, etc., and fixed-sequence playbooks exist for cadenced work (`/pulse-weekly`, `/pulse-monthly`). But there is no way to say "I want to do some discovery work" and selectively pick which discovery skills to run. The user must either know the exact skill name or run an entire playbook.

## Solution

Create 7 Claude Code wrapper skills, one per operational layer, that present a numbered menu of that layer's skills and run the user's selections sequentially.

## New files

All in `.claude/skills/`:

| Directory | Slash command | Layer | Skills presented |
|-----------|--------------|-------|-----------------|
| `pulse-discover/SKILL.md` | `/pulse-discover` | Discovery | map-ecosystem, map-trust-network, scan-acquisitions, type-sources, add-source |
| `pulse-listen/SKILL.md` | `/pulse-listen` | Listen | extract, daily-extract, mine-reviews, scan-ads |
| `pulse-synthesize/SKILL.md` | `/pulse-synthesize` | Synthesis | propose-hypothesis, score-signals, update-directions, find-commodity-pattern, find-gaps |
| `pulse-act/SKILL.md` | `/pulse-act` | Action | write-brief, write-positioning, draft-survey, draft-outreach |
| `pulse-reflect/SKILL.md` | `/pulse-reflect` | Reflect | audit-drift, postmortem, connect-source |
| `pulse-knowledge/SKILL.md` | `/pulse-knowledge` | Knowledge | author-knowledge, refine-knowledge, evolve-knowledge, knowledge-status |
| `pulse-corpus-run/SKILL.md` | `/pulse-corpus-run` | Corpus | ingest, corpus-query, corpus-status, enable-corpus, disable-corpus |

## Modified files

| File | Change |
|------|--------|
| `.claude/skills/pulse/SKILL.md` | Add "Layer work" section to router mapping intents to layer skills |

## SKILL.md pattern

Each layer skill follows the same structure:

```yaml
---
name: pulse:<layer-verb>
description: "<trigger description>"
---
```

Body:
1. One-line layer purpose
2. Prerequisites check (`pulse workspace-status`)
3. Numbered menu table: `#` | Command | Time | Description
4. Execution instructions for the agent

### Execution instructions (identical in all 7)

```
## How to run

1. Show the menu above to the user
2. Ask: "Which skills do you want to run? (enter numbers like 1,3 or 'all')"
3. Run each selected skill sequentially via `pulse <verb>`
4. After each skill completes, print a one-line status before running the next
5. When all selected skills have run, summarize what was done
```

## Router update

Add to `pulse/SKILL.md` after the "Quarterly planning" section and before "I need to gather intelligence":

```markdown
### "I want to do some [layer] work" / "Run [layer] skills"

Layer playbook skills let you pick which skills to run from a layer:

| Intent | Skill |
|--------|-------|
| Discovery / mapping / sources | `/pulse-discover` |
| Intelligence gathering / listening | `/pulse-listen` |
| Analysis / hypotheses / patterns | `/pulse-synthesize` |
| Deliverables / briefs / outreach | `/pulse-act` |
| Review / audit / postmortem | `/pulse-reflect` |
| Knowledge management | `/pulse-knowledge` |
| Corpus / RAG | `/pulse-corpus-run` |
```

Then remove the existing intent sections ("I need to gather intelligence", "Analyze what we've collected", "Create a deliverable", "Map the landscape", "Review past work") since the layer skills now handle those intents with a better interactive UX.

## What we are NOT doing

- No new YAML playbook files in `default_assets/playbooks/`
- No new entries in `pulse/manifest.py`
- No changes to the Python runtime, dispatcher, or playbook runner
- No shared template files between skills — each is self-contained
- No workspace-aware smart defaults — simple numbered menu only
