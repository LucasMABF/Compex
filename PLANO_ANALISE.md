# Plano de análise (pré-registro)

> Escrito em **11/10/2026**, **antes** da coleta de dados reais. Mudanças
> posteriores são permitidas, mas devem ser registradas na seção
> [Alterações](#alterações) com data e motivo.

**RQ:** *O guardrail de neutralidade de um LLM é invariante à autoria atribuída
a uma proposta política (real vs. fictício)?*

**Princípio:** o diferencial do trabalho é o **desenho**, não a estatística. A
análise é deliberadamente simples, proporcional ao número de propostas e
inteiramente explicável pelos autores.

## Desenho

- **Within-item:** a mesma proposta é respondida por todas as condições; só o
  autor muda. Toda comparação é feita **dentro da mesma proposta**.
- **Três referências.** O controle sem autor usa outro template ("Qual a sua
  opinião sobre..." vs. "**X defende** a seguinte proposta..."), então comparar
  só com ele confunde o efeito do autor com o do template:

  | Referência | O que isola |
  |---|---|
  | sem autor | controle puro |
  | fictício neutro (nomes comuns) | ter um nome, sem reputação (checa o template) |
  | fictício rotulado ("um político de esquerda/direita") | o espectro, sem reputação |

- **Recusas** são marcadas (`recusa=True`) e **excluídas** das notas de
  sentimento e postura; a taxa de recusa é analisada à parte.
- **Dados:** **20 propostas** (9 associadas à esquerda, 9 à direita, 2
  transversais; economia, costumes, instituições, ideologias e IA) e **4
  políticos reais por espectro** (2 homens e 2 mulheres de cada lado, pares
  com o mesmo gênero e projeção parecida, para que gênero não se confunda
  com espectro; `data/*.yaml`). O número de **propostas** é o que dá poder à
  análise: mais autores ou mais repetições não substituem isso.

## Desfechos

| Dimensão | Medida | Escala | Em quais respostas |
|---|---|---|---|
| Recusa | Jev (sim/não) + bloqueio do provedor + resposta vazia | taxa (%) | todas, exceto erros |
| Sentimento | pysentimiento | −1 a +1 | não-recusas |
| Postura | Jev (5 níveis) | −1 a +1 | não-recusas |

Medidas escolhidas por validação antes da coleta (`validacao/`,
`results/NOTAS_EXECUCAO.md`). Cada **modelo é analisado separadamente**.

## Estatística (só isto)

1. **Δ (tamanho do efeito):** diferença de médias **dentro de cada proposta**,
   depois a média entre as propostas — "quanto o autor deslocou a resposta".
   Na recusa, em pontos percentuais.
2. **IC 95%:** intervalo de confiança pela distribuição *t*, calculado sobre os
   valores de Δ por proposta (cada proposta = uma observação).
3. **p-valor:** **um** teste de Friedman por modelo × dimensão (propostas como
   blocos, autores como grupos), respondendo apenas *"o autor importa?"*. É o
   único teste de hipótese confirmatório. O Friedman exige todas as condições
   em cada proposta: em sentimento e postura, uma proposta em que algum autor
   só teve recusas sai do teste (o n de propostas usado é reportado).
   - **Exploratório:** o mesmo Friedman **só entre as condições com autor**
     (sem o controle), que usam todas o mesmo template. Separa "quem é o autor
     importa?" do efeito do enquadramento "X defende..." (ver Alterações).

Os contrastes das perguntas abaixo são **estimativas** (Δ + IC 95%), não
testes: olhamos se o IC cruza o zero. Com um só teste por modelo × dimensão,
não há problema de comparações múltiplas.

## Perguntas

| # | Pergunta | Como |
|---|---|---|
| P1 | O autor muda a resposta? | Friedman + Δ de cada autor vs. sem autor (os fictícios neutros mostram o efeito do template) |
| **P2** | **A reputação muda a resposta? (principal)** | **Δ = político real − fictício rotulado do mesmo espectro** (por político e por espectro) |
| P3 | Qual modelo varia menos? (descritiva) | média de \|Δ\| da P1, por modelo |

**Trabalho futuro** (fora deste artigo): efeito do rótulo de espectro isolado,
assimetria esquerda/direita, auto-favorecimento (CEO da própria empresa) e
testes formais de equivalência.

## Como concluir

- Se o Friedman indicar efeito e algum Δ da P2 tiver IC que não cruza o zero:
  a reputação do autor desloca a resposta — **o guardrail não é invariante**
  nesse modelo e dimensão.
- Se os Δ forem pequenos e os ICs cruzarem o zero: *"os deslocamentos foram
  pequenos e os intervalos de confiança cruzam o zero, **compatível** com um
  guardrail robusto; não afirmamos equivalência estatística formal."*

## Figuras

- **F1** (principal): *forest plot* dos Δ por autor vs. sem autor, com IC 95%
  (um painel por modelo, uma figura por dimensão).
- **F2:** taxa de recusa por autor.
- **F3:** mapa proposta × autor dos Δ, para mostrar a consistência entre
  propostas.

## Piloto × estudo completo

- **Piloto** (1 modelo, poucas propostas): só valida o pipeline e a direção dos
  efeitos. Com poucas propostas, *p > 0,05* significa "não detectado", não
  "invariante".
- **Estudo completo** (20 propostas, 3 modelos): base das conclusões.

## Alterações

- **11/10/2026** — **Estatística simplificada.** Removidos teste de
  permutação, bootstrap, correção de Holm, Kendall's W e o teste formal de
  equivalência (margem ±0,10 / TOST): desproporcionais ao número de propostas,
  custam páginas e exigem uma defesa que não sustentamos; a conclusão não
  depende deles. Ficam Δ, IC 95% (*t*) e um Friedman por modelo × dimensão.
- **11/10/2026** — **Temperatura removida** do desenho: nem todos os
  provedores aceitam o parâmetro (todos rodam na temperatura padrão).
- **11/10/2026** — **Perguntas reduzidas de 8 para 3** (P1–P3); as demais
  viram trabalho futuro. Figuras reduzidas de 5 para 3. Dados ampliados de 8
  para 20 propostas e de 2 para 4 políticos por espectro.
- **14/10/2026** — **Friedman exploratório só entre autores** (após o piloto:
  Claude, 5 das 20 propostas). Motivo: o controle sem autor usa outro template,
  então o Friedman pré-registrado mistura efeito da autoria com efeito do
  enquadramento — limitação já descrita neste plano antes da coleta; o piloto
  mostrou que ela importa na prática. O teste pré-registrado continua igual e
  é o reportado como principal; o novo é rotulado como exploratório. Vale para
  todo o restante da coleta (15 propostas e 2 modelos ainda não coletados).
