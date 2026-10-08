"""Carregadores de config e dados, e as pastas de cada execução.

Cada coleta real vive em results/runs/<data-hora>_<nome>/ (o mock, em
results/mock/), com sempre a mesma estrutura:
    config/       cópia do config.yaml e de data/*.yaml usados
    metadata.json quando, commit do código, modelos, argumentos
    raw/          responses.jsonl + coleta.log  (fora do git)
    processed/    scored.csv (fora do git) + CSVs resumidos
    figures/      PNGs
"""
import shutil
from datetime import datetime
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent


def carregar_config(caminho="config.yaml"):
    with open(RAIZ / caminho, encoding="utf-8") as f:
        return yaml.safe_load(f)


def carregar_propostas(cfg):
    with open(RAIZ / cfg["paths"]["proposals"], encoding="utf-8") as f:
        return yaml.safe_load(f)["propostas"]


def carregar_autores(cfg):
    with open(RAIZ / cfg["paths"]["authors"], encoding="utf-8") as f:
        return yaml.safe_load(f)["autores"]


def nova_pasta_run(cfg, nome=None, mock=False):
    """Cria a pasta de uma execução nova. O mock sempre sobrescreve a sua."""
    if mock:
        pasta = RAIZ / cfg["paths"]["mock"]
        shutil.rmtree(pasta, ignore_errors=True)
    else:
        carimbo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        pasta = RAIZ / cfg["paths"]["runs"] / (f"{carimbo}_{nome}" if nome else carimbo)
    pasta.mkdir(parents=True)
    return pasta


def pasta_run(cfg, run=None, mock=False):
    """Pasta de uma execução existente: a informada, a do mock, ou a mais recente."""
    if run:
        pasta = Path(run).resolve()
    elif mock:
        pasta = RAIZ / cfg["paths"]["mock"]
    else:
        runs = sorted(p for p in (RAIZ / cfg["paths"]["runs"]).glob("*") if p.is_dir())
        if not runs:
            raise SystemExit("nenhuma execução em results/runs/ — rode run.py "
                             "(ou use --mock / --run <pasta>)")
        pasta = runs[-1]
    if not pasta.is_dir():
        raise SystemExit(f"pasta de execução não existe: {pasta}")
    return pasta


def arquivos(pasta):
    """Caminhos padronizados dentro de uma pasta de execução."""
    return {
        "raw": pasta / "raw" / "responses.jsonl",
        "log": pasta / "raw" / "coleta.log",
        "scored": pasta / "processed" / "scored.csv",
        "processed": pasta / "processed",
        "figures": pasta / "figures",
    }
