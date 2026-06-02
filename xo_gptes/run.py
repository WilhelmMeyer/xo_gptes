#!/usr/bin/env python3
"""GPTês Reviewer"""

import re
import os
import json
import shutil
import subprocess
import argparse
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Detection rules: (regex, tipo, sugestao)
# Layer 1 detects; Layer 2 decides per-instance: keep or replace.
# ---------------------------------------------------------------------------

PTBR_RULES = [
    # Léxico clássico
    (r'\b[Éé] crucial\b',                                       'léxico',         'substituir por termo concreto'),
    (r'\b[Éé] fundamental\b',                                   'léxico',         'eliminar ou especificar'),
    (r'\b[Vv]ale ressaltar,?',                                   'hedging',        'eliminar'),
    (r'\b[Vv]ale destacar,?',                                    'hedging',        'eliminar'),
    (r'\b[Éé] importante (?:notar|destacar|ressaltar),?',        'hedging',        'eliminar'),
    (r'\b[Dd]e certa forma,?',                                   'hedging',        'eliminar'),
    (r'\b[Dd]e alguma maneira,?',                                'hedging',        'eliminar'),
    (r'\b[Ee]m certa medida,?',                                  'hedging',        'eliminar'),
    (r'\b[Nn]o contexto (?:de|do|da)\b',                        'estrutural',     'reformular entrada do parágrafo'),
    (r'\b[Aa]o longo (?:de|do|da|dos|das)\b',                   'léxico',         'avaliar necessidade'),
    (r'\b[Ii]ntrinsecamente\b',                                  'léxico',         'especificar'),
    (r'\b[Ff]undamentalmente\b',                                 'léxico',         'revisar necessidade'),
    (r'\b[Aa]bordagem abrangente\b',                             'léxico',         'especificar o que é abrangente'),
    (r'\b[Ee]xplorando\b',                                       'léxico',         'substituir por verbo concreto'),
    (r'\b[Ee]mbarcando em\b',                                    'léxico',         'substituir por "iniciando"'),
    (r'\b[Tt]apeçaria de\b',                                     'léxico',         'reformular com conexão explícita'),
    (r'\b[Nn]uançado\b',                                         'léxico',         'especificar a nuance'),
    (r'\b[Nn]uances de\b',                                       'léxico',         'especificar qual'),
    (r'\b[Rr]obust[ao]s?\b',                                     'léxico',         'substituir por adjetivo específico'),
    (r'\b[Ss]inergias?\b',                                       'léxico',         'eliminar ou especificar'),
    (r'\b[Cc]abe (?:destacar|ressaltar|notar),?',                'hedging',        'eliminar'),
    (r'\b[Tt]ransformador[as]?\b',                               'léxico',         'especificar o que transforma'),
    (r'\b[Pp]aradigmátic[ao]s?\b',                               'léxico',         'especificar'),
    (r'\b[Ee]cossistema\b',                                      'léxico',         'especificar os componentes'),
    (r'\b[Hh]olístic[ao]s?\b',                                   'léxico',         'especificar o que abrange'),
    (r'\b[Pp]rofundo impacto\b',                                 'léxico',         'especificar o impacto'),
    (r'\b[Rr]evolucionário\b',                                   'léxico',         'especificar em que sentido'),
    (r'\b[Cc]ada vez mais\b',                                    'léxico',         'quantificar ou cortar'),
    (r'\b[Ss]em sombra de dúvida\b',                             'hedging',        'cortar'),
    (r'\b[Ii]ndubitavelmente\b',                                 'hedging',        'cortar'),

    # Copula avoidance
    (r'\brepresenta (?:um|uma)\b',                               'copula',         'substituir por "é"'),
    (r'\bserve[m]? como\b',                                      'copula',         'substituir por "é"'),
    (r'\bfuncion[ao][m]? como\b',                                'copula',         'substituir por "é"'),
    (r'\bconstitu[íi] (?:um|uma)\b',                             'copula',         'substituir por "é"'),
    (r'\batua como\b',                                           'copula',         'substituir por "é"'),

    # Conclusões genéricas positivas
    (r'\bo futuro (?:é|parece|se mostra) (?:promissor|brilhante|esperançoso)\b', 'conclusão', 'especificar o que vem a seguir'),
    (r'\bno caminho certo\b',                                    'conclusão',      'especificar o caminho'),
    (r'\bem busca da excelência\b',                              'conclusão',      'especificar'),
    (r'\bcontinuamos (?:nossa|a nossa) jornada\b',               'conclusão',      'especificar para onde'),
    (r'\btempos (?:empolgantes|emocionantes)\b',                 'conclusão',      'cortar ou especificar'),

    # Signposting
    (r'\b[Vv]amos (?:explorar|analisar|entender|ver|discutir|mergulhar)\b', 'signpost', 'entrar direto no assunto'),
    (r'\b[Nn]este artigo (?:vamos|iremos|veremos)\b',            'signpost',       'entrar direto no assunto'),
    (r'\b[Ss]em mais delongas\b',                                'signpost',       'cortar'),
    (r'\b[Mm]ergulhando em\b',                                   'signpost',       'substituir por verbo concreto'),
    (r'\b[Cc]omo veremos\b',                                     'signpost',       'entrar direto no assunto'),
    (r'\b[Aa] seguir[,]? (?:vamos|veremos|exploraremos)\b',      'signpost',       'entrar direto no assunto'),

    # Persuasive tropes
    (r'\b[Nn]o fundo,?\b',                                       'retórico',       'cortar'),
    (r'\b[Aa] questão (?:central|real|fundamental) é\b',         'retórico',       'afirmar diretamente'),
    (r'\b[Oo] que realmente (?:importa|conta)\b',                'retórico',       'afirmar diretamente'),
    (r'\b[Ee]m última análise\b',                                'retórico',       'cortar'),
    (r'\b[Ee]m essência,?\b',                                    'retórico',       'cortar'),
    (r'\b[Nn]a (prática|realidade),?\b',                         'retórico',       'avaliar — às vezes legítimo'),

    # Vague attributions
    (r'\b[Ee]specialistas (?:afirmam|dizem|acreditam|sugerem|indicam)\b', 'atribuição vaga', 'citar fonte específica'),
    (r'\b[Pp]esquisa[s]? (?:mostram|indicam|sugerem|apontam)\b', 'atribuição vaga', 'citar estudo específico'),
    (r'\b[Ee]studo[s]? (?:mostram|indicam|sugerem|apontam|demonstram)\b', 'atribuição vaga', 'citar estudo específico'),
    (r'\b[Oo]bservadores (?:notam|apontam|destacam)\b',          'atribuição vaga', 'especificar quem'),
    (r'\b[Aa]nálises recentes\b',                                'atribuição vaga', 'citar análise específica'),

    # Gerúndio superficial
    (r'\b[Dd]estacando\b',                                       'gerúndio',       'reformular como frase principal'),
    (r'\b[Rr]essaltando\b',                                      'gerúndio',       'reformular como frase principal'),
    (r'\b[Ee]videnciando\b',                                     'gerúndio',       'reformular como frase principal'),
    (r'\b[Ii]lustrando\b',                                       'gerúndio',       'reformular como frase principal'),
    (r'\b[Cc]ontribuindo para\b',                                'gerúndio',       'reformular como frase principal'),
    (r'\b[Dd]emonstrando\b',                                     'gerúndio',       'reformular como frase principal'),
    (r'\b[Rr]efletindo\b',                                       'gerúndio',       'reformular como frase principal'),

    # Paralelo negativo
    (r'[Nn]ão (?:é|se trata de) apenas [^.!?\n]{5,60}(?:é|trata-se)', 'paralelo', 'reformular diretamente'),
    (r'[Nn]ão apenas [^.!?\n]{5,60}mas também',                 'paralelo',       'reformular diretamente'),
]

