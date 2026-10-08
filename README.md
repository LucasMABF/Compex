# Robustez do guardrail de neutralidade em LLMs

Auditoria experimental: **o tom (sentimento) da resposta de um LLM a uma
proposta política muda conforme a autoria atribuída (autor real × fictício ×
sem autor)?** Se mudar, o guardrail de neutralidade não é invariante.

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
  processed/       scored.csv [fora do git] + médias, Δ e Friedman por medida
  figures/         3 figuras por medida (leia, jev)
```

Os passos também rodam isolados sobre uma execução existente
(`score.py`, `analyze.py`, `plot.py`, `ver.py` aceitam `--run <pasta>`;
o padrão é a mais recente, e `--mock` usa `results/mock/`).

## Desenho (resumo)

- **Fatorial, within-item:** a MESMA proposta passa por todas as condições de
  autoria; só a autoria muda. Fatores: autoria × modelo. `N` repetições por célula.
- **Condições de autoria:** `controle` (sem autor), político real, CEO, fictício
  neutro, fictício rotulado por espectro. Editáveis em `data/authors.yaml`.
- **Medidas** (ambas em `[-1, +1]`, analisadas lado a lado): **LeIA** = tom das
  palavras (léxico); **Jev** = postura da resposta frente à proposta (recebe a
  proposta, nunca o autor). Trocáveis no `config.yaml`.
- **Invariância:** Δ vs. controle ≈ 0 e teste de Friedman não significativo.

## Estrutura

```
config.yaml            parâmetros (modelos, N, templates, métrica)
data/proposals.yaml    propostas P1..P8 (editável)
data/authors.yaml      autores por categoria/espectro (editável)
src/prompts.py         monta o prompt (autor, proposta)
src/providers.py       APIs (OpenAI/Anthropic/Google) + MOCK
src/sentiment.py       medidas plugáveis (leia/jev/lexico_pt/pysent/llm)
src/loader.py          config/dados e pastas de execução
collect.py             roda o grid -> raw/responses.jsonl + raw/coleta.log
score.py               aplica as medidas -> processed/scored.csv
analyze.py             médias, Δ vs. controle, Friedman por medida -> processed/*.csv
plot.py                3 figuras por medida -> figures/
run.py                 pipeline completo numa pasta nova
ver.py                 lê as respostas de uma execução (depuração)
```

> **Aviso:** o modo `--mock` produz texto **sintético** só para demonstrar o
> pipeline. Não são resultados reais e não devem ser apresentados como tal.
