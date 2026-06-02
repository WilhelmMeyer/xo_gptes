# xo_gptes

Skill para Claude Code e OpenCode que detecta e reescreve marcas de linguagem artificial
("GPTês") em textos pt-BR, com suporte parcial a EN.

## Instalação

**Claude Code**
```
git clone https://github.com/WilhelmMeyer/xo_gptes.git ~/.claude/skills/xo_gptes
```

**OpenCode**
```
git clone https://github.com/WilhelmMeyer/xo_gptes.git ~/.config/opencode/skills/xo_gptes
```

## Uso

```
/xo_gptes caminho/do/arquivo.md
```

O original não é modificado. Os artefatos gerados ficam no mesmo diretório do arquivo:

- `{base}_rev{N}{ext}` — texto revisado
- `{base}_rev{N}_report.md` — substituições aplicadas, flags e score (`baixo` / `médio` / `alto`)

## Via CLI

```
python3 xo_gptes/run.py <arquivo> --model <model-id>
```

## Como funciona

A skill opera em duas camadas independentes.

A primeira usa expressões regulares para detectar padrões objetivos e localizados: palavras
e expressões típicas de IA ("vale ressaltar", "de certa forma", "é importante destacar",
"robusto", "holístico", "transformador"...), travessão usado indevidamente em texto corrido,
abertura de parágrafo com gancho dramático seguido de explicação, contrastivos em excesso e
blocos de bullet onde o texto pede prosa. Quando encontra um padrão com substituição mapeada,
aplica diretamente no arquivo revisado.

A segunda camada envia o texto completo a um LLM e analisa o que a regex não alcança:
estrutura geral de resposta de chatbot, acúmulo de linguagem de ressalva ao longo do texto,
ausência de voz ativa, tom artificialmente uniforme do início ao fim, e uso de vocabulário
sofisticado sem conteúdo concreto por trás. Essa camada não altera o texto; registra as
ocorrências no relatório para revisão manual do autor.