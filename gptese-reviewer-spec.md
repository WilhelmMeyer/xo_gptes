# Spec: skill `gptese-reviewer`

## Visão geral

Skill para Claude Code que recebe um arquivo de texto como entrada, detecta padrões
característicos de conteúdo gerado por LLMs ("GPTês"), e produz dois artefatos:

1. **Arquivo revisado** com substituições aplicadas nos padrões locais (léxico e sintaxe),
   mesmo nome do original com sufixo `_rev{N}` antes da extensão.
2. **Relatório** `.md` com o mesmo nome base e sufixo `_rev{N}_report`, listando todas as
   ocorrências encontradas, as substituições aplicadas e flags de padrões maiores que exigem
   revisão manual pelo autor.

---

## Dois modos de invocação

A skill existe em dois comandos independentes:

- `/gptese_reviewer` — Camada 2 executada com `claude-haiku` (uso cotidiano, custo baixo)
- `/gptese_reviewer_sonnet` — Camada 2 executada com `claude-sonnet` (análise semântica
  mais fina para textos importantes)

Cada comando corresponde a um script Python separado (`run.py` e `run_sonnet.py`) e a um
`SKILL.md` próprio. A Camada 1 (regex) é idêntica nos dois modos.

---

## Arquitetura em duas camadas

### Camada 1 — Regex/determinística (rápida, sem LLM)

Responsável pelos padrões **locais e objetivos**:

- **Léxico pt-BR**: palavras e expressões de alta frequência em IA (lista mantida em
  `references/lexicon_ptbr.md`).
- **Léxico en**: mesmas palavras quando o texto mistura inglês (lista em
  `references/lexicon_en.md`).
- **Travessão sintático** (em dash `—`): quando usado fora de diálogos para conectar
  frases ou ideias (padrão: precedido e seguido de texto corrido, não início de parágrafo).
- **Fronted focus**: padrão `^[A-ZÁÉÍÓÚ][^.?!\n]{1,30}[?]\n` seguido de frase explicativa
  (gancho dramático de uma palavra ou frase curta).
- **Construção contrastiva dupla**: regex `[Ee]mbora|[Ss]e .+ no entanto|[Ee]nquanto .+,`
  em excesso (>2 por parágrafo).
- **Listas excessivas**: sequências de bullet points onde prosa seria mais natural (>4
  bullets consecutivos em resposta discursiva).

Para cada ocorrência, a Camada 1 gera:
- posição (linha:coluna)
- tipo de padrão
- texto original
- substituição aplicada

### Camada 2 — LLM semântica (análise de padrões maiores)

Recebe o texto completo e retorna análise de:

