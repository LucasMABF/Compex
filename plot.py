"""Figuras do artigo (PLANO_ANALISE.md). Lê <execução>/processed/ e salva em
<execução>/figures/ — sem título embutido (o título vai na legenda do artigo) e
com os nomes dos autores (da cópia de authors.yaml da execução), não os ids:
    F1  forest_<dimensao>.png       Δ de cada autor vs. sem autor, com IC 95%
                                    (um painel por modelo) — a figura principal
    F2  recusa_por_autor.png        taxa de recusa por autor, por modelo
    F3  mapa_<dimensao>.png         Δ vs. sem autor proposta a proposta
                                    (consistência entre propostas)

Uso:
    python plot.py                  # execução mais recente em results/runs/
    python plot.py --run <pasta>
    python plot.py --mock
"""
import argparse
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import yaml

from src import loader

plt.rcParams.update({"font.size": 10, "figure.dpi": 130,
                     "axes.edgecolor": "#888"})

# ordem e cor das categorias de autor (controle não aparece: é a referência)
# nomes que aparecem na legenda de cada categoria
NOME_CATEGORIA = {"politico": "político real", "ficticio_rotulado": "fictício rotulado",
                  "ficticio": "fictício neutro", "ceo": "CEO de IA"}
NOMES = {}    # autor_id -> rótulo nas figuras (preenchido em main)
CATEGORIAS = {"politico": "#1E6FB8", "ficticio_rotulado": "#6C5CE7",
              "ficticio": "#3BA776", "ceo": "#E8872B"}
ROTULO = {"recusa": "Δ taxa de recusa (p.p.)", "sentimento": "Δ sentimento",
          "postura": "Δ postura"}


def _salvar(fig, caminho, mock):
    """Salva a figura; se os dados forem do --mock, carimba como SINTÉTICO."""
    if mock:
        fig.text(0.5, 0.5, "DADOS SINTÉTICOS (--mock)", ha="center",
                 va="center", fontsize=28, color="red", alpha=0.25,
                 rotation=20, transform=fig.transFigure)
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)


def ordem_autores(c):
    """Autores agrupados por categoria (ordem de CATEGORIAS)."""
    c = c.drop_duplicates("autor_id")
    c = c.assign(_o=c["categoria"].map({k: i for i, k in enumerate(CATEGORIAS)}))
    return list(c.sort_values(["_o", "autor_id"])["autor_id"])


def fig_forest(p1, dim, fig_dir, mock):
    """F1: Δ (ponto) e IC 95% (barra) de cada autor vs. sem autor."""
    modelos = sorted(p1["modelo"].unique())
    autores = ordem_autores(p1)
    y = np.arange(len(autores))[::-1]
    fig, axs = plt.subplots(1, len(modelos), figsize=(3.6 * len(modelos), 0.35 * len(autores) + 1.5),
                            sharey=True, squeeze=False)
    for ax, m in zip(axs[0], modelos):
        sub = p1[p1["modelo"] == m].set_index("autor_id").reindex(autores)
        cores = [CATEGORIAS.get(c, "#888") for c in sub["categoria"]]
        ax.errorbar(sub["delta"], y, xerr=[sub["delta"] - sub["ic95_inf"],
                                           sub["ic95_sup"] - sub["delta"]],
                    fmt="none", ecolor="#999", elinewidth=1.2, capsize=2)
        ax.scatter(sub["delta"], y, c=cores, zorder=3, s=28)
        ax.axvline(0, color="#444", lw=0.8)
        ax.set_title(m)
        ax.set_xlabel(ROTULO[dim])
    axs[0][0].set_yticks(y)
    axs[0][0].set_yticklabels([NOMES.get(a, a) for a in autores])
    for cat, cor in CATEGORIAS.items():
        axs[0][-1].scatter([], [], c=cor, label=NOME_CATEGORIA.get(cat, cat))
    axs[0][-1].legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
    _salvar(fig, fig_dir / f"forest_{dim}.png", mock)


