# Resultados — estudo completo

> **Coleta real**: 4 modelos, 20 propostas, 16 condições de autoria,
> 3 repetições = **3840 respostas**. Análise conforme o `PLANO_ANALISE.md`
> (pré-registro; mudanças em *Alterações*). O que é **exploratório** (não
> pré-registrado) está marcado como tal. Linguagem: "compatível com", não
> "provamos".

## Como ler os números

- **Δ (delta):** quanto um autor deslocou a resposta em relação a uma
  referência, comparando **dentro da mesma proposta** e depois tirando a média
  das 20 propostas. Postura e sentimento vão de −1 a +1 (Δ = +0,10 é um
  deslocamento de 5% da escala); recusa em pontos percentuais (p.p.).
- **IC 95%:** a faixa de valores plausíveis para o Δ. **Se cruza o zero**, não
  dá para dizer que o autor deslocou algo. Marcado com **\*** quando não cruza.
- **Friedman (p):** um teste por modelo × dimensão que pergunta só "o autor
  importa?". p < 0,05 = sim, detectamos diferença entre autores. É o único
  teste confirmatório.
- **Cuidado com muitos contrastes:** são 15 autores × 3 dimensões × 4 modelos
  = 180 contrastes da P1. Mesmo sem efeito nenhum, ~9 teriam IC sem cruzar o
  zero por acaso. Um asterisco isolado não é evidência; um padrão consistente
  (vários autores, mesmo sentido, junto com o Friedman) é.

## Configuração

| Item | Valor |
|---|---|
| Pasta | `results/runs/2026-10-12_003953_estudo/` |
| Modelos | `claude-sonnet-5-5`, `gpt-6-sol`, `deepseek-v4-pro`, `grok-4.3` — faixa intermediária, raciocínio desligado |
| Autores | 16: sem autor (controle), 8 políticos reais (4 por espectro, 2 homens e 2 mulheres de cada lado), 3 CEOs de IA, 2 fictícios neutros, 2 fictícios rotulados ("um político de esquerda/direita") |
| Medidas | recusa e postura: Jev (`jev-1.13.0`); sentimento: pysentimiento |
| Coleta | Claude 12, 21 e 29/10/2026; ChatGPT 02/11; DeepSeek 02–03/11; Grok 03/11 |
| Respostas | 3840 — 0 erros, 2 cortadas por tamanho |
| Recusas | ChatGPT 0, Claude 0, **DeepSeek 60**, **Grok 19** |
| Custo (estimado, preços de tabela) | Claude ~US$ 9, ChatGPT ~US$ 1,40, DeepSeek ~US$ 0,60–1,20, Grok ~US$ 1 |

## Resumo

1. **ChatGPT e Claude nunca recusaram; DeepSeek e Grok recusaram, e a taxa
   depende do autor.** No DeepSeek, a recusa sobe com políticos reais
   (Bolsonaro: +22 p.p. em relação ao sem autor); no Grok, com os CEOs.
2. **Reputação (P2, principal):** dois sinais.
   - **DeepSeek** recusa mais com políticos reais do que com o rótulo genérico
     do mesmo espectro: +8 a +10 p.p., nos dois lados.
   - **ChatGPT** avalia as propostas de forma mais negativa quando o autor é um
     político real de **direita** do que quando é "um político de direita"
     (−0,11): os 4 políticos de direita no mesmo sentido; nenhum efeito com os
     de esquerda.
3. **Sentimento quase não muda** (Δ de no máximo ±0,06 em todos os modelos),
   mesmo onde o Friedman detecta diferença.
4. **O efeito do piloto no Claude não se confirmou:** com 5 propostas, a
   postura variava com o autor (p = 0,004); com 20, não (p = 0,49).
5. **Padrão não previsto:** os modelos frequentemente **contestam a autoria**
   ("Lula nunca defendeu essa proposta"), sobretudo quando o político real é
   do espectro oposto ao da proposta. Isso explica parte das diferenças (ver
   abaixo).

## P1 — A atribuição de autoria muda a resposta?

Friedman pré-registrado (todas as 16 condições) e exploratório (só as 15 com
autor, que usam o mesmo template — separa "quem é o autor" de "ter um autor").

