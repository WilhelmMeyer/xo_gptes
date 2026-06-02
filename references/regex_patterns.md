# Padrões Regex — Camada 1

Padrões estruturais além do léxico. Aplicados em ordem após o léxico.

## Travessão sintático (em dash `—`)

Sinaliza `—` fora de diálogos conectando frases/ideias.

**Excluir**: início de parágrafo (`^— `) — diálogo legítimo.

```python
# Em dash interno: precedido de letra minúscula ou pontuação, seguido de letra
EMDASH_INTERNAL = re.compile(r'(?<=[a-záéíóúâêîôûãõü,]) — (?=[a-záéíóúâêîôûãõü])', re.UNICODE)
# Substituição: vírgula
```

## Fronted focus (gancho dramático)

Linha curta terminando em `?` seguida de frase explicativa — padrão de abertura de chatbot.

```python
FRONTED_FOCUS = re.compile(r'^([A-ZÁÉÍÓÚ][^.?!\n]{1,30}\?)\s*\n(?=[A-Z])', re.MULTILINE | re.UNICODE)
# Não substitui; sinaliza para flag no relatório
```

## Construção contrastiva dupla

`Embora`, `Se ... no entanto`, `Enquanto ...` em excesso por parágrafo (>2).

```python
CONTRASTIVE = re.compile(r'\b([Ee]mbora|[Ss]e .{1,40}no entanto|[Ee]nquanto .{1,40},)', re.DOTALL)
# Conta por parágrafo; flag se > 2
```

## Listas excessivas

>4 bullets consecutivos em contexto discursivo.

```python
BULLET_BLOCK = re.compile(r'^(?:[-*•]\s+.+\n){5,}', re.MULTILINE)
# Não substitui; flag para revisão manual
```

## Substituições léxicas — regras de reescrita

Mapeamento regex → substituição aplicada diretamente no texto revisado:

```python
SUBSTITUTIONS_PTBR = [
    (r'\bé crucial\b', 'é necessário'),
    (r'\bÉ crucial\b', 'É necessário'),
    (r'\bé fundamental\b', 'é importante'),
    (r'\bÉ fundamental\b', 'É importante'),
    (r'\bvale ressaltar\b', ''),          # eliminar + limpar espaço
    (r'\bVale ressaltar\b', ''),
    (r'\bvale destacar\b', ''),
    (r'\bVale destacar\b', ''),
    (r'\bé importante notar\b', ''),
    (r'\bé importante destacar\b', ''),
    (r'\bé importante ressaltar\b', ''),
    (r'\bde certa forma\b', ''),
    (r'\bde alguma maneira\b', ''),
    (r'\bem certa medida\b', ''),
    (r'\bno contexto de\b', 'em'),
    (r'\bno contexto do\b', 'no'),
    (r'\bno contexto da\b', 'na'),
    (r'\bIntrinsecamente\b', ''),
    (r'\bintrinsecamente\b', ''),
    (r'\babordagem abrangente\b', 'abordagem detalhada'),
    (r'\bExplorando\b', 'Analisando'),
    (r'\bexplorando\b', 'analisando'),
    (r'\bEmbarcando em\b', 'Iniciando'),
    (r'\bembarcando em\b', 'iniciando'),
    (r'\bnuançado\b', 'específico'),
    (r'\bNuançado\b', 'Específico'),
    (r'\brobusta\b', 'sólida'),
    (r'\brobusta\b', 'sólida'),
    (r'\brobusta\b', 'sólido'),
    (r'\brobusta\b', 'sólido'),
    (r'\bsinergias\b', 'interações'),
    (r'\bsinergia\b', 'interação'),
    (r'\bcabe destacar\b', ''),
    (r'\bcabe ressaltar\b', ''),
    (r'\bcabe notar\b', ''),
    (r'\bCabe destacar\b', ''),
    (r'\bCabe ressaltar\b', ''),
    (r'\bCabe notar\b', ''),
]

SUBSTITUTIONS_EN = [
    (r'\bdelves\b', 'explores'),
    (r'\bdelved\b', 'explored'),
    (r'\bdelve\b', 'explore'),
    (r'\bcomprehensive\b', 'thorough'),
    (r'\bcrucial\b', 'key'),
    (r'\bpivotal\b', 'key'),
    (r'\bunderscores\b', 'confirms'),
    (r'\bunderscore\b', 'confirm'),
    (r'\bshowcasing\b', 'demonstrating'),
    (r'\bshowcase\b', 'demonstrate'),
    (r'\bshowcases\b', 'demonstrates'),
    (r'\bembark\b', 'start'),
    (r'\bembарks\b', 'starts'),
    (r'\bемbarked\b', 'started'),
    (r'\bемbarking\b', 'starting'),
    (r'\bnuanced\b', 'specific'),
    (r'\bnuance\b', 'detail'),
    (r'\brobust\b', 'solid'),
    (r'\bit is worth noting\b', ''),
    (r'\bit\'s worth noting\b', ''),
    (r'\bit is important to note\b', ''),
    (r'\bfostering\b', 'building'),
    (r'\bfoster\b', 'build'),
    (r'\bfosters\b', 'builds'),
    (r'\bleverage\b', 'use'),
    (r'\bleverages\b', 'uses'),
    (r'\bleveraged\b', 'used'),
    (r'\bsynergy\b', 'interaction'),
    (r'\bsynergies\b', 'interactions'),
    (r'\bholistic\b', 'comprehensive'),
    (r'\bcutting-edge\b', 'modern'),
    (r'\bgame-changer\b', 'significant change'),
]
```

## Prioridade de aplicação

1. Léxico pt-BR (substituições diretas)
2. Léxico en (substituições diretas, texto misto)
3. Travessão interno (substituição por vírgula)
4. Fronted focus (flag apenas)
5. Contrastiva dupla (flag se >2/parágrafo)
6. Listas excessivas (flag se >4 bullets)