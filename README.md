# xo_gptes

Detecta e reescreve padrões de "GPTês" em texto pt-BR (suporte parcial a EN). Pipeline em duas camadas: detecção por regex (sem LLM, sem custo) + reescrita via Claude.

Produz um arquivo revisado + um relatório markdown com as substituições, flags semânticos e um score de GPTês (`baixo` / `médio` / `alto`).

## O que detecta

- **Léxico**: _nuançado_, _robusto_, _holístico_, _ecossistema_, _transformador_...
- **Hedging**: _vale ressaltar_, _de certa forma_, _é importante destacar_...
- **Copula avoidance**: _representa um_, _serve como_, _funciona como_...
- **Signposting**: _vamos explorar_, _neste artigo iremos_, _sem mais delongas_...
- **Estruturais**: uso indevido de travessão, foco fronteado, contrastivos excessivos, blocos de bullet
- **Flags semânticos** (LLM): ESTRUTURA, HEDGING, VOZ, TOM, PROFUNDIDADE

## Requisitos

- Python 3.10+
- [Claude Code](https://claude.ai/code) ou [OpenCode](https://opencode.ai)

## Instalação

### Claude Code

Clone direto no diretório de skills:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/WilhelmMeyer/xo_gptes.git ~/.claude/skills/xo_gptes
```

Ou copie manualmente se já tiver o repo clonado:

```bash
mkdir -p ~/.claude/skills/xo_gptes
cp -r xo_gptes/ ~/.claude/skills/xo_gptes/
```

### OpenCode

```bash
mkdir -p ~/.config/opencode/skills
git clone https://github.com/WilhelmMeyer/xo_gptes.git ~/.config/opencode/skills/xo_gptes
```

> OpenCode também lê `~/.claude/skills/` por compatibilidade — um único clone lá funciona para as duas ferramentas.

## Uso

### Como skill

```
/xo_gptes caminho/do/arquivo.md
```

A skill pergunta qual modelo Claude usar (haiku → sonnet → opus), guarda a escolha para a sessão e executa a revisão.

### Via CLI

```bash
python3 xo_gptes/run.py <arquivo> --model <model-id>
```

`--model` é obrigatório. Exemplo:

```bash
python3 xo_gptes/run.py artigo.md --model claude-haiku-4-5-20251001
```

## Saídas

Geradas no mesmo diretório do arquivo de entrada:

| Arquivo | Conteúdo |
|---------|----------|
| `{base}_rev{N}{ext}` | Texto reescrito |
| `{base}_rev{N}_report.md` | Substituições + flags semânticos + score |

`N` auto-incrementado (`_rev1`, `_rev2`...). O original nunca é modificado.

## Arquitetura

**Camada 1 — regex, sem LLM:** detecta 50+ padrões em `PTBR_RULES` e `EN_RULES`. Idioma detectado automaticamente (pt/en/misto). Retorna instâncias por match + flags estruturais por parágrafo.

**Camada 2 — LLM:** recebe o texto completo + instâncias detectadas. Decide por instância: manter (uso legítimo) ou reescrever a frase inteira. Runners em cascata: `claude -p` → `opencode run`. Degradação graciosa: se ambos falharem, o relatório é gerado só com Camada 1.

## Referências

| Arquivo | Conteúdo |
|---------|----------|
| `references/lexicon_ptbr.md` | Lista de padrões pt-BR |
| `references/lexicon_en.md` | Lista de padrões EN |
| `references/llm_prompt.md` | Template do prompt da Camada 2 |
| `references/regex_patterns.md` | Padrões estruturais |
| `tests/` | Fixtures: `humano.md`, `ia.md`, `misto.md` |