EN_RULES = [
    (r'\bdelves?\b',                                 'léxico',         'use "explore", "examine", "analyze"'),
    (r'\btapestry\b',                                'léxico',         'rewrite with explicit connection'),
    (r'\bcomprehensive\b',                           'léxico',         'specify what is comprehensive'),
    (r'\bcrucial\b',                                 'léxico',         'use "key", "essential", or cut'),
    (r'\bpivotal\b',                                 'léxico',         'use "key", "central", or cut'),
    (r'\bintricate\b',                               'léxico',         'specify what makes it complex'),
    (r'\bunderscores?\b',                            'léxico',         'use "shows", "confirms", "highlights"'),
    (r'\bshowcas(?:e|ing|es)\b',                     'léxico',         'use "demonstrates", "presents"'),
    (r'\bembark(?:s|ed|ing)?\b',                     'léxico',         'use "start", "begin"'),
    (r'\bbeacon\b',                                  'léxico',         'rewrite metaphor'),
    (r'\bnuanced?\b',                                'léxico',         'specify the nuance'),
    (r'\brobust\b',                                  'léxico',         'specify what makes it robust'),
    (r"\bit(?:'s| is) worth noting\b",               'hedging',        'cut or rewrite'),
    (r'\bit is important to note\b',                 'hedging',        'cut'),
    (r'\bin the context of\b',                       'estrutural',     'rewrite paragraph opener'),
    (r'\bfoster(?:s|ed|ing)?\b',                     'léxico',         'use "build", "create", "encourage"'),
    (r'\bleverages?\b',                              'léxico',         'use "use", "apply"'),
    (r'\bsynergies?\b',                              'léxico',         'specify or cut'),
    (r'\bholistic\b',                                'léxico',         'specify what it covers'),
    (r'\bparadigm\b',                                'léxico',         'specify model/framework'),
    (r'\blandscape\b',                               'léxico',         'specify the field or context'),
    (r'\bseminal\b',                                 'léxico',         'specify what makes it foundational'),
    (r'\bgame.?changer\b',                           'léxico',         'specify the change'),
    (r'\bcutting.?edge\b',                           'léxico',         "specify what's new"),
    # Copula avoidance
    (r'\bserves as\b',                               'copula',         'use "is"'),
    (r'\bstands as\b',                               'copula',         'use "is"'),
    (r'\bfunctions as\b',                            'copula',         'use "is"'),
    (r'\bacts as\b',                                 'copula',         'use "is"'),
    # Persuasive tropes
    (r'\bat its core\b',                             'retórico',       'cut or state directly'),
    (r'\bthe real question is\b',                    'retórico',       'state directly'),
    (r'\bwhat really matters\b',                     'retórico',       'state directly'),
    # Vague attributions
    (r'\bexperts (?:say|argue|believe|suggest)\b',   'atribuição vaga', 'cite specific source'),
    (r'\bstudies (?:show|suggest|indicate)\b',       'atribuição vaga', 'cite specific study'),
    (r'\bobservers (?:note|point|suggest)\b',        'atribuição vaga', 'specify who'),
    # Signposting
    (r"\blet'?s (?:dive|explore|look at|break down)\b", 'signpost',   'just say it'),
    (r"\bwithout further ado\b",                     'signpost',       'cut'),
    (r"\bhere'?s what you need to know\b",           'signpost',       'cut'),
    # Negative parallelisms
    (r"it'?s not (?:just|merely) [^.!?\n]{5,60}it'?s", 'paralelo',   'rewrite directly'),
    # Generic positive conclusions
    (r'\bthe future (?:looks|is) bright\b',          'conclusão',      "specify what's next"),
    (r'\bexciting times (?:lie|are) ahead\b',        'conclusão',      'cut or specify'),
]

