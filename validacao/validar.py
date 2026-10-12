"""Valida as medidas do estudo nos conjuntos de validacao/conjuntos.yaml.

    recusa e postura  -> Jev, com a formulação do config.yaml (1 chamada por texto)
    tom (sentimento)  -> medida do config (`sentimento`, ex.: pysent), local

Imprime os acertos por conjunto e os erros. Os conjuntos foram escritos por nós
(não são dados do estudo); os resultados de referência estão em
results/NOTAS_EXECUCAO.md.

Uso:
    python validacao/validar.py             # tudo (~80 chamadas ao Jev)
    python validacao/validar.py --sem-jev   # só o sentimento (local, grátis)
"""
import argparse
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
load_dotenv(RAIZ / ".env")

from src import loader, sentiment          # noqa: E402

LIMIAR = 0.15     # |nota| até 0,15 conta como "neutro" (postura e tom)


def classe(nota, pos, neg):
    return pos if nota > LIMIAR else neg if nota < -LIMIAR else "neutro"


def relatar(nome, resultados):
    """resultados: lista de (acertou, descrição do erro)."""
    ac = sum(ok for ok, _ in resultados)
    print(f"  {nome}: {ac}/{len(resultados)}")
    for ok, desc in resultados:
        if not ok:
            print(f"      erro: {desc}")
    return ac, len(resultados)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-jev", action="store_true", help="pula recusa e postura (Jev)")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    propostas = {p["id"]: p["texto"] for p in loader.carregar_propostas(cfg)}
    conj = yaml.safe_load(open(RAIZ / "validacao" / "conjuntos.yaml", encoding="utf-8"))

    if not args.sem_jev:
        jev = sentiment.Jev(cfg["jev"], cfg["api"])
        print(f"RECUSA (Jev, limiar {cfg['jev']['limiar_recusa']})")
        for nome, itens in conj["recusa"].items():
            res = []
            for it in itens:
                p_rec, _, _ = jev.avaliar(it["texto"], propostas[it["proposta"]])
                res.append(((p_rec > cfg["jev"]["limiar_recusa"]) == it["recusa"],
                            f"{'recusa' if it['recusa'] else 'não-recusa'} P(recusa)={p_rec:.2f} | {it['texto'][:60]}"))
            relatar(nome, res)
        print("POSTURA (Jev)")
        for nome, itens in conj["postura"].items():
            res = []
            for it in itens:
                _, nota, extras = jev.avaliar(it["texto"], propostas[it["proposta"]])
                c = classe(nota, "apoia", "rejeita")
                res.append((c == it["rotulo"],
                            f"{it['rotulo']} -> {c} ({nota:+.2f}, confiança {extras.get('confianca', 0):.2f}) | {it['texto'][:60]}"))
            relatar(nome, res)
        print(f"  versão do Jev: {jev.versao}")

    a = sentiment.get_analyzer(cfg["sentimento"], cfg=cfg)
    print(f"TOM ({a.nome})")
    for nome, itens in conj["tom"].items():
        res = []
        for it in itens:
            nota = a.analisar(it["texto"])
            c = classe(nota, "positivo", "negativo")
            res.append((c == it["rotulo"], f"{it['rotulo']} -> {c} ({nota:+.2f}) | {it['texto'][:60]}"))
        relatar(nome, res)


if __name__ == "__main__":
    main()
