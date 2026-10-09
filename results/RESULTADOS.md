# Resultados preliminares — piloto

> **Status (08/10/2026): PENDENTE — piloto real ainda não rodado.**
> As saídas em `results/mock/` são do modo `--mock`
> (DADOS SINTÉTICOS, carimbados nas figuras) e **não** devem ser apresentados.
> Preencher as seções abaixo só com números de `results/runs/<pasta>/processed/` após a
> coleta real.

## Configuração do piloto

| Item | Valor |
|---|---|
| Comando | `python run.py --nome piloto --models <modelo> --props P1 P2 P3 --reps 3` |
| Pasta da execução | `results/runs/<data-hora>_piloto/` _(preencher)_ |
| Modelo | _preencher_ (ex.: `claude` → `claude-sonnet-5-5`) |
| Propostas | _preencher_ (mín. 3 — Friedman exige ≥ 3 blocos) |
| Autores | todos os 12 de `data/authors.yaml` |
| Repetições (N) | 3 |
| Medidas | pysentimiento (sentimento) e Jev (postura), analisadas lado a lado |
| Data da coleta | _preencher_ |
| Respostas coletadas / recusas / erros | _preencher_ (saída do `score.py`) |

## Δ médio por categoria de autor (vs. controle sem autor)

Fonte: `<pasta>/processed/delta_vs_neutro.csv` (média por categoria).

| Categoria | Δ pysent | Δ Jev |
|---|---|---|
| politico | | |
| ceo | | |
| ficticio | | |
| ficticio_rotulado | | |

**Controle de reputação** (político real − fictício rotulado, mesmo espectro):

| Espectro | pysent | Jev |
|---|---|---|
| esquerda | | |
| direita | | |

## Teste de invariância (Friedman) por modelo

Fonte: `<pasta>/processed/teste_invariancia.csv`.

| Medida | Modelo | n propostas | n condições | χ² | p | Invariante (p > 0,05)? |
|---|---|---|---|---|---|---|
| pysent | | | | | | |
| jev | | | | | | |

## Interpretação

_2–3 frases após os dados._ Lembrete: com 3 propostas o teste tem baixo poder;
p > 0,05 significa "não detectamos efeito no piloto", não "o guardrail é
invariante".

## Figuras

Em `<pasta>/figures/`, para cada medida `M` ∈ {pysent, jev}:

- `barras_por_autor_<M>.png` — nota média por autor
- `heatmap_proposta_autor_<M>.png` — proposta × autor
- `delta_por_categoria_<M>.png` — Δ vs. controle por categoria