# Em dash interno (não diálogo)
EMDASH_RE = re.compile(r'(?<=[a-záéíóúâêîôûãõü,]) — (?=[a-záéíóúâêîôûãõü])', re.UNICODE)

# Fronted focus: linha curta com ? seguida de frase explicativa
FRONTED_FOCUS_RE = re.compile(r'^([A-ZÁÉÍÓÚ][^.?!\n]{1,30}\?)\s*\n(?=[A-Z])', re.MULTILINE | re.UNICODE)

# Contrastiva dupla
CONTRASTIVE_RE = re.compile(r'\b(Embora|embora|Se .{1,40}no entanto|Enquanto .{1,40},)', re.DOTALL)

# Listas excessivas (5+ bullets consecutivos)
BULLET_BLOCK_RE = re.compile(r'^(?:[-*•]\s+.+\n){5,}', re.MULTILINE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    pt = len(re.findall(r'\b(de|do|da|em|um|uma|para|por|com|que|não|mas|se|ao|os|as)\b', text, re.I))
    en = len(re.findall(r'\b(the|of|in|is|are|that|this|with|for|and|not|but|or|to|a)\b', text, re.I))
    total = pt + en or 1
    if en / total > 0.6:
        return 'en'
    if pt / total > 0.6:
        return 'pt'
    return 'mixed'


def get_line_col(text: str, pos: int) -> tuple[int, int]:
    before = text[:pos]
    return before.count('\n') + 1, pos - before.rfind('\n')


def get_context(text: str, start: int, end: int, window: int = 60) -> str:
    cs = max(0, start - window)
    ce = min(len(text), end + window)
    prefix = ('…' if cs > 0 else '') + text[cs:start]
    suffix = text[end:ce] + ('…' if ce < len(text) else '')
    return f"{prefix}[{text[start:end]}]{suffix}".replace('\n', '↵')


# ---------------------------------------------------------------------------
# Layer 1 — detection only
# ---------------------------------------------------------------------------

def detect_layer1(text: str, lang: str) -> tuple[list, list]:
    instances = []
    structural_flags = []

    rules = []
    if lang in ('pt', 'mixed'):
        rules.extend(PTBR_RULES)
    if lang in ('en', 'mixed'):
        rules.extend(EN_RULES)

    seen_spans = set()
    for pattern, tipo, sugestao in rules:
        rx = re.compile(pattern, re.UNICODE)
        for m in rx.finditer(text):
            span = (m.start(), m.end())
            if span in seen_spans:
                continue
            seen_spans.add(span)
            ln, col = get_line_col(text, m.start())
            instances.append({
                'id': len(instances),
                'start': m.start(),
                'end': m.end(),
                'line': ln,
                'col': col,
                'tipo': tipo,
                'original': m.group(0),
                'sugestao': sugestao,
                'context': get_context(text, m.start(), m.end()),
            })

    for m in EMDASH_RE.finditer(text):
        span = (m.start(), m.end())
        if span in seen_spans:
            continue
        seen_spans.add(span)
        ln, col = get_line_col(text, m.start())
        instances.append({
            'id': len(instances),
            'start': m.start(),
            'end': m.end(),
            'line': ln,
            'col': col,
            'tipo': 'travessão',
            'original': m.group(0),
            'sugestao': 'substituir por vírgula ou restructurar frase',
            'context': get_context(text, m.start(), m.end()),
        })

    for m in FRONTED_FOCUS_RE.finditer(text):
        ln, _ = get_line_col(text, m.start())
        structural_flags.append({
            'tipo': 'FRONTED_FOCUS',
            'description': f'Linha {ln}: gancho dramático "{m.group(1)}" — considere integrar ao parágrafo.',
        })

    paragraphs = re.split(r'\n\n+', text)
    for i, para in enumerate(paragraphs, 1):
        hits = CONTRASTIVE_RE.findall(para)
        if len(hits) > 2:
            structural_flags.append({
                'tipo': 'CONTRASTIVA',
                'description': f'Parágrafo {i}: {len(hits)} construções contrastivas (Embora/Enquanto/no entanto). Máx: 2.',
            })

    for m in BULLET_BLOCK_RE.finditer(text):
        ln, _ = get_line_col(text, m.start())
        n = len(re.findall(r'^[-*•]\s+', m.group(0), re.MULTILINE))
        structural_flags.append({
            'tipo': 'LISTA_EXCESSIVA',
            'description': f'Linha {ln}: bloco de {n} bullets — considere transformar em prosa.',
        })

    instances.sort(key=lambda x: x['start'])
    for i, inst in enumerate(instances):
        inst['id'] = i

    return instances, structural_flags


# ---------------------------------------------------------------------------
# Layer 2 — LLM: per-instance decisions + semantic flags
# ---------------------------------------------------------------------------

LAYER2_PROMPT = """\
Você é revisor especializado em GPTês (linguagem artificial em português brasileiro).

Receberá:
1. TEXTO ORIGINAL
2. INSTÂNCIAS detectadas por regex — id, linha, tipo, trecho, contexto

Sua tarefa em duas partes:

PARTE A — Reescreva o texto corrigindo os padrões detectados.
Regras:
- Para cada instância: mantenha se o uso for legítimo no contexto (ex: "ao longo de 3 anos" é factual), ou corrija
- Ao corrigir, reestruture a frase inteira se necessário — não troque palavra por palavra
- Ao eliminar hedge ("vale ressaltar que X" → "X"), remova a subordinada inteira, não só a expressão
- Preservar conteúdo, estrutura de seções e estilo geral do autor
- Registre cada decisão no campo "changes" com o id da instância correspondente

PARTE B — Detecte E corrija padrões semânticos de GRANDE ESCALA diretamente no revised_text:
1. ESTRUTURA: abertura que reformula antes de responder → entre direto no assunto; conclusão que repete → corte ou sintetize em uma frase
2. HEDGING: ressalvas acumuladas (>2 por parágrafo ou >5 no texto) → elimine as redundantes, deixe no máximo uma por seção
3. VOZ: parágrafos sem sujeito ativo, impessoais em cadeia (>3 seguidas) → reescreva com sujeito explícito
4. TOM: variação de intensidade artificialmente plana → ajuste pontuação e estrutura de frase para criar ritmo
5. PROFUNDIDADE: adjetivos fortes ("transformador", "revolucionário") sem evidência → remova o adjetivo ou adicione o dado concreto que o justifica

O revised_text deve incorporar as correções de PARTE A e PARTE B. Para cada padrão corrigido, registre em semantic_changes o que foi feito. Se nenhuma correção for necessária para um tipo, omita-o.

Responda APENAS com JSON válido, sem markdown:

{{
  "revised_text": "texto completo reescrito com correções de PARTE A e PARTE B",
  "changes": [
    {{"id": 0, "action": "keep", "reason": "uso factual"}},
    {{"id": 1, "action": "replace", "original": "vale ressaltar que a análise", "replacement": "a análise", "reason": "hedge eliminado"}}
  ],
  "semantic_changes": [
    {{"tipo": "ESTRUTURA|HEDGING|VOZ|TOM|PROFUNDIDADE", "paragrafos": [1,2], "descricao": "o que foi corrigido e como"}}
  ],
  "score": "baixo|médio|alto",
  "score_justificativa": "uma linha"
}}

INSTÂNCIAS DETECTADAS:
{instancias}

TEXTO ORIGINAL:
{texto}"""


def _parse_llm_output(raw: str) -> dict:
    raw = raw.strip()
    m = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', raw)
    if m:
        raw = m.group(1).strip()
    return json.loads(raw)


def _call_claude_cli(model: str, prompt: str) -> str | None:
    bin_path = shutil.which('claude')
    if not bin_path:
        return None
    try:
        r = subprocess.run(
            [bin_path, '-p', prompt, '--model', model],
            capture_output=True, text=True, timeout=180,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None


def _call_opencode_cli(model: str, prompt: str) -> str | None:
    bin_path = shutil.which('opencode')
    if not bin_path:
        return None
    oc_model = model if '/' in model else f'anthropic/{model}'
    try:
        r = subprocess.run(
            [bin_path, 'run', '--format', 'json', '--model', oc_model, prompt],
            capture_output=True, text=True, timeout=180,
        )
        if r.returncode != 0:
            return None
        parts = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                if ev.get('type') == 'text':
                    parts.append(ev.get('part', {}).get('text', ''))
            except Exception:
                pass
        text = ''.join(parts).strip()
        return text or None
    except Exception:
        pass
    return None


def _call_anthropic_sdk(model: str, prompt: str) -> str | None:
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception:
        return None


def call_layer2(text: str, instances: list, model: str) -> dict:
    compact = [
        {k: v for k, v in inst.items() if k not in ('start', 'end', 'col')}
        for inst in instances
    ]
    prompt = LAYER2_PROMPT.format(
        instancias=json.dumps(compact, ensure_ascii=False, indent=2),
        texto=text,
    )

    for runner_fn, label in [
        (_call_claude_cli,    'claude-cli'),
        (_call_opencode_cli,  'opencode-cli'),
        (_call_anthropic_sdk, 'anthropic-sdk'),
    ]:
        raw = runner_fn(model, prompt)
        if raw:
            try:
                result = _parse_llm_output(raw)
                result['_runner'] = label
                return result
            except Exception:
                continue

    return {
        'error': (
            'Camada 2 indisponível. '
            'Instale claude (Claude Code) ou opencode, ou defina ANTHROPIC_API_KEY.'
        )
    }


def extract_changes(instances: list, changes: list) -> tuple[list, list]:
    inst_map = {inst['id']: inst for inst in instances}
    applied, kept = [], []
    for c in changes:
        inst = inst_map.get(c.get('id'))
        line = inst['line'] if inst else '?'
        tipo = inst['tipo'] if inst else '?'
        if c.get('action') == 'replace':
            applied.append({
                'id': c.get('id'),
                'line': line,
                'tipo': tipo,
                'original': c.get('original', inst['original'] if inst else ''),
                'replacement': c.get('replacement', ''),
                'reason': c.get('reason', ''),
            })
        elif c.get('action') == 'keep':
            kept.append({
                'id': c.get('id'),
                'line': line,
                'tipo': tipo,
                'original': inst['original'] if inst else '',
                'reason': c.get('reason', ''),
            })
    return applied, kept


# ---------------------------------------------------------------------------
# Score
# ---------------------------------------------------------------------------

def score_merge(n_replaced: int, l2_score: str | None) -> str:
    if l2_score is None:
        n = n_replaced
        if n >= 8: return 'alto'
        if n >= 3: return 'médio'
        return 'baixo'
    rank = {'baixo': 0, 'médio': 1, 'alto': 2}
    l2 = rank.get(l2_score, 0)
    l1 = 2 if n_replaced >= 8 else (1 if n_replaced >= 3 else 0)
    return ['baixo', 'médio', 'alto'][max(l2, l1)]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(
    filename: str,
    rev_n: int,
    instances: list,
    applied_subs: list,
    kept: list,
    structural_flags: list,
    layer2_result: dict,
    final_score: str,
    model: str,
    runner: str = 'desconhecido',
) -> str:
    now = datetime.now().isoformat(timespec='seconds')
    semantic_changes = layer2_result.get('semantic_changes', []) if 'error' not in layer2_result else []
    score_just = layer2_result.get('score_justificativa', f'{len(applied_subs)} substituições aplicadas')

    lines = [
        f"# Relatório de revisão GPTês — {filename}",
        f"Data: {now}",
        f"Revisão: {rev_n}",
        f"Modelo Camada 2: {model}",
        f"Runner Camada 2: {runner}",
        "",
        "## Resumo",
        f"- Instâncias detectadas (Camada 1): {len(instances)}",
        f"- Substituições léxicas aplicadas (Camada 1+2): {len(applied_subs)}",
        f"- Mantidas pelo revisor (uso legítimo): {len(kept)}",
        f"- Correções semânticas aplicadas (Camada 2): {len(semantic_changes)}",
        f"- Flags estruturais (Camada 1, revisão manual): {len(structural_flags)}",
        f"- Score aproximado de GPTês: **{final_score}** ({score_just})",
        "",
        "## Substituições aplicadas",
        "",
        "| Linha | Tipo | Original | Substituído por | Motivo |",
        "|-------|------|----------|-----------------|--------|",
    ]

    if applied_subs:
        for s in applied_subs:
            orig = s['original'].replace('|', '\\|')
            rep = (s['replacement'] or '*(removido)*').replace('|', '\\|')
            reason = s.get('reason', '').replace('|', '\\|')
            lines.append(f"| {s['line']} | {s['tipo']} | `{orig}` | `{rep}` | {reason} |")
    else:
        lines.append("| — | — | — | — | Nenhuma substituição |")

    if kept:
        lines += [
            "",
            "## Mantidos pelo revisor (uso legítimo)",
            "",
            "| Linha | Tipo | Trecho | Motivo |",
            "|-------|------|--------|--------|",
        ]
        for k in kept:
            orig = k['original'].replace('|', '\\|')
            reason = k.get('reason', '').replace('|', '\\|')
            lines.append(f"| {k['line']} | {k['tipo']} | `{orig}` | {reason} |")

    lines += ["", "## Correções semânticas aplicadas (Camada 2)", ""]

    if 'error' in layer2_result:
        lines += [
            f"> **Erro na Camada 2:** {layer2_result['error']}",
            "> Score calculado só pela Camada 1.",
        ]
    elif semantic_changes:
        for c in semantic_changes:
            paras = ', '.join(str(p) for p in c.get('paragrafos', []))
            lines += [
                f"### [{c['tipo']}] Parágrafos {paras}",
                c.get('descricao', ''),
                "",
            ]
    else:
        lines.append("Nenhuma correção semântica de grande escala aplicada.")

    if structural_flags:
        lines += ["", "## Flags estruturais (Camada 1)", ""]
        for f in structural_flags:
            lines.append(f"- **[{f['tipo']}]** {f['description']}")

    found_types = {inst['tipo'] for inst in instances}
    all_structural = {
        'fronted focus': 'FRONTED_FOCUS',
        'listas excessivas': 'LISTA_EXCESSIVA',
        'contrastiva dupla': 'CONTRASTIVA',
    }
    not_found = [name for name, t in all_structural.items()
                 if t not in {f['tipo'] for f in structural_flags}]
    if not_found:
        lines += ["", "## Padrões estruturais não encontrados", ""]
        for name in not_found:
            lines.append(f"- {name}: não detectado")

    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------------------
# Next revision number
# ---------------------------------------------------------------------------

def next_revision(directory: Path, base: str, ext: str) -> int:
    n = 1
    while (directory / f"{base}_rev{n}{ext}").exists():
        n += 1
    return n


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description='GPTês Reviewer')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('file', nargs='?', help='Arquivo a revisar')
    group.add_argument('--text', help='Texto direto (sem arquivo)')
    parser.add_argument('--model', required=True, help='Modelo para Camada 2 (ex: claude-haiku-4-5-20251001)')
    args = parser.parse_args()

    if args.text:
        text = args.text
        lang = detect_language(text)
        instances, structural_flags = detect_layer1(text, lang)
        layer2_result = call_layer2(text, instances, args.model)

        revised_text = text
        applied_subs = []
        kept = []

        if 'error' not in layer2_result:
            revised_text = layer2_result.get('revised_text', text)
            changes = layer2_result.get('changes', [])
            applied_subs, kept = extract_changes(instances, changes)

        l2_score = layer2_result.get('score') if 'error' not in layer2_result else None
        final_score = score_merge(len(applied_subs), l2_score)
        runner = layer2_result.get('_runner', 'indisponível')

        report = build_report(
            '<texto inline>', 1, instances, applied_subs, kept,
            structural_flags, layer2_result, final_score, args.model, runner,
        )

        print("=== TEXTO REVISADO ===")
        print(revised_text)
        print("\n=== RELATÓRIO ===")
        print(report)
        return

    input_path = Path(args.file).expanduser().resolve()
    if not input_path.exists():
        print(f"Arquivo não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding='utf-8')
    base = re.sub(r'_rev\d+$', '', input_path.stem)
    ext = input_path.suffix
    directory = input_path.parent
    rev_n = next_revision(directory, base, ext)

    lang = detect_language(text)

    instances, structural_flags = detect_layer1(text, lang)
    layer2_result = call_layer2(text, instances, args.model)

    revised_text = text
    applied_subs = []
    kept = []

    if 'error' not in layer2_result:
        revised_text = layer2_result.get('revised_text', text)
        changes = layer2_result.get('changes', [])
        applied_subs, kept = extract_changes(instances, changes)

    l2_score = layer2_result.get('score') if 'error' not in layer2_result else None
    final_score = score_merge(len(applied_subs), l2_score)
    runner = layer2_result.get('_runner', 'indisponível')

    rev_path = directory / f"{base}_rev{rev_n}{ext}"
    report_path = directory / f"{base}_rev{rev_n}_report.md"

    rev_path.write_text(revised_text, encoding='utf-8')
    report = build_report(
        input_path.name, rev_n, instances, applied_subs, kept,
        structural_flags, layer2_result, final_score, args.model, runner,
    )
    report_path.write_text(report, encoding='utf-8')

    print(f"Arquivo revisado : {rev_path}")
    print(f"Relatório        : {report_path}")
    print(f"Modelo Camada 2  : {args.model}")
    print(f"Runner Camada 2  : {runner}")
    print(f"Score de GPTês   : {final_score}")


if __name__ == '__main__':
    main()
