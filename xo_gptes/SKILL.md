---
name: xo-gptes
description: Detecta e reescreve padrões GPTês em texto pt-BR. Produz arquivo revisado + relatório.
compatibility: claude-code, opencode
---

# Skill: xo-gptes

Detecta e reescreve padrões GPTês em texto pt-BR. Produz arquivo revisado + relatório.

**allowed-tools:** Read, Write, Bash, AskUserQuestion

---

## Invocação

```
/xo-gptes <caminho_do_arquivo>
```

Exemplo: `/xo-gptes artigo.md`

---

## Execução

### Passo 1 — Selecionar modelo para Camada 2

Verificar preferência da sessão atual:

```bash
SESSION_KEY=$(ps -o ppid= -p $$ 2>/dev/null | tr -d ' ')
PREFS_FILE="/tmp/xo-gptes_${SESSION_KEY}"
cat "$PREFS_FILE" 2>/dev/null || echo "{}"
```

- Se arquivo existe e contém `preferred_model` → usar esse modelo, pular para Passo 2
- Caso contrário → detectar plataforma e montar opções

**Detecção de plataforma:**

```bash
command -v claude   &>/dev/null && echo "claudecode"
command -v opencode &>/dev/null && echo "opencode"
```

---

**Se Claude Code** (`claude` disponível):

O agente já conhece os modelos disponíveis na sessão pelo próprio contexto do sistema. Apresentar os modelos da sessão atual ordenados do mais barato ao mais caro (haiku → sonnet → opus), um por família, versão mais recente de cada.

---

**Se OpenCode** (`opencode` disponível):

Listar todos os modelos disponíveis na sessão:

```bash
opencode models 2>/dev/null
```

Apresentar os modelos via AskUserQuestion com uma seleção representativa (modelo atual da sessão, mais barato, mais capaz, e opção "Outro" para digitar manualmente). Usar IDs exatos como retornados pelo comando.

---

Apresentar via AskUserQuestion. Sempre incluir "Other" para digitar qualquer ID manualmente.

Após escolha, salvar para a sessão:

```bash
echo "{\"preferred_model\": \"<modelo escolhido>\"}" > "$PREFS_FILE"
```

O arquivo `/tmp/xo-gptes_<SESSION_KEY>` expira quando o processo encerra ou na reinicialização.

### Passo 2 — Executar revisão

```bash
RUN_PY="$HOME/.claude/skills/xo-gptes/run.py"
[ -f "$RUN_PY" ] || RUN_PY=$(find "$HOME" -maxdepth 8 -path "*/xo-gptes/run.py" 2>/dev/null | head -1)

# Fallback para opencode
[ -f "$RUN_PY" ] || RUN_PY="$HOME/.config/opencode/skills/xo-gptes/run.py"
INPUT="<argumento recebido>"
if [ -f "$INPUT" ]; then
  python3 "$RUN_PY" "$INPUT" --model <modelo>
else
  python3 "$RUN_PY" --text "$INPUT" --model <modelo>
fi
```

### Passo 3 — Exibir resultado

**Modo arquivo** (entrada era um caminho de arquivo): mostrar os 5 campos do stdout:

```
Arquivo revisado : /path/artigo_rev1.md
Relatório        : /path/artigo_rev1_report.md
Modelo Camada 2  : <modelo>
Runner Camada 2  : claude-cli | opencode-cli | indisponível
Score de GPTês   : baixo | médio | alto
```

**Modo texto inline** (entrada era texto direto): exibir na sessão os dois blocos retornados pelo script:

```
=== TEXTO REVISADO ===
<texto revisado>

=== RELATÓRIO ===
<relatório markdown>
```

Renderizar o relatório como markdown na resposta.

---

## O que a revisão faz

**Camada 1 (regex — sem LLM, sem custo):** detecta 50+ padrões em pt-BR e EN.
Tipos: léxico, hedging, copula avoidance, signpost, conclusão genérica, atribuição vaga, gerúndio superficial, travessão, paralelo negativo.

**Camada 2 (LLM — subagente separado, sem contexto desta sessão):** recebe texto + instâncias detectadas. Decide por instância: manter (uso legítimo) ou reescrever a frase inteira. Detecta também: ESTRUTURA, HEDGING, VOZ, TOM, PROFUNDIDADE.

Runners tentados em cascata: `claude -p` → `opencode run` → Anthropic SDK.

---

## Saídas

No mesmo diretório do arquivo de entrada:

| Arquivo | Conteúdo |
|---------|----------|
| `{base}_rev{N}{ext}` | Texto reescrito pela Camada 2 |
| `{base}_rev{N}_report.md` | Substituições + flags semânticos + score |

**N** auto-incrementado: `_rev1`, `_rev2`...

---

## Graceful degradation

Camada 2 falha → relatório gerado com flags só da Camada 1, score aproximado, nota de erro.

---

## Referências

- `references/lexicon_ptbr.md` — padrões pt-BR
- `references/lexicon_en.md` — padrões EN
- `references/regex_patterns.md` — padrões estruturais
- `references/llm_prompt.md` — prompt template Camada 2
