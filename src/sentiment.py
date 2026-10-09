"""Analisadores de sentimento — PLUGÁVEIS.

Todos expõem: .nome  e  .analisar(texto, proposta=None) -> float em [-1, 1]
(-1 = muito negativo, +1 = muito positivo). `proposta` é o texto da proposta
(SEM o autor), usado pelos avaliadores que julgam a postura (NLI, Jev).

- PySent:   pysentimiento (transformer PT) — medida de SENTIMENTO do estudo.
- NLI:      NLI zero-shot (mDeBERTa-v3 multilíngue) — POSTURA e detecção de RECUSA.
- Jev:      Jev / TypeSafe System One (postura; exploratório).
- LexicoPT: léxico embutido mínimo, sem dependências (só para testes offline).

Se a medida pedida não carregar, o erro sobe: trocar de medida em silêncio
invalidaria a comparação.

get_analyzer(nome) devolve a instância certa.
"""

import os
import re
import hashlib

# --- léxico mínimo em PT (placeholder honesto, só para testes offline)
_LEX = {
    # positivos
    "positiva": 1, "positivo": 1, "importante": 1, "benéfica": 1, "benéfico": 1,
    "promissora": 1, "justa": 1, "justo": 1, "necessária": 1, "necessário": 1,
    "apoio": 1, "avanço": 1, "avanços": 1, "progresso": 1, "favorável": 1,
    "boa": 1, "bom": 1, "excelente": 1, "eficaz": 1,
    # negativos
    "preocupante": -1, "arriscada": -1, "arriscado": -1, "problemática": -1,
    "problemático": -1, "prejudicial": -1, "reservas": -1, "negativos": -1,
    "negativo": -1, "controversa": -1, "controverso": -1, "dúvidas": -1,
    "ruim": -1, "péssima": -1, "perigosa": -1, "perigoso": -1, "contra": -1,
}


class LexicoPT:
    nome = "lexico_pt"

    def analisar(self, texto, proposta=None):
        toks = re.findall(r"[a-záéíóúâêôãõç]+", (texto or "").lower())
        if not toks:
            return 0.0
        s = sum(_LEX.get(t, 0) for t in toks)
        pos = sum(1 for t in toks if _LEX.get(t, 0) > 0)
        neg = sum(1 for t in toks if _LEX.get(t, 0) < 0)
        hits = pos + neg
        return 0.0 if hits == 0 else max(-1.0, min(1.0, s / hits))


def dividir_em_trechos(texto, contar, max_tokens):
    """Agrupa frases (ou palavras, se a frase for longa) em trechos de até
    max_tokens, segundo a função `contar` (nº de tokens do modelo)."""
    unidades = []
    for frase in re.split(r"(?<=[.!?:;])\s+", (texto or "").strip()):
        unidades += [frase] if contar(frase) <= max_tokens else frase.split()
    trechos, atual = [], ""
    for u in unidades:
        junto = f"{atual} {u}".strip()
        if atual and contar(junto) > max_tokens:
            trechos.append(atual)
            junto = u
        atual = junto
    return trechos + [atual] if atual else trechos


def agregar(notas, pesos):
    """Nota final = média ponderada pelo tamanho dos trechos. Devolve também
    as variantes de sensibilidade (ver PySent)."""
    extras = {"n_trechos": len(notas), "inicio": notas[0], "fim": notas[-1],
              "media_simples": sum(notas) / len(notas)}
    return sum(n * w for n, w in zip(notas, pesos)) / sum(pesos), extras


class PySent:
    """pysentimiento (modelo bertweet-pt-sentiment). Por trecho, a nota é
    P(positivo) − P(negativo), em [-1, 1].

    O modelo só lê 128 tokens e IGNORA o resto em silêncio. Por isso a
    resposta é dividida em trechos de até MAX_TOKENS (respeitando frases) e a
    nota final é a média dos trechos ponderada pelo nº de tokens de cada um —
    assim a resposta inteira conta, cada parte no seu peso.

    Para análise de sensibilidade (a conclusão não pode depender da forma de
    agregar), `extras` guarda, por resposta, variantes calculadas dos MESMOS
    trechos: n_trechos, inicio (só o 1º trecho = o que o modelo leria sem a
    divisão), fim (só o último, onde costuma estar a conclusão) e media_simples
    (todos os trechos com o mesmo peso)."""
    nome = "pysent"
    MAX_TOKENS = 100          # margem abaixo dos 128 do modelo

    def __init__(self):
        from pysentimiento import create_analyzer
        self._a = create_analyzer(task="sentiment", lang="pt")
        self.versao = self._a.model.config.name_or_path
        self.extras = {}

    def _n(self, texto):
        return len(self._a.tokenizer.tokenize(texto))

    def trechos(self, texto):
        return dividir_em_trechos(texto, self._n, self.MAX_TOKENS)

    def analisar(self, texto, proposta=None):
        self.extras = {}
        partes = self.trechos(texto)
        if not partes:
            return float("nan")
        # um trecho por vez: com lista, o pysentimiento monta um "dataset" a
        # cada chamada e fica dezenas de vezes mais lento
        res = [self._a.predict(t) for t in partes]
        pesos = [self._n(t) for t in partes]
        notas = [r.probas.get("POS", 0) - r.probas.get("NEG", 0) for r in res]
        nota, self.extras = agregar(notas, pesos)
        return nota


