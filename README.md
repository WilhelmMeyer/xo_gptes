# xo_gptes

Detects and rewrites "GPTês" patterns in pt-BR text (partial EN support). Two-layer pipeline: regex detection (no LLM, no cost) + LLM rewrite via Claude.

Produces a revised file + a markdown report with substitutions, semantic flags, and a GPTês score (`baixo` / `médio` / `alto`).

## What it detects

- **Léxico**: _nuançado_, _robusto_, _holístico_, _ecossistema_, _transformador_...
- **Hedging**: _vale ressaltar_, _de certa forma_, _é importante destacar_...
- **Copula avoidance**: _representa um_, _serve como_, _funciona como_...
- **Signposting**: _vamos explorar_, _neste artigo iremos_, _sem mais delongas_...
- **Structural**: em dash misuse, fronted focus, excessive contrastives, bullet blocks
- **Semantic flags** (LLM): ESTRUTURA, HEDGING, VOZ, TOM, PROFUNDIDADE

## Requirements

- Python 3.10+
- One of: [Claude Code](https://claude.ai/code), [OpenCode](https://opencode.ai), or `ANTHROPIC_API_KEY` env var

## Installation

### Claude Code

Clone directly into Claude Code's skills directory:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/willj/xo_gptes.git ~/.claude/skills/xo_gptes
```

Or copy manually if you already have this repo cloned:

```bash
mkdir -p ~/.claude/skills/xo_gptes
cp -r xo_gptes/ ~/.claude/skills/xo_gptes/
```

### OpenCode

```bash
mkdir -p ~/.config/opencode/skills
git clone https://github.com/willj/xo_gptes.git ~/.config/opencode/skills/xo_gptes
```

> OpenCode also scans `~/.claude/skills/` for compatibility — a single clone there works for both tools.

## Usage

### As a Claude Code / OpenCode skill

```
/xo_gptes path/to/file.md
```

The skill asks which Claude model to use (haiku → sonnet → opus), remembers your choice for the session, then runs the review.

### CLI direct

```bash
python3 xo_gptes/run.py <file> --model <model-id>
```

`--model` is required. Example:

```bash
python3 xo_gptes/run.py artigo.md --model claude-haiku-4-5-20251001
```

## Output

Written to the same directory as the input file:

| File | Content |
|------|---------|
| `{base}_rev{N}{ext}` | Full rewritten text |
| `{base}_rev{N}_report.md` | Substitutions + semantic flags + score |

`N` auto-increments (`_rev1`, `_rev2`...) — the original is never modified.

## Architecture

**Layer 1 — regex, no LLM:** detects 50+ patterns against `PTBR_RULES` and `EN_RULES`. Language auto-detected (pt/en/mixed). Returns per-match instances + paragraph-level structural flags.

**Layer 2 — LLM:** receives the full text + detected instances. Makes per-instance keep/replace decisions and rewrites the full text (not word-for-word swaps). Runner cascade: `claude -p` → `opencode run` → Anthropic SDK. Graceful degradation: if all runners fail, the report is generated from Layer 1 only.

## Reference files

| File | Purpose |
|------|---------|
| `references/lexicon_ptbr.md` | pt-BR pattern list (mirrors code) |
| `references/lexicon_en.md` | EN pattern list (mirrors code) |
| `references/llm_prompt.md` | Layer 2 prompt template |
| `references/regex_patterns.md` | Structural patterns |
| `tests/` | Fixtures: `humano.md`, `ia.md`, `misto.md` |
