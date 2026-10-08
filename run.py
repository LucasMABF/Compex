"""Pipeline completo: coleta -> pontuação -> análise -> gráficos, tudo numa
pasta nova de execução (results/runs/<data-hora>_<nome>/; o mock vai para
results/mock/). Ver src/loader.py para a estrutura da pasta.

Uso:
    python run.py --mock                                   # sem chaves
    python run.py --nome piloto --models claude --props P1 P2 P3 --reps 3
    python run.py --nome completo                          # tudo do config
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--nome", help="sufixo da pasta da execução (ex.: piloto)")
    ap.add_argument("--reps", type=int)
    ap.add_argument("--models", nargs="+")
    ap.add_argument("--props", nargs="+")
    args = ap.parse_args()

    pasta = loader.nova_pasta_run(loader.carregar_config(), args.nome, args.mock)
    run = ["--run", str(pasta)]
    flags = (["--mock"] if args.mock else []) + \
            (["--nome", args.nome] if args.nome else []) + \
            (["--reps", str(args.reps)] if args.reps else []) + \
            (["--models", *args.models] if args.models else []) + \
            (["--props", *args.props] if args.props else [])

    passo(["collect.py", *run, *flags])
    passo(["score.py", *run])
    passo(["analyze.py", *run])
    passo(["plot.py", *run])
    print(f"\nPronto. Tudo em {pasta}/")


if __name__ == "__main__":
    main()
