"""Analisadores de sentimento — PLUGÁVEIS.

Todos expõem: .nome  e  .analisar(texto, proposta=None) -> float em [-1, 1]
(-1 = muito negativo, +1 = muito positivo). `proposta` é o texto da proposta
(SEM o autor), usado pelos avaliadores que julgam a postura (Jev, LLM).

- LexicoPT: léxico embutido, sem dependências. É o baseline que SEMPRE roda.
- Leia:     LeIA (VADER adaptado ao PT).         [pip install leia]
- PySent:   pysentimiento (transformer PT).      [pip install pysentimiento]
- LLMJudge: usa um LLM para dar a nota (a "tecnologia nova" do contraste).

get_analyzer(nome) devolve a instância certa.
"""

import os
import re
import hashlib

# --- léxico mínimo em PT (placeholder honesto; troque por LeIA/pysent p/ valer)
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


class Leia:
    nome = "leia"

    def __init__(self):
        from LeIA import SentimentIntensityAnalyzer   # pacote: leia-br
        self._a = SentimentIntensityAnalyzer()

    def analisar(self, texto, proposta=None):
        return self._a.polarity_scores(texto or "")["compound"]


class PySent:
    nome = "pysent"

    def __init__(self):
        from pysentimiento import create_analyzer
        self._a = create_analyzer(task="sentiment", lang="pt")

    def analisar(self, texto, proposta=None):
        p = self._a.predict(texto or "").probas
        return p.get("POS", 0) - p.get("NEG", 0)   # [-1, 1]


class LLMJudge:
    """Usa um LLM para pontuar o sentimento de -1 a 1. É aqui que entra
    qualquer 'tecnologia nova' de avaliação (LLM-as-judge)."""
    nome = "llm"

    def __init__(self, modelo="claude", mock=False):
        self.modelo, self.mock = modelo, mock

    def analisar(self, texto, proposta=None):
        from src import providers
        contexto = f"Proposta: {proposta}\n\n" if proposta else ""
        prompt = ("Dê uma nota de sentimento de -1 (muito negativo) a 1 "
                  "(muito positivo) para a resposta abaixo. Responda SÓ o número.\n\n"
                  f"{contexto}Resposta: {texto}")
        r = providers.chamar(self.modelo, prompt, max_tokens=8,
                             mock=self.mock)
        m = re.search(r"-?\d+(?:[.,]\d+)?", r or "")
        return max(-1.0, min(1.0, float(m.group().replace(",", ".")))) if m else 0.0


def _buscar_num(obj, chaves):
    """Procura recursivamente o primeiro número sob uma das chaves."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in chaves and isinstance(v, (int, float)):
                return float(v)
        for v in obj.values():
            r = _buscar_num(v, chaves)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _buscar_num(v, chaves)
            if r is not None:
                return r
    return None


class Jev:
    """Jev / TypeSafe 'System One'. NÃO gera texto: devolve uma decisão
    tipada e calibrada. Usamos uma pergunta Score com 5 níveis (rejeita ->
    apoia); a resposta vem em answers['sentimento'].score (0..4), que
    normalizamos para [-1, 1].

    Endpoint, header (Authorization: Bearer) e schema conferidos em
    docs.typesafe.ai/primitives/score. O score vem como média ponderada
    dos níveis (pode ser fracionário, ex.: 2.43)."""
    nome = "jev"
    URL = "https://api.typesafe.ai/v1/systemone"
    CRITERIOS = [
        "Rejeita fortemente a proposta",
        "Tende a rejeitar a proposta (tom negativo)",
        "Neutro ou ambivalente em relação à proposta",
        "Tende a apoiar a proposta (tom positivo)",
        "Apoia fortemente a proposta",
    ]

    def __init__(self, mock=False):
        self.mock = mock
        self.key = os.environ.get("JEV_API_KEY")
        if not mock and not self.key:
            raise RuntimeError("defina JEV_API_KEY no .env para usar o Jev")

    def _normalizar(self, score):
        n = len(self.CRITERIOS) - 1            # 4 -> escala 0..4
        return max(-1.0, min(1.0, score / n * 2 - 1))

    def analisar(self, texto, proposta=None):
        if self.mock:                          # valor sintético estável p/ demo
            h = int(hashlib.md5((texto or "").encode()).hexdigest(), 16)
            return round((h % 2000) / 1000 - 1, 3)
        import requests
        body = {
            "model": "jev-latest",
            # a proposta vai junto (sem o autor, para não enviesar o avaliador)
            "state": (f"Proposta: {proposta}\n\nResposta: {texto or ''}"
                      if proposta else texto or ""),
            "questions": {
                "sentimento": {
                    "type": "score",
                    "instructions": "Qual a postura da resposta em relação "
                                    "à proposta?",
                    "criteria": self.CRITERIOS,
                }
            },
        }
        r = requests.post(self.URL, json=body, timeout=30,
                          headers={"Authorization": f"Bearer {self.key}"})
        r.raise_for_status()
        data = r.json()
        try:
            score = data["answers"]["sentimento"]["score"]
        except (KeyError, TypeError):
            score = _buscar_num(data, {"score"})   # fallback defensivo
        # sem nota -> NaN (0.0 seria um "neutro" falso)
        return self._normalizar(score) if score is not None else float("nan")


def get_analyzer(nome, mock=False):
    if nome in (None, "", "lexico_pt"):
        return LexicoPT()
    if nome == "leia":
        try:
            return Leia()
        except Exception as e:                                  # noqa: BLE001
            print(f"[aviso] LeIA indisponível ({e}); usando lexico_pt. "
                  "Instale com: pip install leia-br")
            return LexicoPT()
    if nome == "pysent":
        try:
            return PySent()
        except Exception as e:                                  # noqa: BLE001
            print(f"[aviso] pysentimiento indisponível ({e}); usando lexico_pt.")
            return LexicoPT()
    if nome == "jev":
        return Jev(mock=mock)
    if nome == "llm":
        return LLMJudge(mock=mock)
    raise ValueError(f"analisador desconhecido: {nome}")