- **Hedging excessivo**: linguagem de ressalva acumulada ("é importante notar que",
  "vale ressaltar", "cabe destacar", "de certa forma", "de alguma maneira", "em certa
  medida").
- **Ausência de voz**: parágrafos sem agente claro, construções impessoais em excesso.
- **Consistência artificial de tom**: variação de sentimento/tom artificialmente plana
  ao longo do texto.
- **Estrutura padronizada**: introdução com restatement da pergunta + desenvolvimento em
  tópicos + conclusão que repete o que foi dito (padrão de resposta de chatbot).
- **Falsa profundidade**: uso de vocabulário sofisticado onde o conteúdo é raso
  (detectável por densidade de adjetivos avaliativos sem evidência).

A Camada 2 **não altera o texto**: apenas produz flags descritivos para o relatório,
indicando parágrafo(s) afetado(s) e o padrão identificado.

---

## Interface de invocação

```
/gptese_reviewer <caminho_do_arquivo>         # haiku
/gptese_reviewer_sonnet <caminho_do_arquivo>  # sonnet
```

### Parâmetros implícitos

| Parâmetro | Como passar | Padrão |
|---|---|---|
| `arquivo` | caminho no comando | obrigatório |
| `revisão N` | `_rev{N}` no nome | auto-incremento |
| `idioma` | detectado automaticamente | pt-BR |

---

## Saídas

### Arquivo revisado

- Mesmo diretório do original.
- Nome: `{nome_base}_rev{N}{extensão}` (ex: `artigo.md` → `artigo_rev1.md`).
- Conteúdo: texto com substituições da Camada 1 aplicadas diretamente. Padrões da Camada 2
  não são alterados, apenas sinalizados no relatório.

### Relatório

- Nome: `{nome_base}_rev{N}_report.md`
- Mesmo diretório do arquivo de entrada.
- Estrutura:

```markdown
# Relatório de revisão GPTês — {nome_arquivo}
Data: {ISO datetime}
Revisão: {N}
Modelo Camada 2: {haiku|sonnet}

## Resumo
- Substituições aplicadas: {n}
- Flags para revisão manual: {n}
- Score aproximado de GPTês: {baixo|médio|alto} ({justificativa de 1 linha})

## Substituições aplicadas (Camada 1)

| Linha | Tipo | Original | Substituído por |
|-------|------|----------|-----------------|
| 12    | léxico | "é crucial destacar" | "vale notar" |
| 34    | travessão | "mercado — que cresce" | "mercado, que cresce" |

## Flags para revisão manual (Camada 2)

### [ESTRUTURA] Parágrafo 1–3: restatement de abertura
O texto abre repetindo a premissa da pergunta antes de desenvolver. Padrão típico de
resposta de chatbot. Considere entrar direto no desenvolvimento.

### [HEDGING] Parágrafos 5, 8, 11: acúmulo de ressalvas
Expressões como "vale ressaltar", "é importante notar" e "de certa forma" aparecem 6
vezes. Considere eliminar as redundantes e manter no máximo uma por seção.

### [TOM] Texto inteiro: variação de sentimento artificialmente plana
...

## Padrões não encontrados
- Fronted focus: não detectado
- Listas excessivas: não detectado
```

---

## Fluxo de execução interno

```
1. Ler arquivo de entrada
2. Detectar número de revisão (checar se já existe _rev{N} no diretório → incrementar)
3. CAMADA 1:
   a. Carregar lexicon_ptbr.md (e lexicon_en.md se texto misto)
   b. Executar regex sobre o texto
   c. Coletar ocorrências com posição
   d. Aplicar substituições diretamente → gerar texto revisado
4. CAMADA 2:
   a. Montar prompt com texto completo + instruções de análise semântica
   b. Chamar LLM (haiku ou sonnet conforme o script)
   c. Parsear resposta estruturada em flags
5. Gerar arquivo revisado (_rev{N})
6. Gerar relatório (_rev{N}_report.md)
7. Imprimir no stdout: paths dos dois arquivos, modelo usado e score de GPTês
```

---

## Estrutura de arquivos da skill

```
gptese-reviewer/
├── gptese_reviewer/
│   └── SKILL.md              ← instruções para o agente (modo haiku)
├── gptese_reviewer_sonnet/
│   └── SKILL.md              ← instruções para o agente (modo sonnet)
├── run.py                    ← script haiku
├── run_sonnet.py             ← script sonnet
├── references/
│   ├── lexicon_ptbr.md
│   ├── lexicon_en.md
│   ├── regex_patterns.md
│   └── llm_prompt.md
└── tests/
    ├── humano.md
    ├── ia.md
    └── misto.md
```

---

## Arquivo `references/lexicon_ptbr.md` — conteúdo inicial

Formato: `| padrão (regex) | tipo | sugestão |`

| Padrão | Tipo | Sugestão |
|--------|------|----------|
| `[Éé] crucial` | léxico | substituir por "é necessário" |
| `[Éé] fundamental` | léxico | eliminar ou substituir por termo concreto |
| `[Vv]ale ressaltar` | hedging | eliminar |
| `[Vv]ale destacar` | hedging | eliminar |
| `[Éé] importante (notar\|destacar\|ressaltar)` | hedging | eliminar |
| `[Dd]e certa forma` | hedging | eliminar |
| `[Dd]e alguma maneira` | hedging | eliminar |
| `[Ee]m certa medida` | hedging | eliminar |
| `[Nn]o contexto (de\|do\|da)` | estrutural | reformular entrada do parágrafo |
| `[Aa]o longo (de\|do\|da\|dos\|das)` | léxico | avaliar necessidade |
| `[Ii]ntrinsecamente` | léxico | substituir por termo concreto |
| `[Ff]undamental(mente)?` | léxico | revisar necessidade |
| `[Aa]bordagem abrangente` | léxico | especificar o que é abrangente |
| `[Ee]xplorando\b` | léxico | substituir por verbo concreto (analisar, descrever) |
| `[Ee]mbarcando em` | léxico | substituir por "iniciando", "começando" |
| `[Tt]apestry\|tapeçaria de` | léxico | reformular com conexão explícita |
| `[Nn]uançado\|nuances de` | léxico | especificar qual nuance |
| `[Rr]obust[ao]` | léxico | substituir por adjetivo específico |
| `[Ss]inergias?\b` | léxico | eliminar ou especificar |
| `— [a-záéíóúâêîôûãõü]` | travessão interno | substituir por vírgula ou ponto |
| `[a-záéíóú] —` | travessão interno | substituir por vírgula ou ponto |

---

## Arquivo `references/lexicon_en.md` — conteúdo inicial

| Padrão | Tipo | Sugestão |
|--------|------|----------|
| `\bdelve(s\|d)?\b` | léxico | replace with "explore", "examine", "analyze" |
| `\btapestry\b` | léxico | rewrite with explicit connection |
| `\bcomprehensive\b` | léxico | specify what is comprehensive |
| `\bcrucial\b` | léxico | use "key", "essential", or cut |
| `\bpivotal\b` | léxico | use "key", "central", or cut |
| `\bintricate\b` | léxico | specify what makes it complex |
| `\bunderscores?\b` | léxico | use "shows", "confirms", "highlights" |
| `\bshowcas(e\|ing)\b` | léxico | use "demonstrates", "presents" |
| `\bembark(s\|ed\|ing)?\b` | léxico | use "start", "begin" |
| `\bbeacon\b` | léxico | rewrite metaphor |
| `\bnuanced?\b` | léxico | specify the nuance |
| `\brobust\b` | léxico | specify what makes it robust |
| `\bit('s\| is) worth noting\b` | hedging | cut or rewrite |
| `\bit is important to note\b` | hedging | cut |
| `\bin the context of\b` | estrutural | rewrite paragraph opener |

---

## Arquivo `references/llm_prompt.md` — template de prompt para Camada 2

```
Você é um revisor especializado em detectar padrões de linguagem artificial (GPTês) em
textos em português brasileiro. Analise o texto abaixo e identifique APENAS os seguintes
padrões de GRANDE ESCALA — não faça substituições, apenas aponte onde ocorrem:

1. ESTRUTURA DE CHATBOT: abertura que reformula a pergunta antes de responder, conclusão
   que repete o que já foi dito, desenvolvimento em tópicos genéricos.
2. HEDGING ACUMULADO: contagem de expressões de ressalva por parágrafo. Flag se >2 por
   parágrafo ou >5 no texto inteiro.
3. AUSÊNCIA DE VOZ: parágrafos inteiros sem sujeito ativo, construções impessoais em
   cadeia (>3 seguidas).
4. TOM PLANO: ausência de variação de intensidade emocional ou retórica ao longo do texto
   (texto que parece ter o mesmo "volume" do início ao fim).
5. FALSA PROFUNDIDADE: adjetivos avaliativos fortes ("profundo", "revolucionário",
   "transformador") sem evidência ou exemplo concreto.

Para cada padrão encontrado, responda em JSON estruturado:

{
  "flags": [
    {
      "tipo": "ESTRUTURA|HEDGING|VOZ|TOM|PROFUNDIDADE",
      "paragrafos": [1, 2],
      "descricao": "descrição concisa do problema",
      "sugestao": "orientação de como corrigir"
    }
  ],
  "score": "baixo|médio|alto",
  "score_justificativa": "uma linha explicando o score"
}

Se nenhum padrão for encontrado, retorne {"flags": [], "score": "baixo",
"score_justificativa": "texto não apresenta padrões de GPTês detectáveis"}.

TEXTO:
{texto}
```

---

## Decisões de design e restrições

- Existem dois scripts independentes: `run.py` (haiku) e `run_sonnet.py` (sonnet). A
  Camada 1 é compartilhada; apenas o modelo da Camada 2 difere.
- Substituições são **sempre aplicadas**: se a skill identificou um padrão e tem uma
  sugestão mapeada, substitui diretamente no arquivo revisado. O autor avalia o resultado
  comparando `_rev{N}` com o original.
- O arquivo revisado **preserva formatação**: markdown, LaTeX, código em blocos e diálogos
  (início de parágrafo com `—`) são excluídos da análise de travessão.
- A skill **não apaga o original**: sempre cria novo arquivo com sufixo.
- Se o arquivo de entrada for `.tex`, a skill ignora comandos LaTeX e analisa apenas o
  conteúdo textual dos ambientes de texto corrido.
- O relatório é gerado mesmo quando a Camada 2 falha (graceful degradation): nesse caso,
  a seção de flags é substituída por uma nota de erro e o score fica como "indeterminado".

---

## Critérios de sucesso

- [ ] Dado um texto com 5+ ocorrências léxicas conhecidas, todas são detectadas e
      substituídas no arquivo revisado.
- [ ] Travessão em diálogos (início de parágrafo) **não** é sinalizado.
- [ ] Travessão entre frases corridas **é** sinalizado e substituído por vírgula.
- [ ] O relatório é gerado mesmo quando a Camada 2 falha.
- [ ] O score de GPTês é consistente com o número e tipo de padrões encontrados.
- [ ] Textos claramente humanos recebem score "baixo".
- [ ] O relatório registra qual modelo foi usado na Camada 2.