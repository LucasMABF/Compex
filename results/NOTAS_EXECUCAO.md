# Notas de execução — dificuldades e ajustes

## 08/10/2026 — revisão do scaffold

### Problemas encontrados e corrigidos

- **Resultados commitados eram sintéticos.** Os CSVs/figuras do commit inicial
  vinham do `--mock` (respostas `[MOCK] ...`, com viés por espectro injetado
  de propósito no gerador) e estavam desatualizados (10 autores; o
  `authors.yaml` tem 12). Foram removidos do git; figuras de mock agora saem
  carimbadas "DADOS SINTÉTICOS".
- **LeIA não carregava.** O pacote correto é `leia-br` (`from LeIA import ...`);
  existe um pacote `leia` no PyPI que é outra coisa. Corrigido em
  `src/sentiment.py` e `requirements.txt`; LeIA virou o primário.
- **Temperatura removida.** A coleta rodava 0.0 e 0.7, mas a análise
  misturava as duas; além disso os modelos atuais recusam ou ignoram o
  parâmetro. Agora todos rodam na temperatura padrão do provedor.
- **Sem log de coleta.** Agora cada chamada vai para `raw/coleta.log`
  (tempo, tamanho, recusa/vazia, erro completo) e `ver.py` mostra os textos.
- **Execuções se sobrescreviam e o mock caía junto com os dados reais.** Agora
  cada execução real tem sua pasta (`results/runs/<data-hora>_<nome>/`) com
  cópia do config, `metadata.json` (commit do código, modelos, argumentos),
  dados crus, CSVs e figuras; o mock vai para `results/mock/` (fora do git).
- **O Jev era chamado mas não analisado.** `analyze.py`/`plot.py` agora rodam
  para cada medida (coluna `medida` nos CSVs, figuras `*_<medida>.png`). O Jev
  recebe a proposta junto com a resposta (sem o autor), não é chamado para
  recusas/erros, e uma falha dele numa resposta deixa a nota vazia (antes
  virava 0 ou derrubava a pontuação).
- **Erros de API viravam nota de sentimento.** A string `[ERRO] ...` era
  pontuada como resposta. Agora o erro vai para o campo `erro` e a linha é
  excluída da nota (como as recusas).
- **Nomes de modelo desatualizados.** `gpt-4o-mini`, `claude-3-5-sonnet-20241022`
  e `gemini-1.5-flash` → `gpt-6-luna`, `claude-sonnet-5-5`, `gemini-3.8-flash`.
  SDK do Google migrado de `google-generativeai` (legado) para `google-genai`.
  OpenAI: `max_tokens` → `max_completion_tokens` (o antigo dá 400 nos gpt-6).
- **Faltavam `.gitignore` e `.env.example`** (citados no README/CLAUDE.md).
- **Piloto pela linha de comando:** `run.py` agora aceita `--models` e `--props`.

### 09/10/2026 — corte de respostas e custo

- **`max_tokens: 400` cortava respostas no meio** sem que soubéssemos. O teto
  virou 1500 (é só segurança — paga-se o que é gerado, não o teto) e cada
  resposta agora registra `parada` (`fim` / `limite` / `bloqueio`), `cortada`
  e os tokens de entrada/saída. Cortes aparecem no log (`CORTADA`) e em
  `ver.py --cortadas`. Na análise: reportar a taxa de corte por condição e
  refazer sem as cortadas (sensibilidade) — a implementar.
- **Bloqueio do provedor conta como recusa.** Quando o filtro de segurança
  da API barra a resposta (`refusal` / `content_filter` / `SAFETY`), a
  resposta é marcada `recusa=True`, além da lista de expressões.
- **Versões dos pacotes fixadas** em `requirements.txt` (reprodutibilidade).
- **Brevidade** só é controlável pelo prompt (não há parâmetro comum aos três
  provedores); decidir depois de ler as primeiras respostas reais, mantendo o
  texto igual em todas as condições.

### Limitações / pontos de método em aberto

- **Templates diferem além do nome.** O controle não tem o "X *defende* a
  seguinte proposta". Esse enquadramento pode mudar o tom por si só; os
  fictícios neutros são uma comparação mais limpa que o "sem autor".
- **Heurística de recusa agressiva.** "como uma ia" / "não tenho opiniões"
  costumam preceder uma análise completa; podem descartar respostas válidas.
  Revisar recusas à mão no piloto.
- **Léxico do LeIA tem lacunas** ("positiva", "justa", "benéfica" valem 0) e
  mede tom das palavras, não posição sobre a proposta — daí o Jev como contraste.
- **Raciocínio ("thinking") no mínimo nos três**, para respostas diretas e
  comparáveis e para não gastar o `max_tokens` com raciocínio:
  OpenAI `reasoning_effort="none"`, Claude `thinking: between_tools`,
  Gemini `thinking_level=LOW` (o 3.8-flash não aceita `minimal`).
- **Poder estatístico:** Friedman com 3 propostas tem baixo poder.

## Piloto real

_A preencher: data, modelo, custo, rate limits, nº de recusas/erros, ajustes._
