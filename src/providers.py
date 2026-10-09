"""Clientes de API unificados + um provider MOCK para rodar sem chaves.

Interface: chamar(modelo, prompt, max_tokens) -> dict com o texto da resposta,
o motivo de parada (fim / limite / bloqueio) e os tokens usados.
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
    if rng.random() < 0.05:    # recusa sintética, para exercitar a detecção
        return "[MOCK] Não posso opinar sobre propostas políticas."
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
# Cada um devolve um dict:
#   texto            texto da resposta
#   parada           por que o modelo parou, normalizado:
#                      "fim"      terminou normalmente
#                      "limite"   cortado por max_tokens (resposta incompleta)
#                      "bloqueio" barrado pelo filtro de segurança do provedor
#                      outro      valor cru do provedor
#   parada_bruta     valor original do provedor
#   tokens_entrada / tokens_saida   uso, para custo
# ----------------------------------------------------------------------
_PARADAS = {
    # OpenAI (finish_reason)
    "stop": "fim", "length": "limite", "content_filter": "bloqueio",
    # Anthropic (stop_reason)
    "end_turn": "fim", "max_tokens": "limite", "refusal": "bloqueio",
    # Google (finish_reason)
    "STOP": "fim", "MAX_TOKENS": "limite", "SAFETY": "bloqueio",
    "BLOCKLIST": "bloqueio", "PROHIBITED_CONTENT": "bloqueio",
}


def _resposta(texto, parada, tokens_entrada, tokens_saida):
    parada = str(parada) if parada is not None else None
    return {"texto": texto or "", "parada": _PARADAS.get(parada, parada),
            "parada_bruta": parada, "tokens_entrada": tokens_entrada,
            "tokens_saida": tokens_saida}


# Timeout e novas tentativas: OpenAI e Anthropic já esperam e tentam de novo
# sozinhos (com espera crescente) em erro de rede, limite de uso (429) e
# servidor (5xx); só ajustamos os valores, iguais para os três (config `api`).
def _openai(prompt, modelo, max_tokens, timeout_s, retentativas):
    from openai import OpenAI
    cli = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                 timeout=timeout_s, max_retries=retentativas)
    # sem raciocínio: resposta direta; o max_tokens antigo dá 400 nos gpt-6
    r = cli.chat.completions.create(
        model=modelo, max_completion_tokens=max_tokens,
        reasoning_effort="none",
        messages=[{"role": "user", "content": prompt}])
    c = r.choices[0]
    return _resposta(c.message.content, c.finish_reason,
                     r.usage.prompt_tokens, r.usage.completion_tokens)


def _anthropic(prompt, modelo, max_tokens, timeout_s, retentativas):
    import anthropic
    cli = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"],
                              timeout=timeout_s, max_retries=retentativas)
    # thinking não pode ser "disabled" no sonnet-5-5; "between_tools" o
    # desliga (sem ferramentas) e o max_tokens vai todo para a resposta
    r = cli.messages.create(
        model=modelo, max_tokens=max_tokens,
        thinking={"type": "between_tools"},
        messages=[{"role": "user", "content": prompt}])
    # a resposta pode trazer blocos que não são texto: pega o 1º de texto
    texto = next((b.text for b in r.content if b.type == "text"), "")
    return _resposta(texto, r.stop_reason,
                     r.usage.input_tokens, r.usage.output_tokens)


def _google(prompt, modelo, max_tokens, timeout_s, retentativas):
    # SDK novo (google-genai); o google-generativeai é legado
    from google import genai
    from google.genai import types
    # aqui o timeout é em milissegundos e `attempts` conta a 1ª chamada
    cli = genai.Client(api_key=os.environ["GOOGLE_API_KEY"],
                       http_options=types.HttpOptions(
                           timeout=int(timeout_s * 1000),
                           retry_options=types.HttpRetryOptions(attempts=retentativas + 1)))
    r = cli.models.generate_content(
        model=modelo, contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            # menor nível aceito no 3.8-flash ("minimal" dá erro)
            thinking_config=types.ThinkingConfig(thinking_level="LOW")))
    fim = r.candidates[0].finish_reason if r.candidates else None
    u = r.usage_metadata
    # o raciocínio (thoughts) também é cobrado como saída
    saida = (u.candidates_token_count or 0) + (u.thoughts_token_count or 0) if u else None
    return _resposta(r.text, getattr(fim, "name", fim),
                     u.prompt_token_count if u else None, saida)


_REAIS = {"chatgpt": _openai, "claude": _anthropic, "gemini": _google}


def chamar(modelo_rotulo, prompt, max_tokens=1500, mock=False, espectro=None,
           timeout_s=120, retentativas=5):
    """Ponto único de chamada. Retorna o dict descrito acima. Se todas as
    tentativas falharem, a exceção sobe (o collect.py a registra como erro)."""
    if mock:
        return _resposta(_mock(prompt, modelo_rotulo, espectro, max_tokens),
                         "fim", None, None)
    fn = _REAIS[modelo_rotulo]
    modelo_real = MODELOS_REAIS[modelo_rotulo]
    return fn(prompt, modelo_real, max_tokens, timeout_s, retentativas)
