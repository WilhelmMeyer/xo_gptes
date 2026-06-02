# xo_gptes

Skill para Claude Code que detecta e reescreve padrões de "GPTês" em texto pt-BR (suporte parcial a EN).

Produz um arquivo revisado + relatório com substituições, flags e score (`baixo` / `médio` / `alto`).

## Instalação

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/WilhelmMeyer/xo_gptes.git ~/.claude/skills/xo_gptes
```

## Uso

```
/xo_gptes caminho/do/arquivo.md
```

A skill pergunta qual modelo usar na primeira execução e guarda a escolha para a sessão.

### Via CLI

```bash
python3 xo_gptes/run.py <arquivo> --model <model-id>
```

## Saídas

No mesmo diretório do arquivo de entrada:

| Arquivo | Conteúdo |
|---------|----------|
| `{base}_rev{N}{ext}` | Texto reescrito |
| `{base}_rev{N}_report.md` | Substituições + flags + score |

O original nunca é modificado. `N` auto-incrementado.

## O que detecta

- **Léxico**: _nuançado_, _robusto_, _holístico_, _ecossistema_, _transformador_...
- **Hedging**: _vale ressaltar_, _de certa forma_, _é importante destacar_...
- **Copula avoidance**: _representa um_, _serve como_, _funciona como_...
- **Signposting**: _vamos explorar_, _neste artigo iremos_, _sem mais delongas_...
- **Estruturais**: travessão indevido, foco fronteado, contrastivos excessivos, blocos de bullet
- **Semânticos** (LLM): ESTRUTURA, HEDGING, VOZ, TOM, PROFUNDIDADE

## Arquitetura

**Camada 1 — regex:** detecta 50+ padrões sem custo de LLM. Idioma detectado automaticamente (pt/en/misto).

**Camada 2 — LLM:** reescreve o texto completo com base nas instâncias detectadas. Decide por instância: manter (uso legítimo) ou reescrever. Runners em cascata: `claude -p` → `opencode run`. Se ambos falharem, o relatório é gerado só com Camada 1.

## Referências

| Arquivo | Conteúdo |
|---------|----------|
| `references/lexicon_ptbr.md` | Padrões pt-BR |
| `references/lexicon_en.md` | Padrões EN |
| `references/llm_prompt.md` | Prompt da Camada 2 |
| `tests/` | Fixtures: `humano.md`, `ia.md`, `misto.md` |
