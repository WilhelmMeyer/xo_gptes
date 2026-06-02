# Léxico GPTês — pt-BR

Formato: `padrão (regex) | tipo | sugestão`

| Padrão | Tipo | Sugestão |
|--------|------|----------|
| `[Éé] crucial` | léxico | substituir por "é necessário" |
| `[Éé] fundamental` | léxico | eliminar ou especificar |
| `[Vv]ale ressaltar` | hedging | eliminar |
| `[Vv]ale destacar` | hedging | eliminar |
| `[Éé] importante (notar\|destacar\|ressaltar)` | hedging | eliminar |
| `[Dd]e certa forma` | hedging | eliminar |
| `[Dd]e alguma maneira` | hedging | eliminar |
| `[Ee]m certa medida` | hedging | eliminar |
| `[Nn]o contexto (de\|do\|da)` | estrutural | reformular entrada do parágrafo |
| `[Aa]o longo (de\|do\|da\|dos\|das)` | léxico | avaliar necessidade |
| `[Ii]ntrinsecamente` | léxico | especificar |
| `[Ff]undamental(mente)?` | léxico | revisar necessidade |
| `[Aa]bordagem abrangente` | léxico | especificar abrangência |
| `[Ee]xplorando\b` | léxico | substituir por verbo concreto (analisar, descrever) |
| `[Ee]mbarcando em` | léxico | substituir por "iniciando", "começando" |
| `[Tt]apestry\|[Tt]apeçaria de` | léxico | reformular com conexão explícita |
| `[Nn]uançado\|[Nn]uances de` | léxico | especificar qual nuance |
| `[Rr]obust[ao]` | léxico | especificar |
| `[Ss]inergias?\b` | léxico | eliminar ou especificar |
| `— [a-záéíóúâêîôûãõü]` | travessão interno | substituir por vírgula ou ponto |
| `[a-záéíóú] —` | travessão interno | substituir por vírgula ou ponto |
| `[Pp]rofundo impacto` | léxico | especificar o impacto |
| `[Tt]ransformador(a)?` | léxico | especificar o que transforma |
| `[Rr]evolucionário` | léxico | especificar em que sentido |
| `[Pp]aradigma` | léxico | especificar |
| `[Ee]cossistema de` | léxico | especificar componentes |
| `[Hh]olístic[ao]` | léxico | especificar abrangência |
| `[Cc]ada vez mais` | léxico | quantificar ou cortar |
| `[Ss]em sombra de dúvida` | hedging | cortar |
| `[Ii]ndubitavelmente` | hedging | cortar |
| `[Cc]abe (destacar\|ressaltar\|notar)` | hedging | eliminar |