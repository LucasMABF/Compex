"""Lê as respostas cruas de forma legível, para depurar e revisar prompts.

Lê a execução mais recente em results/runs/ (ou --run <pasta> / --mock).

Uso:
    python ver.py                          # resumo: contagens, erros, recusas
    python ver.py --modelo claude --prop P1 --autor pol_dir_1
    python ver.py --erros                  # só chamadas com erro
    python ver.py --recusas                # só respostas marcadas como recusa
"""
import argparse
import json

from src import loader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="pasta da execução (padrão: a mais recente)")
    ap.add_argument("--mock", action="store_true", help="usa results/mock/")
    ap.add_argument("--modelo")
    ap.add_argument("--prop")
    ap.add_argument("--autor")
    ap.add_argument("--erros", action="store_true")
    ap.add_argument("--recusas", action="store_true")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    pasta = loader.pasta_run(cfg, args.run, args.mock)
    linhas = [json.loads(l) for l in
              open(loader.arquivos(pasta)["raw"], encoding="utf-8")]
    print(f"[{pasta}]")

    filtros = any([args.modelo, args.prop, args.autor, args.erros, args.recusas])
    if not filtros:
        print(f"{len(linhas)} respostas")
        for m in sorted({l["modelo"] for l in linhas}):
            sub = [l for l in linhas if l["modelo"] == m]
            print(f"  {m}: {len(sub)} | erros {sum(bool(l.get('erro')) for l in sub)}"
                  f" | recusas {sum(l['recusa'] for l in sub)}")
        print("Use --modelo/--prop/--autor/--erros/--recusas para ver os textos.")
        return

    for l in linhas:
        if args.modelo and l["modelo"] != args.modelo: continue
        if args.prop and l["proposta_id"] != args.prop: continue
        if args.autor and l["autor_id"] != args.autor: continue
        if args.erros and not l.get("erro"): continue
        if args.recusas and not l["recusa"]: continue
        print("=" * 78)
        print(f"{l['proposta_id']} | {l['autor_id']} | {l['modelo']} | "
              f"rep={l['rep']}"
              + (" | RECUSA" if l["recusa"] else ""))
        print(f"PROMPT: {l['prompt']}")
        print("-" * 78)
        print(f"ERRO: {l['erro']}" if l.get("erro") else l["resposta"])


if __name__ == "__main__":
    main()