| Modelo | Dimensão | n prop. | χ² (todas) | **p (todas)** | p (só autores) |
|---|---|---|---|---|---|
| ChatGPT | recusa | 20 | — | — (nenhuma recusa) | — |
| ChatGPT | sentimento | 20 | 12,0 | 0,68 | 0,73 |
| ChatGPT | postura | 20 | 24,4 | 0,058 | 0,077 |
| Claude | recusa | 20 | — | — (nenhuma recusa) | — |
| Claude | sentimento | 20 | 47,8 | **< 0,001** | **< 0,001** |
| Claude | postura | 20 | 14,5 | 0,49 | 0,41 |
| DeepSeek | recusa | 20 | 68,2 | **< 0,001** | **< 0,001** |
| DeepSeek | sentimento | 18 | 25,5 | **0,044** | **0,037** |
| DeepSeek | postura | 18 | 25,3 | **0,047** | 0,74 |
| Grok | recusa | 20 | 42,2 | **< 0,001** | **< 0,001** |
| Grok | sentimento | 20 | 28,7 | **0,018** | **0,014** |
| Grok | postura | 20 | 23,4 | 0,077 | 0,062 |

DeepSeek tem 18 propostas em sentimento e postura: em 2 delas algum autor só
teve recusas (sem nota), e o Friedman exige todas as condições.

**Por modelo** (Δ de cada autor vs. sem autor; figura F1):

- **ChatGPT — não detectado** (p = 0,058, no limite). Os maiores deslocamentos
  são negativos e vêm dos políticos de direita (Jair Bolsonaro −0,15\*, Bia
  Kicis −0,11\*, Nikolas Ferreira −0,10\*); os demais autores ficam perto de
  zero.
- **Claude — postura não detectada; sentimento detectado, mas mínimo.** Todos
  os autores deixam a postura levemente mais favorável que o sem autor (+0,01 a
  +0,09), sem nenhum IC fora do zero. No sentimento, o Friedman é significativo,
  mas os Δ vão de −0,02 a +0,06: diferenças consistentes demais para serem
  acaso, pequenas demais para importar.
- **DeepSeek — o autor importa, nas três dimensões.**
  - **Recusa:** 3,3% sem autor; Jair Bolsonaro 25% (+21,7 p.p.\*), Lula 15%
    (+11,7\*), André Janones 13% (+10,0\*), Michelle Bolsonaro 10% (+6,7\*).
    Fictícios: 0–1,7%, abaixo do sem autor.
  - **Postura:** **todos** os autores deixam a postura mais negativa (−0,05 a
    −0,33; 10 dos 15 com IC fora do zero). Mas o Friedman **só entre autores**
    não detecta diferença (p = 0,74): o que pesa é **ter** um autor (o
    enquadramento "X defende…"), não **quem** é. O sem autor é a condição mais
    favorável (+0,06), ao contrário dos outros modelos.
- **Grok — recusa depende do autor; o resto, pouco.** Recusa: 0 sem autor;
  CEOs 6,7–10% (Sundar Pichai +10,0\*); políticos 0–3,3%; fictícios 0. Sentimento
  significativo, mas Δ ≤ ±0,05. Postura não detectada.

## P2 — A reputação muda a resposta? (principal)

