"""Coleta: roda o grid (proposta × autor × modelo × repetição) e salva, na
pasta da execução (ver src/loader.py):
    raw/responses.jsonl   uma resposta por linha (prompt, texto, erro, motivo
                          de parada/corte, tokens). A coleta só grava FATOS: a
                          classificação (recusa etc.) é feita no score.py.
    raw/coleta.log        uma linha por chamada (tempo, tamanho, erro completo)
    config/, metadata.json  o que foi usado, para reproduzir

Para LER as respostas: python ver.py

Uso:
    python collect.py --nome piloto      # nova pasta em results/runs/
    python collect.py --mock             # offline, sem chaves -> results/mock/
"""
import argparse
import json
import logging
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:          # noqa: BLE001
    pass

from src import loader, prompts, providers

def commit_atual():
    """Commit do código que gerou os dados (e se havia mudanças não commitadas)."""
    def git(*a):
        r = subprocess.run(["git", *a], cwd=loader.RAIZ, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    return {"commit": git("rev-parse", "HEAD"),
            "alteracoes_nao_commitadas": bool(git("status", "--porcelain"))}


def salvar_contexto(pasta, cfg, args, modelos, propostas, reps):
    """Copia config/dados usados e grava metadata.json na pasta da execução."""
    (pasta / "config").mkdir()
    shutil.copy(loader.RAIZ / "config.yaml", pasta / "config")
    for chave in ("proposals", "authors"):
        shutil.copy(loader.RAIZ / cfg["paths"][chave], pasta / "config")
    meta = {
        "inicio": datetime.now(timezone.utc).isoformat(),
        "mock": args.mock,
        "modelos": {m: providers.MODELOS_REAIS.get(m) for m in modelos},
        "propostas": [p["id"] for p in propostas],
        "repeticoes": reps,
        "max_tokens": cfg["max_tokens"],
        "argumentos": vars(args),
        "codigo": commit_atual(),
        "python": platform.python_version(),
    }
    (pasta / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="sem rede/chaves")
    ap.add_argument("--nome", help="sufixo da pasta da execução (ex.: piloto)")
    ap.add_argument("--run", help="pasta da execução (o run.py cria e passa)")
    ap.add_argument("--reps", type=int, help="sobrescreve repetições")
    ap.add_argument("--models", nargs="+", help="sobrescreve modelos")
    ap.add_argument("--props", nargs="+", help="só estas propostas (ex.: P1 P2 P3)")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    propostas = loader.carregar_propostas(cfg)
    if args.props:
        propostas = [p for p in propostas if p["id"] in args.props]
    autores = loader.carregar_autores(cfg)
    modelos = args.models or cfg["modelos"]
    reps = args.reps or cfg["repeticoes"]

    pasta = Path(args.run) if args.run else loader.nova_pasta_run(cfg, args.nome, args.mock)
    arq = loader.arquivos(pasta)
    arq["raw"].parent.mkdir(parents=True, exist_ok=True)
    salvar_contexto(pasta, cfg, args, modelos, propostas, reps)

    log = logging.getLogger("coleta")
    log.setLevel(logging.INFO)
    h = logging.FileHandler(arq["log"], mode="w", encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    log.info("inicio mock=%s modelos=%s reps=%s propostas=%s max_tokens=%s",
             args.mock, {m: providers.MODELOS_REAIS.get(m) for m in modelos},
             reps, [p["id"] for p in propostas], cfg["max_tokens"])

    total = len(propostas) * len(autores) * len(modelos) * reps
    print(f"Coletando {total} respostas "
          f"({len(propostas)} propostas × {len(autores)} autores × "
          f"{len(modelos)} modelos × {reps} reps)"
          f"{'  [MOCK]' if args.mock else ''} -> {pasta}")

    n = n_erros = n_cortadas = tok_in = tok_out = 0
    with open(arq["raw"], "w", encoding="utf-8") as f:
        for prop in propostas:
            for autor in autores:
                prompt = prompts.montar_prompt(
                    prop["texto"], autor["nome"],
                    cfg["template_autor"], cfg["template_neutro"])
                for modelo in modelos:
                    for rep in range(reps):
                        erro, r = None, {}
                        t0 = time.monotonic()
                        try:
                            r = providers.chamar(
                                modelo, prompt,
                                max_tokens=cfg["max_tokens"],
                                mock=args.mock,
                                espectro=autor.get("espectro"),
                                timeout_s=cfg["api"]["timeout_s"],
                                retentativas=cfg["api"]["retentativas"])
                        except Exception as e:      # noqa: BLE001
                            erro = f"{type(e).__name__}: {e}"
                        resp = r.get("texto")
                        parada = r.get("parada")
                        cortada = parada == "limite"
                        onde = (f"{prop['id']} {autor['id']} {modelo} rep={rep} "
                                f"({time.monotonic() - t0:.1f}s)")
                        if erro:
                            log.error("%s ERRO %s", onde, erro)
                        else:
                            log.info("%s ok %d chars, %s tokens%s%s%s", onde,
                                     len(resp), r.get("tokens_saida"),
                                     " BLOQUEIO" if parada == "bloqueio" else "",
                                     " CORTADA" if cortada else "",
                                     " VAZIA" if not resp.strip() else "")
                        linha = {
                            "proposta_id": prop["id"],
                            "proposta_texto": prop["texto"],
                            "eixo": prop.get("eixo"),
                            "autor_id": autor["id"],
                            "categoria": autor["categoria"],
                            "espectro": autor.get("espectro"),
                            "modelo": modelo,
                            "rep": rep,
                            "prompt": prompt,
                            "resposta": resp,
                            "erro": erro,
                            "parada": parada,
                            "parada_bruta": r.get("parada_bruta"),
                            "cortada": cortada,
                            "tokens_entrada": r.get("tokens_entrada"),
                            "tokens_saida": r.get("tokens_saida"),
                            "mock": args.mock,
                            "ts": datetime.now(timezone.utc).isoformat(),
                        }
                        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
                        n += 1
                        n_erros += erro is not None
                        n_cortadas += cortada
                        tok_in += r.get("tokens_entrada") or 0
                        tok_out += r.get("tokens_saida") or 0
                        if n % 50 == 0 or n == total:
                            print(f"  {n}/{total}")
                        if not args.mock:
                            time.sleep(0.2)   # educado com rate limits
    log.info("fim: %d respostas, %d erros, %d cortadas, tokens entrada=%d saida=%d",
             n, n_erros, n_cortadas, tok_in, tok_out)
    print(f"OK -> {arq['raw']}  (log: {arq['log']})")
    print(f"tokens: entrada={tok_in} saída={tok_out}")
    if n_cortadas:
        print(f"[aviso] {n_cortadas} respostas cortadas por max_tokens "
              f"({cfg['max_tokens']}) — campo 'cortada' no jsonl")
    if n_erros:
        print(f"[aviso] {n_erros} chamadas falharam — veja {arq['log']}")


if __name__ == "__main__":
    main()