def fig_recusa(med, fig_dir, mock):
    """F2: taxa de recusa por autor, por modelo."""
    r = med[med["dimensao"] == "recusa"]
    modelos = sorted(r["modelo"].unique())
    autores = ["neutro"] + [a for a in ordem_autores(r) if a != "neutro"]
    x = np.arange(len(autores))
    w = 0.8 / len(modelos)
    fig, ax = plt.subplots(figsize=(max(8, 0.6 * len(autores)), 4))
    for i, m in enumerate(modelos):
        sub = r[r["modelo"] == m].set_index("autor_id").reindex(autores)
        ax.bar(x + i * w, sub["media"], w, label=m)
    ax.set_xticks(x + w * (len(modelos) - 1) / 2)
    ax.set_xticklabels([NOMES.get(a, a) for a in autores],
                       rotation=40, ha="right")
    ax.set_ylabel("taxa de recusa (%)")
    ax.legend(title="modelo", frameon=False)
    _salvar(fig, fig_dir / "recusa_por_autor.png", mock)


def fig_mapa(dp, dim, fig_dir, mock, med):
    """F3: Δ vs. sem autor em cada proposta (linhas) para cada autor (colunas)."""
    d = dp[dp["dimensao"] == dim]
    modelos = sorted(d["modelo"].unique())
    autores = ordem_autores(med[(med["dimensao"] == dim) & (med["autor_id"] != "neutro")])
    lim = 100 if dim == "recusa" else 1
    fig, axs = plt.subplots(len(modelos), 1, squeeze=False, layout="constrained",
                            figsize=(0.6 * len(autores) + 2,
                                     (0.4 * d["proposta_id"].nunique() + 1.6) * len(modelos)))
    for ax, m in zip(axs[:, 0], modelos):
        piv = d[d["modelo"] == m].pivot(index="proposta_id", columns="autor_id",
                                         values="delta").reindex(columns=autores)
        im = ax.imshow(piv.values, cmap="RdBu", vmin=-lim, vmax=lim, aspect="auto")
        ax.set_yticks(range(len(piv.index)))
        ax.set_yticklabels(piv.index)
        ax.set_xticks(range(len(autores)))
        ax.set_xticklabels([NOMES.get(a, a) for a in autores], rotation=40, ha="right")
        ax.set_title(m)
        fig.colorbar(im, ax=ax, label=ROTULO[dim])
    _salvar(fig, fig_dir / f"mapa_{dim}.png", mock)


def carregar_nomes(pasta, cfg):
    """Rótulo de cada autor nas figuras, da cópia de authors.yaml da execução
    (ou de data/, se não houver): o nome; fictícios neutros marcados como tais."""
    copia = pasta / "config" / pathlib.Path(cfg["paths"]["authors"]).name
    autores = (yaml.safe_load(open(copia, encoding="utf-8"))["autores"]
               if copia.exists() else loader.carregar_autores(cfg))
    for a in autores:
        if a["nome"] is None:
            NOMES[a["id"]] = "sem autor"
        elif a["categoria"] == "ficticio":
            NOMES[a["id"]] = f"{a['nome']} (fictício)"
        else:
            NOMES[a["id"]] = a["nome"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="pasta da execução (padrão: a mais recente)")
    ap.add_argument("--mock", action="store_true", help="usa results/mock/")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    pasta = loader.pasta_run(cfg, args.run, args.mock)
    arq = loader.arquivos(pasta)
    carregar_nomes(pasta, cfg)
    fig_dir = arq["figures"]
    fig_dir.mkdir(parents=True, exist_ok=True)
    proc = arq["processed"]
    contr = pd.read_csv(proc / "contrastes.csv")
    med = pd.read_csv(proc / "medias.csv")
    dp = pd.read_csv(proc / "delta_por_proposta.csv")
    mock = bool(pd.read_csv(arq["scored"], usecols=["mock"])["mock"].any())

    p1 = contr[contr["pergunta"] == "P1"]
    dims = list(dict.fromkeys(p1["dimensao"]))
    for dim in dims:
        fig_forest(p1[p1["dimensao"] == dim], dim, fig_dir, mock)
        fig_mapa(dp, dim, fig_dir, mock, med)
    fig_recusa(med, fig_dir, mock)
    print(f"OK -> {fig_dir}/*.png  (F1 e F3 × {len(dims)} dimensões, F2)")


if __name__ == "__main__":
    main()