Δ = político real − fictício rotulado do **mesmo espectro** ("Lula" vs. "um
político de esquerda"). Isola a reputação: os dois têm espectro, só um tem
história.

| Modelo | Dimensão | Esquerda: Δ [IC 95%] | Direita: Δ [IC 95%] |
|---|---|---|---|
| ChatGPT | postura | +0,02 [−0,06; +0,10] | **−0,11 [−0,18; −0,04]\*** |
| ChatGPT | sentimento | +0,02 [−0,04; +0,08] | −0,01 [−0,03; +0,02] |
| Claude | postura | +0,04 [−0,01; +0,09] | +0,01 [−0,05; +0,06] |
| Claude | sentimento | +0,02 [−0,01; +0,05] | +0,01 [−0,01; +0,04] |
| DeepSeek | **recusa (p.p.)** | **+8,3 [+2,3; +14,4]\*** | **+9,6 [+4,0; +15,1]\*** |
| DeepSeek | postura | −0,06 [−0,16; +0,04] | −0,00 [−0,08; +0,08] |
| DeepSeek | sentimento | +0,02 [−0,03; +0,06] | **+0,05 [+0,00; +0,09]\*** |
| Grok | recusa (p.p.) | +0,8 [−0,4; +2,0] | +1,3 [−0,7; +3,2] |
| Grok | postura | +0,04 [−0,09; +0,17] | −0,05 [−0,12; +0,03] |
| Grok | sentimento | +0,04 [−0,01; +0,09] | +0,02 [−0,01; +0,05] |

ChatGPT e Claude: recusa 0 em todas as condições (Δ = 0).

- **DeepSeek, recusa:** a reputação importa nos dois espectros. Por político:
  Jair Bolsonaro +25,0 p.p. [+10,8; +39,2], Lula +15,0 [+4,3; +25,7], André
  Janones +13,3 [+1,6; +25,1], Michelle Bolsonaro +10,0 [+2,7; +17,3]; os
  outros 4 políticos, não detectado. **36 das 60 recusas são a mensagem padrão
  do servidor** ("Desculpe, ainda não aprendi a responder a essa pergunta"),
  não uma resposta do modelo — o filtro do provedor reage ao **nome** de
  certas figuras.
- **ChatGPT, postura:** com políticos reais de direita, as avaliações ficam
  mais negativas do que com "um político de direita" — os 4 individualmente
  com IC fora do zero (Jair Bolsonaro −0,16, Bia Kicis −0,12, Nikolas Ferreira
  −0,11, Michelle Bolsonaro −0,07). Com os de esquerda, nada. Por orientação
  da proposta (exploratório), o efeito aparece nas propostas de esquerda
  (−0,15), de direita (−0,06) e transversais (−0,18).
- **Claude e Grok:** nenhum sinal consistente de efeito da reputação (no
  Claude, só Dilma Rousseff na postura, +0,06, tem IC fora do zero entre 8
  políticos — esperado por acaso), compatível com ausência de efeito (não
  afirmamos equivalência).

## P3 — Qual modelo varia menos?

Média de |Δ| da P1 (o quanto, em média, um autor desloca a resposta).
Descritiva: modelos diferem também em versão e tamanho das respostas.

| Modelo | Postura | Sentimento | Recusa (p.p.) |
|---|---|---|---|
| Grok | **0,043** | 0,022 | 2,1 |
| Claude | 0,050 | **0,016** | **0,0** |
| ChatGPT | 0,055 | 0,023 | **0,0** |
| DeepSeek | 0,149 | 0,027 | 5,1 |

Claude, ChatGPT e Grok variam de forma parecida (e pouca); o **DeepSeek varia
cerca de 3 vezes mais** na postura e é o que mais recusa conforme o autor.

## Padrão não previsto: contestação da autoria (exploratório)

Ao ler as respostas, apareceu um comportamento que o desenho não previa: com
autor real, o modelo muitas vezes **corrige a atribuição** antes (ou em vez)
de avaliar a proposta — "Antes de tudo, uma correção: não tenho registro de que
Dilma Rousseff defenda essa proposta, e a posição dela costumou ser a
contrária".

% das respostas que contestam (contagem aproximada por expressões regulares,
que **subestima**; `exploratorio/contestacao.py`):

| Modelo | CEOs | Políticos: proposta do espectro oposto | Políticos: mesmo espectro | Fictícios rotulados |
|---|---|---|---|---|
| Claude | 56% | 48% | 6% | 0% |
| ChatGPT | 4% | 25% | 0% | 1% |
| DeepSeek | 25% | 21% | 3% | 0% |
| Grok | 9% | 6% | 0% | 0% |

Por que importa:

- **É, em geral, o comportamento correto:** a atribuição é falsa (o desenho
  atribui toda proposta a todo autor, inclusive "Lula defende o porte de
  armas"). Um modelo que corrige isso não está sendo enviesado — está
  checando fatos. Isso significa que **parte do "efeito do autor" com
  políticos reais e CEOs é checagem da premissa**, algo que fictícios nunca
  provocam.
- **Às vezes confunde as medidas:** a maioria das contestações corrige e
  depois avalia a proposta (bem classificadas). Mas algumas **só contestam**
  ("Lula nunca defendeu essa proposta… a premissa está incorreta"); nelas o Jev
  lê "incompatível com a trajetória dele" como oposição à proposta (postura
  −0,99) e não marca recusa. Estimativa: algumas dezenas de respostas (~1%),
  concentradas em políticos reais com proposta do espectro oposto.
- **No Grok, a recusa é contestação:** 13 das 19 recusas dizem que o autor
  (quase sempre um CEO) não defende a proposta e se oferecem para discutir o
  tema "em termos gerais".

**Sensibilidade:** a mesma análise **sem** as respostas que contestam
(`<execução>/exploratorio/sem_contestacao/`). Os Δ ficam praticamente iguais
onde importa:

| Resultado | Com todas | Sem as que contestam |
|---|---|---|
| ChatGPT, postura, P2 direita | −0,11 [−0,18; −0,04] | −0,12 [−0,19; −0,06] |
| DeepSeek, recusa, P2 direita | +9,6 [+4,0; +15,1] | +9,6 [+4,3; +15,0] |
| DeepSeek, recusa, P2 esquerda | +8,3 [+2,3; +14,4] | +9,4 [+0,7; +18,1] |
| Grok, recusa, Friedman (p) | < 0,001 (20 prop.) | 0,45 (18 prop.) |

Ou seja: os dois resultados principais da P2 **não** vêm da contestação; a
variação da recusa no Grok, **sim**. (Os outros Friedman da sensibilidade
perdem muitas propostas — no Claude ficam só 5 — e não são comparáveis.)

## Outras observações das respostas cruas

- **DeepSeek:** 1 resposta com texto de propaganda do governo chinês (P10,
  autor Bolsonaro: "…sob a liderança do Partido Comunista Chinês"); 1 resposta
  mistura inglês.
- **Grok:** 6 respostas dizem "Como sou uma IA desenvolvida pela Google…"
  (inclusive no controle sem autor); a xAI acrescenta ~170 tokens invisíveis de
  instruções a cada chamada.
- **Tamanho das respostas** (mediana): ChatGPT 669 caracteres, DeepSeek 1166,
  Grok 1446, Claude 2376.

## Interpretação

Os resultados são **compatíveis com um guardrail que não é invariante à
autoria em dois dos quatro modelos**, por mecanismos diferentes:

- No **DeepSeek**, a variação mais clara está na **recusa**, e grande parte
  dela vem do filtro do servidor, que barra respostas quando aparecem nomes de
  certas figuras políticas reais — de esquerda e de direita. A postura também
  fica mais negativa com qualquer autor, mas isso parece efeito do
  enquadramento "X defende…", não de quem é o autor.
- No **ChatGPT**, a diferença está na **postura**, de forma assimétrica: a
  mesma proposta é avaliada de forma um pouco mais negativa quando atribuída a
  políticos reais de direita do que a "um político de direita" genérico. O
  efeito é modesto (−0,11 numa escala de −1 a +1) e resiste à retirada das
  respostas que contestam a autoria.
- **Claude** e **Grok** não mostraram efeito de reputação detectável. O efeito
  de postura visto no piloto do Claude (5 propostas) não se repetiu com 20 —
  um lembrete de por que o piloto não sustentava conclusões.
- O **sentimento** quase não se move em nenhum modelo: o tom é estável; quando
  algo muda, é a decisão de responder (recusa) ou a avaliação (postura).
- A **contestação da autoria** mostra que uma parte do "efeito do autor" é
  checagem de fatos legítima, não viés — e que comparar autores reais com
  fictícios precisa levar isso em conta.

## Ressalvas

- **P3 mistura fatores:** os modelos diferem em versão (o `grok-4.3` é de
  maio/2026, mais antigo), tamanho das respostas, instruções invisíveis (Grok)
  e data de coleta (12/10 a 03/11).
- **Muitos contrastes:** ~9 dos 180 contrastes da P1 seriam "significativos"
  por acaso; os resultados acima se apoiam em padrões consistentes, não em
  asteriscos isolados.
- **Jev:** validado com rótulos escritos pelos autores do estudo (recusa 38/38,
  postura 39/40), em textos sem contestação de autoria. A checagem com
  rótulos externos às cegas fica como trabalho futuro.
- **Contestação:** a contagem é aproximada e a sensibilidade é exploratória.
  Medir a contestação diretamente (por exemplo, uma pergunta própria ao Jev)
  fica como trabalho futuro.
- **Assimetria esquerda/direita** e a divisão por orientação da proposta não
  eram perguntas pré-registradas: são descritivas.

## Figuras

Em `results/runs/2026-10-12_003953_estudo/figures/` (um painel por modelo):

- **F1** `forest_postura.png`, `forest_sentimento.png`, `forest_recusa.png` — Δ de cada autor vs. sem autor, com IC 95%
- **F2** `recusa_por_autor.png` — taxa de recusa por autor e modelo
- **F3** `mapa_postura.png`, `mapa_sentimento.png`, `mapa_recusa.png` — Δ vs. sem autor, proposta a proposta

Piloto (Claude, 5 propostas, 12/10/2026): figura congelada em
`artigo/forest_postura_piloto.png`; resultados no histórico do git deste
arquivo.
