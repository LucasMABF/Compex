# Resultados preliminares — piloto

> **Piloto real** (1 modelo, 5 das 20 propostas). Serve para validar o pipeline
> e a direção dos efeitos; **não sustenta conclusões** — essas virão do estudo
> completo (20 propostas, 3 modelos), que complementa esta mesma execução.
> Análise conforme `PLANO_ANALISE.md` (pré-registro). Com 5 propostas,
> *p > 0,05* significa "não detectado", não "invariante".

## Configuração

| Item | Valor |
|---|---|
| Comando | `python run.py --nome estudo --models claude --props P1 P6 P9 P14 P18 --reps 3` |
| Pasta da execução | `results/runs/2026-10-12_003953_estudo/` |
| Modelo | `claude` → `claude-sonnet-5-5` |
| Propostas | P1 (taxação de fortunas), P6 (porte de armas), P9 (fim da propriedade privada dos meios de produção), P14 (anistia ao 8 de janeiro), P18 (imposto sobre substituição de trabalhadores por IA) |
| Autores | 16 (`data/authors.yaml`): sem autor, 8 políticos reais (4 por espectro), 3 CEOs, 2 fictícios neutros, 2 fictícios rotulados |
| Repetições (N) | 3 |
| Medidas | recusa e postura: Jev (`jev-1.13.0`); sentimento: pysentimiento |
| Data da coleta | 12/10/2026 |
| Respostas | 240 — 0 erros, 0 recusas, 1 recusa incerta, 0 cortadas |
| Tokens / custo | entrada 18.588, saída 215.479 (~900 por resposta) — ~US$ 2,19 |

## P1 — A atribuição de autoria muda a resposta?

Fonte: `friedman.csv` e `contrastes.csv` (P1: Δ de cada autor vs. sem autor).

| Dimensão | n propostas | χ² | p |
|---|---|---|---|
| Recusa | 5 | — | — (nenhuma recusa: sem variação) |
| Sentimento | 5 | 18,83 | 0,22 |
| **Postura** | 5 | **33,81** | **0,004** |

- **Postura:** todos os 15 autores deslocam a postura no mesmo sentido —
  **mais favorável** à proposta do que o controle sem autor (Δ de +0,02 a
  +0,25). A sem autor é a condição mais negativa (média −0,36).
  - Fictícios (neutros e rotulados): Δ pequenos, +0,02 a +0,11, todos com IC
    cruzando o zero.
  - CEOs: +0,18 a +0,25, ICs **sem** cruzar o zero.
  - Políticos reais: +0,02 a +0,20; só Lula com IC sem cruzar o zero (+0,16;
    IC 95% +0,03 a +0,28) — entre 15 contrastes, um assim é esperado por acaso.
- **Sentimento:** deslocamentos mínimos (−0,06 a +0,04), todos com IC
  cruzando o zero.
- **Controle do template:** os fictícios neutros (Marcos, Helena) deslocam
  pouco (postura +0,05 e +0,06, ICs cruzando o zero), mas o Friedman inclui a
  condição sem autor, que usa outro template ("Qual a sua opinião sobre..." vs.
  "X defende..."). Parte do efeito detectado pode vir do enquadramento, não da
  identidade do autor.

## P2 — A reputação muda a resposta? (principal)

Fonte: `contrastes.csv` (P2). Δ = político real − fictício rotulado do mesmo
espectro.

| Dimensão | Contraste | Δ | IC 95% | IC cruza o zero? |
|---|---|---|---|---|
| Postura | políticos de esquerda − "um político de esquerda" | +0,089 | −0,084 a +0,261 | sim |
| Postura | políticos de direita − "um político de direita" | +0,010 | −0,070 a +0,090 | sim |
| Sentimento | políticos de esquerda − rotulado | −0,016 | −0,070 a +0,039 | sim |
| Sentimento | políticos de direita − rotulado | +0,007 | −0,067 a +0,080 | sim |
| Recusa (p.p.) | ambos os espectros | 0,0 | — | (nenhuma recusa) |

Por político, só Lula − rotulado de esquerda na postura tem IC sem cruzar o
zero (+0,13; IC +0,02 a +0,24). Nenhum sinal consistente de efeito da
reputação além do rótulo de espectro. **Um resultado nulo na P2 é um desfecho
válido** (compatível com ausência de efeito de reputação), não uma falha: é o
contraste mais fino do estudo e pode permanecer "não detectado" no estudo
completo.

## P3 — Qual modelo varia menos?

Não se aplica ao piloto (1 modelo). Referência para o estudo completo: média
de |Δ| da P1 no Claude = 0,12 (postura), 0,03 (sentimento), 0 (recusa).

## Interpretação

No piloto, a postura do Claude **não foi invariante à atribuição de autoria**:
apresentar a proposta como defendida por alguém a tornou mais favorável, com
deslocamentos maiores para figuras reais conhecidas (CEOs, ex-presidentes) do
que para nomes fictícios. Os deslocamentos são modestos (até ~0,25 numa escala
de −1 a +1) e **não há sinal de efeito da reputação** além do rótulo de
espectro (P2 com ICs cruzando o zero), padrão compatível com um guardrail
robusto à reputação, mas sensível ao enquadramento de autoria. Sentimento não
variou de forma detectável e não houve recusas. Com 1 modelo e 5 propostas,
são indícios a confirmar, não conclusões.

## Ressalvas

- **Tamanho:** 1 modelo, 5 propostas; ICs largos.
- **Template:** o controle sem autor usa outro template; o Friedman da P1 mistura
  efeito de atribuição e de enquadramento.
- **Jev mede recusa e postura:** a validação (recusa 38/38, postura 39/40) usa
  rótulos escritos pelos autores do estudo, não independentes. Uma checagem
  com rótulos externos às cegas está prevista para o estudo completo.
- **Recusas:** nenhuma no Claude — a dimensão recusa só será informativa se os
  outros modelos recusarem.

## Figuras

Em `results/runs/2026-10-12_003953_estudo/figures/`:

- **F1** `forest_postura.png`, `forest_sentimento.png`, `forest_recusa.png` — Δ de cada autor vs. sem autor, com IC 95%
- **F2** `recusa_por_autor.png` — taxa de recusa por autor (vazia: nenhuma recusa)
- **F3** `mapa_postura.png`, `mapa_sentimento.png`, `mapa_recusa.png` — Δ vs. sem autor, proposta a proposta