class NLI:
    """NLI zero-shot (mDeBERTa-v3 multilíngue): o modelo diz se a premissa
    (proposta + resposta; o autor NUNCA entra) IMPLICA cada hipótese do config
    (bloco `nli`). Numa só passada, por trecho, mede duas coisas:

    POSTURA  = P(a favor) − P(contra), em [-1, 1]. Resposta equilibrada fica
               perto de 0 (não implica nenhuma das duas).
    RECUSA   = max(P(hipóteses de recusa)) − max(P(discute), P(a favor),
               P(contra)), em [-1, 1]. > limiar_recusa (config) = recusa.
               Opinar ("sou contra", "me recuso a apoiar") conta como
               engajamento, por isso não vira recusa; ressalva seguida de
               análise também não. Ver results/NOTAS_EXECUCAO.md (testes).

    Respostas longas: trechos de até MAX_TOKENS (o modelo lê 512 contando
    proposta e hipótese), média ponderada pelo tamanho; `extras` traz as
    variantes de sensibilidade da postura (como no PySent) e p_apoia/p_rejeita."""
    nome = "nli"
    MAX_TOKENS = 400

    def __init__(self, cfg_nli):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from transformers.utils import logging as hf_logging
        # contar tokens de respostas longas (>512) dispara um aviso inofensivo
        hf_logging.set_verbosity_error()
        self._torch = torch
        # usa a GPU se houver (mesmo resultado, bem mais rápido); senão, CPU
        self._dev = "cuda" if torch.cuda.is_available() else "cpu"
        self._tok = AutoTokenizer.from_pretrained(cfg_nli["modelo"])
        self._mod = AutoModelForSequenceClassification.from_pretrained(
            cfg_nli["modelo"]).eval().to(self._dev)
        self._i_ent = {v.lower(): k for k, v in self._mod.config.id2label.items()}["entailment"]
        self.premissa = cfg_nli["premissa"]
        # ordem fixa: 0 a favor, 1 contra, 2 discute, 3.. recusa
        self.hipoteses = [cfg_nli["hipotese_apoia"], cfg_nli["hipotese_rejeita"],
                          cfg_nli["hipotese_discute"], *cfg_nli["hipoteses_recusa"]]
        self.versao = cfg_nli["modelo"]
        self.extras = {}

    def _n(self, texto):
        return len(self._tok.tokenize(texto))

    def avaliar(self, texto, proposta):
        """Devolve (postura, recusa, extras) da resposta."""
        if not proposta:
            raise ValueError("o NLI precisa do texto da proposta")
        partes = dividir_em_trechos(texto, self._n, self.MAX_TOKENS)
        if not partes:
            return float("nan"), float("nan"), {}
        premissas = [self.premissa.format(proposta=proposta, resposta=t) for t in partes]
        # todos os pares (trecho × hipótese) da resposta num lote só
        pares = [(p, h) for p in premissas for h in self.hipoteses]
        x = self._tok([p for p, _ in pares], [h for _, h in pares], return_tensors="pt",
                      padding=True, truncation="only_first", max_length=512).to(self._dev)
        with self._torch.no_grad():
            p_ent = self._torch.softmax(self._mod(**x).logits, -1)[:, self._i_ent]
        p = p_ent.reshape(len(partes), len(self.hipoteses)).tolist()
        apoia, rejeita = [r[0] for r in p], [r[1] for r in p]
        recusa_tr = [max(r[3:]) - max(r[0], r[1], r[2]) for r in p]
        pesos = [self._n(t) for t in partes]
        postura, extras = agregar([a - r for a, r in zip(apoia, rejeita)], pesos)
        extras["p_apoia"] = agregar(apoia, pesos)[0]
        extras["p_rejeita"] = agregar(rejeita, pesos)[0]
        return postura, agregar(recusa_tr, pesos)[0], extras

    def analisar(self, texto, proposta=None):
        postura, _, self.extras = self.avaliar(texto, proposta)
        return postura


