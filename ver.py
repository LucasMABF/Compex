"""Lê as respostas de forma legível, para depurar e revisar prompts.

Lê a execução mais recente em results/runs/ (ou --run <pasta> / --mock).
Usa processed/scored.csv quando existe (traz a classificação de recusa); senão,
só os dados crus de raw/responses.jsonl.

Uso:
    python ver.py                          # resumo: contagens, erros, recusas
    python ver.py --modelo claude --prop P1 --autor pol_dir_1
    python ver.py --erros                  # só chamadas com erro
    python ver.py --recusas                # só respostas classificadas como recusa
    python ver.py --incertas               # recusa/não-recusa perto do limiar: revisar
    python ver.py --cortadas               # só respostas cortadas por max_tokens
"""
import argparse
import json

import pandas as pd

from src import loader


def carregar(arq):
    """Linhas da execução como dicts; NaN vira None."""
    if arq["scored"].exists():
        df = pd.read_csv(arq["scored"])
        return df.astype(object).where(df.notna(), None).to_dict("records"), True
    return [json.loads(l) for l in open(arq["raw"], encoding="utf-8")], False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="pasta da execução (padrão: a mais recente)")
    ap.add_argument("--mock", action="store_true", help="usa results/mock/")
    ap.add_argument("--modelo")
    ap.add_argument("--prop")
    ap.add_argument("--autor")
    ap.add_argument("--erros", action="store_true")
    ap.add_argument("--recusas", action="store_true")
    ap.add_argument("--incertas", action="store_true")
    ap.add_argument("--cortadas", action="store_true")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    pasta = loader.pasta_run(cfg, args.run, args.mock)
    linhas, classificado = carregar(loader.arquivos(pasta))
    print(f"[{pasta}]" + ("" if classificado else "  (sem scored.csv: rode score.py "
                                                  "para ver a classificação de recusa)"))
    if (args.recusas or args.incertas) and not classificado:
        raise SystemExit("--recusas/--incertas precisam do scored.csv: rode score.py")

    filtros = any([args.modelo, args.prop, args.autor, args.erros,
                   args.recusas, args.incertas, args.cortadas])
    if not filtros:
        print(f"{len(linhas)} respostas")
        for m in sorted({l["modelo"] for l in linhas}):
            sub = [l for l in linhas if l["modelo"] == m]
            rec = ""
            if classificado:
                motivos = pd.Series([l["recusa_motivo"] for l in sub if l["recusa"]])
                rec = (f" | recusas {sum(bool(l['recusa']) for l in sub)} "
                       f"{motivos.value_counts().to_dict() or ''}"
                       f" | incertas {sum(bool(l['recusa_incerta']) for l in sub)}")
            print(f"  {m}: {len(sub)} | erros {sum(bool(l.get('erro')) for l in sub)}{rec}"
                  f" | cortadas {sum(bool(l.get('cortada')) for l in sub)}"
                  f" | tokens saída {int(sum(l.get('tokens_saida') or 0 for l in sub))}")
        print("Use --modelo/--prop/--autor/--erros/--recusas/--incertas/--cortadas "
              "para ver os textos.")
        return

    for l in linhas:
        if args.modelo and l["modelo"] != args.modelo: continue
        if args.prop and l["proposta_id"] != args.prop: continue
        if args.autor and l["autor_id"] != args.autor: continue
        if args.erros and not l.get("erro"): continue
        if args.recusas and not l["recusa"]: continue
        if args.incertas and not l["recusa_incerta"]: continue
        if args.cortadas and not l.get("cortada"): continue
        rec = ""
        if classificado and l["recusa"]:
            rec = f" | RECUSA ({l['recusa_motivo']})"
        if classificado and l.get("jev_p_recusa") is not None:
            rec += f" | P(recusa)={l['jev_p_recusa']:.2f}" + (" INCERTA" if l["recusa_incerta"] else "")
        print("=" * 78)
        print(f"{l['proposta_id']} | {l['autor_id']} | {l['modelo']} | "
              f"rep={l['rep']}" + rec
              + (" | CORTADA" if l.get("cortada") else "")
              + (f" | parada={l['parada_bruta']}" if l.get("parada_bruta") else ""))
        print(f"PROMPT: {l['prompt']}")
        print("-" * 78)
        print(f"ERRO: {l['erro']}" if l.get("erro") else l["resposta"])


if __name__ == "__main__":
    main()
