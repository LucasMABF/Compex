## Contexto

Esse é o projeto da disciplina de Computação Experimental. Nossa pesquisa é uma
**auditoria experimental da robustez do guardrail de neutralidade de LLMs**.

**RQ:** *O guardrail de neutralidade de um LLM é invariante à autoria atribuída
a uma proposta política (real vs. fictício)?*

Medimos, de forma quantitativa e reproduzível, se a **resposta** de um LLM a uma
**proposta política** muda conforme a **autoria atribuída** (autor real × autor
fictício × sem autor), em três dimensões:

- **Recusa** — o modelo se nega a opinar mais para certos autores? (NLI +
  bloqueio do provedor + resposta vazia)
- **Sentimento** — o tom da resposta muda? (pysentimiento)
- **Postura** — a avaliação da proposta muda? (NLI)

O guardrail é invariante se **nenhuma** dimensão muda com o autor. Se alguma
muda só porque o autor mudou, isso é um resultado de segurança/alinhamento, não
uma opinião política. O **Jev** (TypeSafe) também é rodado como teste
exploratório de postura: fica no repositório, mas não sustenta as conclusões.

Desenho: **experimento fatorial, within-item** (a mesma proposta passa por
todas as condições; só a autoria muda), fatores **autoria × modelo**, com `N`
repetições por célula, na temperatura padrão de cada provedor. Condição de
**controle** = proposta sem autor.

A entrega desta semana é a de **execução**: preciso ter **evidências reais
preliminares** (dados coletados + gráficos) para mostrar, além de registrar
dificuldades e ajustes.

## O que você deve fazer

1. **Revisar o scaffold** (`config.yaml`, `data/`, `src/`, `collect.py`,
   `score.py`, `analyze.py`, `plot.py`, `run.py`) e garantir que roda ponta a
   ponta em modo mock: `python run.py --mock` deve gerar, em `results/mock/`,
   os CSVs e as 3 figuras por medida (pysentimiento e Jev).

DEFERIR, EU QUERO FAZER EU MESMO. EU QUE MEXO COM API KEYS
2. **Ligar as APIs reais** (`src/providers.py`): OpenAI, Anthropic e Google.
   Ler chaves do `.env`. Implementar: timeout, *retry* com *backoff* em erro de
   rede/rate-limit, e registro de erro por célula (nunca derrubar a coleta
   inteira). Confirmar os nomes de modelo em `MODELOS_REAIS`.

3. **Análise de sentimento em português.** Medida de sentimento:
   **pysentimiento** (transformer PT, local; substituiu o LeIA, que acertou
   5/12 num teste de sanidade contra 9/12). Postura: **NLI** zero-shot
   (mDeBERTa-v3 multilíngue, 11/12 no mesmo teste). Contraste: **Jev**
   (TypeSafe System One, escolha do grupo). Lista em `medidas` no `config.yaml`.

4. **Rodar um piloto real pequeno** para a entrega: 2–3 propostas, todos os
   autores, 1 modelo, `N=3`. Salvar os dados crus e gerar os gráficos. Conferir
   que recusas do modelo são marcadas (`recusa=True`) e **excluídas** da nota.

5. **Gerar um resumo dos resultados preliminares** em `results/RESULTADOS.md`:
   o Δ médio por categoria de autor, o resultado do teste de Friedman por
   modelo, e 2–3 frases interpretando (o guardrail se mostrou invariante ou
   não, nesse piloto). Incluir os caminhos das figuras.

6. **Registrar dificuldades e ajustes** num `results/NOTAS_EXECUCAO.md`
   (ex.: recusas frequentes, limites de rate, custo, ajustes de template).

## Regras importantes

- **Não invente dados.** O modo `--mock` é só para validar o pipeline; rotule
  qualquer figura/saída de mock como sintética. Resultados apresentados devem
  vir de coleta real.
- Mantenha a **proposta idêntica entre condições** — só a autoria varia.
- Mantenha tudo **configurável por arquivo** (`config.yaml`, `data/*.yaml`); não
  "hard-code" propostas, autores nem parâmetros no código.
- **Não comite** `.env` nem os dados crus (já está no `.gitignore`).
- Scripts pequenos e legíveis, em português, como já estão.
- Controle de reputação: ao analisar, compare político **real** com o fictício
  **rotulado** de mesmo espectro — é o que separa "efeito do nome" de "efeito
  da reputação".

## Pronto quando

- [ ] `python run.py --mock` roda limpo e gera CSVs + 3 figuras por medida.
- [ ] `python run.py` coleta de verdade com pelo menos 1 API, com retry/erros tratados.
- [ ] pysentimiento integrado como medida de sentimento (sem fallback silencioso).
- [ ] Piloto real rodado; recusas marcadas e excluídas da nota.
- [ ] `results/RESULTADOS.md` e `results/NOTAS_EXECUCAO.md` escritos.
