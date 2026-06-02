# Template de Prompt — Camada 2

Prompt enviado à API Anthropic (haiku ou sonnet). `{texto}` substituído pelo conteúdo do arquivo após substituições da Camada 1.

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

## Notas de uso

- JSON retornado pelo LLM parseado pelo script. Falha → graceful degradation.
- `paragrafos`: array inteiros 1-indexed, conta parágrafos não-vazios.
- `score` reflete flags Camada 2 + volume Camada 1.
- Script mescla scores: Camada 1 >5 ocorrências + Camada 2 "baixo" → score final elevado para "médio".