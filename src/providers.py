"""Clientes de API unificados + um provider MOCK para rodar sem chaves.

Interface: chamar(modelo, prompt, max_tokens) -> str (texto da resposta).
Temperatura não é enviada: todos usam o padrão do provedor.

Os SDKs reais são importados de forma preguiçosa (lazy), então o modo
--mock funciona sem openai/anthropic/google instalados ou configurados.
As chaves vêm de variáveis de ambiente (ver .env.example)."""

import os
import random
import hashlib

# mapeia o rótulo do config -> modelo real de cada provedor
# (conferido em out/2026 nas páginas de modelos de cada provedor)
MODELOS_REAIS = {
    "chatgpt": "gpt-6-luna",          # tier eficiente (sucessor do gpt-4o-mini)
    "claude": "claude-sonnet-5-5",
    "gemini": "gemini-3.8-flash",     # gemini-1.5-flash foi desligado
}


# ----------------------------------------------------------------------
# MOCK — gera texto sintético plausível, SEM rede.
# O tom é levemente enviesado por (modelo, espectro do autor) só para
# que o pipeline e os gráficos demonstrem um padrão. NÃO são dados reais.
# ----------------------------------------------------------------------
_POS = ["positiva", "importante", "benéfica", "promissora", "justa",
        "necessária", "apoio essa medida", "traz avanços", "é um progresso"]
_NEG = ["preocupante", "arriscada", "problemática", "prejudicial",
        "tenho reservas", "pode trazer efeitos negativos", "é controversa",
        "gera sérias dúvidas"]
_NEU = ["é um tema complexo", "há argumentos dos dois lados",
        "depende de como for implementada", "exige análise cuidadosa"]


def _mock(prompt, modelo, espectro, max_tokens):
    # semente determinística por prompt+modelo -> reprodutível
    semente = int(hashlib.md5(f"{prompt}{modelo}".encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(semente)
    # viés sintético: cada "modelo" reage um pouco diferente à autoria
    vies = 0.0
    if espectro == "esquerda":
        vies += {"chatgpt": 0.25, "claude": 0.15, "gemini": 0.10}.get(modelo, 0)
    elif espectro == "direita":
        vies -= {"chatgpt": 0.20, "claude": 0.10, "gemini": 0.15}.get(modelo, 0)
    p = max(0.0, min(1.0, 0.5 + vies + rng.uniform(-0.15, 0.15)))
    if rng.random() < p - 0.15:
        corpo = rng.choice(_POS)
    elif rng.random() < 0.5:
        corpo = rng.choice(_NEG)
    else:
        corpo = rng.choice(_NEU)
    return (f"[MOCK] Sobre a proposta, considero que ela é {corpo}. "
            f"É preciso ponderar os impactos envolvidos.")


# ----------------------------------------------------------------------
# Providers reais (lazy)
# ----------------------------------------------------------------------
def _openai(prompt, modelo, max_tokens):
    from openai import OpenAI
    cli = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    # sem raciocínio: resposta direta; o max_tokens antigo dá 400 nos gpt-6
    r = cli.chat.completions.create(
        model=modelo, max_completion_tokens=max_tokens,
        reasoning_effort="none",
        messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content


def _anthropic(prompt, modelo, max_tokens):
    import anthropic
    cli = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # thinking não pode ser "disabled" no sonnet-5-5; "between_tools" o
    # desliga (sem ferramentas) e o max_tokens vai todo para a resposta
    r = cli.messages.create(
        model=modelo, max_tokens=max_tokens,
        thinking={"type": "between_tools"},
        messages=[{"role": "user", "content": prompt}])
    # a resposta pode trazer blocos que não são texto: pega o 1º de texto
    return next((b.text for b in r.content if b.type == "text"), "")


def _google(prompt, modelo, max_tokens):
    # SDK novo (google-genai); o google-generativeai é legado
    from google import genai
    from google.genai import types
    cli = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    r = cli.models.generate_content(
        model=modelo, contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            # menor nível aceito no 3.8-flash ("minimal" dá erro)
            thinking_config=types.ThinkingConfig(thinking_level="LOW")))
    return r.text or ""


_REAIS = {"chatgpt": _openai, "claude": _anthropic, "gemini": _google}


def chamar(modelo_rotulo, prompt, max_tokens=400, mock=False, espectro=None):
    """Ponto único de chamada. Retorna o texto da resposta."""
    if mock:
        return _mock(prompt, modelo_rotulo, espectro, max_tokens)
    fn = _REAIS[modelo_rotulo]
    modelo_real = MODELOS_REAIS[modelo_rotulo]
    return fn(prompt, modelo_real, max_tokens)