class Jev:
    """Jev / TypeSafe System One — postura, EXPLORATÓRIO. Não gera texto:
    responde uma pergunta tipada (Score) com níveis descritos, e devolve a
    posição na escala (média ponderada dos níveis, pode ser fracionária), as
    probabilidades de cada nível e a confiança. Normalizamos para [-1, 1].

    Tudo vem do config (bloco `jev`), conforme docs.typesafe.ai:
      - `state` é um OBJETO {proposta, resposta} (o autor NUNCA entra);
      - pergunta e níveis referenciam esses campos; níveis descrevem
        situações, uma só dimensão (postura);
      - versão FIXADA (o alias jev-latest muda quando sai versão nova);
        a versão que respondeu é gravada por resposta;
      - limite de 32k tokens para state + pergunta: sem divisão em trechos;
      - 429 (limite) e 529 (sobrecarga): novas tentativas com espera
        crescente (config `api`); 401/422 etc. falham na hora.
    `extras`: confianca e p0..pN (probabilidade de cada nível)."""
    nome = "jev"
    URL = "https://api.typesafe.ai/v1/systemone"
    REPETIR = {429, 500, 502, 503, 504, 529}

    def __init__(self, cfg_jev, cfg_api, mock=False):
        self.mock = mock
        self.cfg = cfg_jev
        self.timeout = cfg_jev["timeout_s"]
        self.retentativas = cfg_api["retentativas"]
        self.versao, self.extras = None, {}
        self.key = os.environ.get("JEV_API_KEY")
        if not mock and not self.key:
            raise RuntimeError("defina JEV_API_KEY no .env para usar o Jev")

    def _normalizar(self, score):
        n = len(self.cfg["criteria"]) - 1            # 5 níveis -> escala 0..4
        return max(-1.0, min(1.0, score / n * 2 - 1))

    def _post(self, body):
        """POST com novas tentativas (espera 1, 2, 4, 8... s) em erro passageiro."""
        import random
        import time
        import requests
        for tentativa in range(self.retentativas + 1):
            try:
                r = requests.post(self.URL, json=body, timeout=self.timeout,
                                  headers={"Authorization": f"Bearer {self.key}"})
                if r.status_code not in self.REPETIR:
                    r.raise_for_status()          # 401, 422...: não adianta repetir
                    return r.json()
            except (requests.ConnectionError, requests.Timeout):
                pass
            if tentativa == self.retentativas:
                raise RuntimeError(f"Jev falhou após {self.retentativas + 1} tentativas")
            time.sleep(2 ** tentativa + random.random())

    def analisar(self, texto, proposta=None):
        self.versao, self.extras = None, {}
        if self.mock:                          # valor sintético estável p/ demo
            self.versao = "mock"
            h = int(hashlib.md5((texto or "").encode()).hexdigest(), 16)
            return round((h % 2000) / 1000 - 1, 3)
        body = {
            "model": self.cfg["modelo"],
            "state": {"proposta": proposta, "resposta": texto or ""},
            "questions": {"postura": {"type": "score",
                                      "instructions": self.cfg["instructions"],
                                      "criteria": self.cfg["criteria"]}},
        }
        data = self._post(body)
        # só o campo documentado; qualquer outro formato é falha (nota vazia)
        resp = data["answers"]["postura"]
        self.versao = data.get("model")
        self.extras = {"confianca": resp.get("confidence"),
                       **{f"p{k}": v for k, v in (resp.get("probabilities") or {}).items()}}
        return self._normalizar(resp["score"])


# Medidas que podem faltar sem invalidar a coleta (dependem de chave/crédito
# externos e são exploratórias). Qualquer outra medida que falhe PARA tudo.
MEDIDAS_OPCIONAIS = {"jev"}


def get_analyzer(nome, mock=False, cfg=None):
    if nome == "lexico_pt":
        return LexicoPT()
    if nome == "pysent":
        return PySent()
    if nome == "nli":
        return NLI(cfg["nli"])
    if nome == "jev":
        return Jev(cfg["jev"], cfg["api"], mock=mock)
    raise ValueError(f"analisador desconhecido: {nome}")
