# Robustez do guardrail de neutralidade em LLMs

Auditoria experimental. **RQ:** *O guardrail de neutralidade de um LLM é
invariante à autoria atribuída a uma proposta política (real vs. fictício)?*

A mesma proposta é apresentada sem autor, com autores reais e com autores
fictícios, e a resposta do modelo é medida em três dimensões — **recusa**,
**sentimento** e **postura**. O guardrail é invariante se nenhuma muda com o
autor.

Projeto da disciplina CIC0203 (Computação Experimental) — Grupo 3.

## Como rodar

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt

# DEMO sem chaves de API (dados sintéticos só p/ validar o pipeline):
.venv/bin/python run.py --mock                  # -> results/mock/

# Coleta REAL (precisa de chaves em .env — veja .env.example):
cp .env.example .env     # preencha as chaves
.venv/bin/python run.py --nome piloto --models claude --props P1 P2 P3 --reps 3
.venv/bin/python run.py --nome completo         # tudo o que está no config

# Ler as respostas coletadas (execução mais recente):
.venv/bin/python ver.py                         # resumo
.venv/bin/python ver.py --modelo claude --prop P1 --autor pol_dir_1
```

Sem flags, `run.py` usa todas as propostas, os modelos e as repetições do
`config.yaml`. Cada execução real ganha uma pasta própria — nada é sobrescrito:

```
results/runs/<data-hora>_<nome>/
  config/          cópia do config.yaml e data/*.yaml usados
  metadata.json    quando, commit do código, modelos, argumentos
  raw/             responses.jsonl (respostas) + coleta.log (execução)   [fora do git]
  processed/       scored.csv [fora do git] + médias, Δ, contrastes e Friedman
  figures/         F1 forest plot e F3 mapa por dimensão, F2 taxa de recusa
```

Os passos também rodam isolados sobre uma execução existente
(`score.py`, `analyze.py`, `plot.py`, `ver.py` aceitam `--run <pasta>`;
o padrão é a mais recente, e `--mock` usa `results/mock/`).

## Desenho (resumo)

- **Fatorial, within-item:** a MESMA proposta passa por todas as condições de
  autoria; só a autoria muda. Fatores: autoria × modelo. `N` repetições por célula.
- **Condições de autoria:** `controle` (sem autor), político real, CEO, fictício
  neutro, fictício rotulado por espectro. Editáveis em `data/authors.yaml`.
- **Dimensões da resposta:**
  - **recusa** — classificada no `score.py` a partir do texto salvo: bloqueio do
    provedor, resposta vazia ou o **Jev** julgando que a resposta não se engaja
    com a proposta (probabilidade e motivo gravados; casos perto do limiar
    marcados como incertos — `ver.py --incertas`);
  - **sentimento** — **pysentimiento** (transformer PT, local; respostas longas
    divididas em trechos), em `[-1, +1]`;
  - **postura** — **Jev** (escala de 5 níveis, com probabilidades e confiança),
    em `[-1, +1]`.

  O Jev (TypeSafe System One) responde recusa e postura numa só chamada por
  resposta; recebe a proposta, nunca o autor; versão fixada no `config.yaml`.
  Se o Jev ou o pysentimiento falharem ao carregar, a pontuação para.
  Escolhas validadas antes da coleta: `python validacao/validar.py`.
- **Análise** (`PLANO_ANALISE.md`, pré-registro): Δ dentro de cada proposta,
  IC 95% pela distribuição *t* e um teste de Friedman por modelo × dimensão.
  Perguntas: P1 o autor importa?, P2 (principal) a reputação importa?
  (político real − fictício rotulado do mesmo espectro), P3 qual modelo varia
  menos.

## Estrutura

```
config.yaml            parâmetros (modelos, N, templates, métrica)
data/proposals.yaml    propostas P1..P20, com eixo e orientação (editável)
data/authors.yaml      autores por categoria/espectro (editável)
src/prompts.py         monta o prompt (autor, proposta)
src/providers.py       APIs (OpenAI/Anthropic/Google) + MOCK
src/sentiment.py       medidas: Jev (recusa + postura), pysent (sentimento), lexico_pt
src/loader.py          config/dados e pastas de execução
collect.py             roda o grid -> raw/responses.jsonl + raw/coleta.log (só fatos)
score.py               classifica (erro/recusa) e aplica as medidas -> processed/scored.csv
analyze.py             Δ + IC 95% (t) + Friedman (P1–P3) -> processed/*.csv
plot.py                figuras F1–F3 -> figures/
run.py                 pipeline completo numa pasta nova
ver.py                 lê as respostas de uma execução (depuração)
validacao/             conjuntos de validação das medidas + validar.py
PLANO_ANALISE.md       plano de análise pré-registrado (antes da coleta)
```

> **Aviso:** o modo `--mock` produz texto **sintético** só para demonstrar o
> pipeline. Não são resultados reais e não devem ser apresentados como tal.
