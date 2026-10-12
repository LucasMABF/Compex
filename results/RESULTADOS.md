# Resultados preliminares — piloto

> **Status: PENDENTE — piloto real ainda não rodado.**
> As saídas em `results/mock/` são do modo `--mock` (DADOS SINTÉTICOS,
> carimbados nas figuras) e **não** devem ser apresentadas. Preencher as seções
> abaixo só com números de `results/runs/<pasta>/processed/` após a coleta real.
> Análise conforme `PLANO_ANALISE.md`.

## Configuração do piloto

| Item | Valor |
|---|---|
| Comando | `python run.py --nome piloto --models <modelo> --props <ids> --reps 3` |
| Pasta da execução | `results/runs/<data-hora>_piloto/` _(preencher)_ |
| Modelo | _preencher_ (ex.: `claude` → `claude-sonnet-5-5`) |
| Propostas | _preencher_ (mín. 3 — o Friedman exige ≥ 3 propostas completas) |
| Autores | todos os de `data/authors.yaml` |
| Repetições (N) | 3 |
| Medidas | recusa e postura: Jev; sentimento: pysentimiento |
| Data da coleta | _preencher_ |
| Respostas / recusas / erros | _preencher_ (saída do `score.py`) |

## P1 — O autor importa?

Fonte: `friedman.csv` (um teste por modelo × dimensão) e `contrastes.csv`
(pergunta P1: Δ de cada autor vs. sem autor, IC 95%).

| Modelo | Dimensão | n propostas | χ² | p |
|---|---|---|---|---|
| | recusa | | | |
| | sentimento | | | |
| | postura | | | |

Fictícios neutros vs. sem autor (efeito do template): _preencher_.

## P2 — A reputação importa? (principal)

Fonte: `contrastes.csv` (pergunta P2, linhas "políticos de <espectro> − <rotulado>").

| Modelo | Dimensão | Contraste | Δ | IC 95% | IC cruza o zero? |
|---|---|---|---|---|---|
| | sentimento | políticos de esquerda − fic_esq | | | |
| | sentimento | políticos de direita − fic_dir | | | |
| | postura | políticos de esquerda − fic_esq | | | |
| | postura | políticos de direita − fic_dir | | | |
| | recusa (p.p.) | políticos de esquerda − fic_esq | | | |
| | recusa (p.p.) | políticos de direita − fic_dir | | | |

## P3 — Qual modelo varia menos? (descritiva)

Fonte: `variacao_modelos.csv` (média de |Δ| da P1). _Só com mais de um modelo._

## Interpretação

_2–3 frases após os dados, com linguagem modesta:_ ex.: "os deslocamentos
foram pequenos e os intervalos de confiança cruzam o zero, compatível com um
guardrail robusto; não afirmamos equivalência estatística formal". Com poucas
propostas, p > 0,05 significa "não detectado", não "invariante".

## Figuras

Em `<pasta>/figures/`:

- **F1** `forest_<dimensao>.png` — Δ de cada autor vs. sem autor, com IC 95%
- **F2** `recusa_por_autor.png` — taxa de recusa por autor
- **F3** `mapa_<dimensao>.png` — Δ vs. sem autor, proposta a proposta
