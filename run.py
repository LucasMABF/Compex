"""Pipeline completo: coleta -> pontuação -> análise -> gráficos, tudo numa
pasta nova de execução (results/runs/<data-hora>_<nome>/; o mock vai para
results/mock/). Ver src/loader.py para a estrutura da pasta.

Uso:
    python run.py --mock                                   # sem chaves
    python run.py --nome piloto --models claude --props P1 P2 P3 --reps 3
    python run.py --nome completo                          # tudo do config

    # complementar uma execução existente (coleta só o que falta, refaz o que
    # deu erro e reanalisa tudo junto; confere antes se template e dados são
    # os mesmos):
    python run.py --run results/runs/<pasta> --models gemini
    python run.py --run results/runs/<pasta>               # o resto do config

Sem --run (e sem --mock), cria uma execução NOVA e pede confirmação antes de
gastar chamadas — esquecer o --run não paga de novo o que já existe.
--sim pula a confirmação (para scripts).
"""
import argparse
import subprocess
import sys

from src import loader


def passo(args_lista):
    print(f"\n$ python {' '.join(args_lista)}")
    r = subprocess.run([sys.executable, *args_lista])
    if r.returncode:
        sys.exit(r.returncode)


def confirmar_nova(args):
    """Execução nova = coleta do zero: mostra o tamanho e pede confirmação."""
    cfg = loader.carregar_config()
    props = [p for p in loader.carregar_propostas(cfg)
             if not args.props or p["id"] in args.props]
    n = (len(props) * len(loader.carregar_autores(cfg))
         * len(args.models or cfg["modelos"]) * (args.reps or cfg["repeticoes"]))
    existentes = sorted((loader.RAIZ / cfg["paths"]["runs"]).glob("*/"))
    print(f"Isso cria uma execução NOVA (não complementa nenhuma) e faz {n} chamadas.")
    if existentes:
        print(f"Para complementar uma existente, use --run <pasta> "
              f"(a mais recente: {existentes[-1].relative_to(loader.RAIZ)}).")
    if input("Continuar? [s/N] ").strip().lower() not in ("s", "sim"):
        sys.exit("Cancelado; nada foi coletado.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--nome", help="sufixo da pasta da execução (ex.: piloto)")
    ap.add_argument("--reps", type=int)
    ap.add_argument("--models", nargs="+")
    ap.add_argument("--props", nargs="+")
    ap.add_argument("--run", help="complementa esta execução em vez de criar uma nova")
    ap.add_argument("--sim", action="store_true", help="não pede confirmação")
    args = ap.parse_args()

    if not args.run and not args.mock and not args.sim:
        confirmar_nova(args)

    if args.run:
        pasta = loader.pasta_run(loader.carregar_config(), args.run)
        extra = ["--complementar"]
    else:
        pasta = loader.nova_pasta_run(loader.carregar_config(), args.nome, args.mock)
        extra = []
    run = ["--run", str(pasta)]
    flags = (["--mock"] if args.mock else []) + \
            (["--nome", args.nome] if args.nome else []) + \
            (["--reps", str(args.reps)] if args.reps else []) + \
            (["--models", *args.models] if args.models else []) + \
            (["--props", *args.props] if args.props else [])

    passo(["collect.py", *run, *extra, *flags])
    passo(["score.py", *run])
    passo(["analyze.py", *run])
    passo(["plot.py", *run])
    print(f"\nPronto. Tudo em {pasta}/")


if __name__ == "__main__":
    main()
