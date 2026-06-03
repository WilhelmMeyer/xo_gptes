# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`xo-gptes` — a Claude Code skill (`/xo-gptes`) that detects and rewrites "GPTês" patterns (AI-generated language markers) in pt-BR text, with partial English support. Produces a rewritten file + a markdown report.

## Running

```bash
python3 xo_gptes/run.py <file> --model <model-id>
```

`--model` é obrigatório. O modelo é sempre escolha do usuário (via skill ou CLI direto).

Outputs to the same directory as the input:
- `{base}_rev{N}{ext}` — rewritten text
- `{base}_rev{N}_report.md` — substitutions applied + semantic flags + score

Test fixtures live in `tests/`: `humano.md`, `ia.md`, `misto.md`. Run against them to verify changes:

```bash
python3 xo_gptes/run.py tests/ia.md --model <model-id>
```

## Architecture

Two-layer pipeline, all in `xo_gptes/run.py`:

**Layer 1 — regex, no LLM, zero cost**
Detects 50+ patterns against `PTBR_RULES` and `EN_RULES` arrays. Language is auto-detected (pt/en/mixed) by word frequency. Also runs structural regexes: em dash (non-dialogue), fronted focus, excessive contrastives, bullet blocks. Returns `instances` (per-match) + `structural_flags` (paragraph-level, report-only).

**Layer 2 — LLM**
Receives the full text + all detected instances. Makes per-instance keep/replace decisions and rewrites the full text (not word-for-word swaps). Also emits semantic flags (ESTRUTURA, HEDGING, VOZ, TOM, PROFUNDIDADE). Runner cascade: `claude -p` → `opencode run` → Anthropic SDK (`ANTHROPIC_API_KEY`). Graceful degradation: if all runners fail, report is generated from Layer 1 only with score estimated by instance count.

**Score** (`score_merge`): max of Layer 1 count-based score and Layer 2 score → `baixo|médio|alto`.

## Key design constraints

- **Original never modified.** Always writes `_rev{N}` with auto-increment.
- **Layer 2 rewrites full text**, not individual tokens — hedge removals strip the entire subordinate clause, not just the flagged phrase.
- **Dialogue em dash excluded**: `^— ` (paragraph-start) is not flagged; only internal `— ` between lowercase-terminated text.
- **Layer 1 is detection-only** now — `references/regex_patterns.md` contains older direct-substitution tables that predate the current architecture where Layer 2 owns all text changes.

## Reference files

| File | Purpose |
|------|---------|
| `references/lexicon_ptbr.md` | Human-readable list of pt-BR patterns (mirrors `PTBR_RULES`) |
| `references/lexicon_en.md` | English patterns (mirrors `EN_RULES`) |
| `references/regex_patterns.md` | Structural patterns + legacy substitution tables |
| `references/llm_prompt.md` | Layer 2 prompt template (canonical source for `LAYER2_PROMPT` in `run.py`) |
| `xo_gptes/SKILL.md` | Skill invocation instructions used by Claude Code |
| `xo_gptes/run.py` | Main pipeline (Layer 1 + Layer 2) |

When adding new patterns, update both `xo_gptes/run.py` and the corresponding `references/` file (the human-readable doc).

## Skill invocation

Model preference stored per-session in `/tmp/xo-gptes_<SESSION_KEY>`. Expires when process ends.
