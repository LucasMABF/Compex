"""Analisadores de sentimento — PLUGÁVEIS.

Todos expõem: .nome  e  .analisar(texto, proposta=None) -> float em [-1, 1]
(-1 = muito negativo, +1 = muito positivo). `proposta` é o texto da proposta
(SEM o autor), usado pelos avaliadores que julgam a postura (Jev, LLM).

- PySent:   pysentimiento (transformer PT) — medida de SENTIMENTO do estudo.
- Jev:      Jev / TypeSafe System One (postura; exploratório).
- LexicoPT: léxico embutido mínimo, sem dependências (só para testes offline).
- LLMJudge: usa um LLM para dar a nota (opção não usada no estudo).

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
        """Agrupa frases (ou palavras, se a frase for longa) em trechos curtos."""
        unidades = []
        for frase in re.split(r"(?<=[.!?:;])\s+", texto.strip()):
            unidades += [frase] if self._n(frase) <= self.MAX_TOKENS else frase.split()
        trechos, atual = [], ""
        for u in unidades:
            junto = f"{atual} {u}".strip()
            if atual and self._n(junto) > self.MAX_TOKENS:
                trechos.append(atual)
                junto = u
            atual = junto
        return trechos + [atual] if atual else trechos

    def analisar(self, texto, proposta=None):
        self.extras = {}
        partes = self.trechos(texto or "")
        if not partes:
            return float("nan")
        # um trecho por vez: com lista, o pysentimiento monta um "dataset" a
        # cada chamada e fica dezenas de vezes mais lento
        res = [self._a.predict(t) for t in partes]
        pesos = [self._n(t) for t in partes]
        notas = [r.probas.get("POS", 0) - r.probas.get("NEG", 0) for r in res]
        self.extras = {"n_trechos": len(notas), "inicio": notas[0],
                       "fim": notas[-1], "media_simples": sum(notas) / len(notas)}
        return sum(n * w for n, w in zip(notas, pesos)) / sum(pesos)


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
                             mock=self.mock)["texto"]
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
    dos níveis (pode ser fracionário, ex.: 2.43).

    `versao` guarda a versão do modelo que respondeu (ex.: "jev-1.13.0"):
    "jev-latest" muda com o tempo, então a versão é gravada por resposta."""
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
        self.versao = None
        self.key = os.environ.get("JEV_API_KEY")
        if not mock and not self.key:
            raise RuntimeError("defina JEV_API_KEY no .env para usar o Jev")

    def _normalizar(self, score):
        n = len(self.CRITERIOS) - 1            # 4 -> escala 0..4
        return max(-1.0, min(1.0, score / n * 2 - 1))

    def analisar(self, texto, proposta=None):
        self.versao = None
        if self.mock:                          # valor sintético estável p/ demo
            self.versao = "mock"
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
        self.versao = data.get("model")
        try:
            score = data["answers"]["sentimento"]["score"]
        except (KeyError, TypeError):
            score = _buscar_num(data, {"score"})   # fallback defensivo
        # sem nota -> NaN (0.0 seria um "neutro" falso)
        return self._normalizar(score) if score is not None else float("nan")


def get_analyzer(nome, mock=False):
    if nome == "lexico_pt":
        return LexicoPT()
    if nome == "pysent":
        return PySent()
    if nome == "jev":
        return Jev(mock=mock)
    if nome == "llm":
        return LLMJudge(mock=mock)
    raise ValueError(f"analisador desconhecido: {nome}")
