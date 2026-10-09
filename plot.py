"""Gráficos para a apresentação. Lê <execução>/processed/ e salva, para
CADA medida (pysent, jev, ...), 3 PNGs em <execução>/figures/:
    barras_por_autor_<medida>.png, heatmap_proposta_autor_<medida>.png,
    delta_por_categoria_<medida>.png

Uso:
    python plot.py                  # execução mais recente em results/runs/
    python plot.py --run <pasta>
    python plot.py --mock
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import loader

plt.rcParams.update({"font.size": 10, "figure.dpi": 130,
                     "axes.edgecolor": "#888"})

AZUL, LARANJA, VERDE = "#1E6FB8", "#E8872B", "#3BA776"
VERM, ROXO = "#D64550", "#6C5CE7"


def _salvar(fig, caminho, mock):
    """Salva a figura; se os dados forem do --mock, carimba como SINTÉTICO."""
    if mock:
        fig.text(0.5, 0.5, "DADOS SINTÉTICOS (--mock)", ha="center",
                 va="center", fontsize=28, color="red", alpha=0.25,
                 rotation=20, transform=fig.transFigure)
    fig.savefig(caminho)
    plt.close(fig)


def fig_barras_por_autor(med, fig_dir, mock, medida):
    """Nota média por autor, agrupada por modelo."""
    modelos = sorted(med["modelo"].unique())
    autores = list(dict.fromkeys(med["autor_id"]))
    x = np.arange(len(autores))
    w = 0.8 / len(modelos)
    cores = [AZUL, LARANJA, VERDE, VERM, ROXO]
    fig, ax = plt.subplots(figsize=(11, 5))
    for i, m in enumerate(modelos):
        sub = med[med["modelo"] == m].set_index("autor_id").reindex(autores)
        ax.bar(x + i * w, sub["sent_medio"], w, label=m, color=cores[i % 5])
    ax.axhline(0, color="#444", lw=0.8)
    ax.set_xticks(x + w * (len(modelos) - 1) / 2)
    ax.set_xticklabels(autores, rotation=40, ha="right")
    ax.set_ylabel(f"nota média [{medida}]  (−1 a +1)")
    ax.set_title(f"Nota da resposta por autor atribuído, por modelo  [{medida}]")
    ax.legend(title="modelo")
    fig.tight_layout()
    _salvar(fig, fig_dir / f"barras_por_autor_{medida}.png", mock)


def fig_heatmap(df, fig_dir, mock, medida):
    """Proposta × autor: nota média (agregando modelos)."""
    piv = df.pivot_table(index="proposta_id", columns="autor_id",
                         values=f"sent_{medida}",
                         aggfunc="mean")
    fig, ax = plt.subplots(figsize=(11, 5))
    im = ax.imshow(piv.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns, rotation=40, ha="right")
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index)
    ax.set_title(f"Mapa de calor — nota média (proposta × autor)  [{medida}]")
    fig.colorbar(im, ax=ax, label="nota média")
    fig.tight_layout()
    _salvar(fig, fig_dir / f"heatmap_proposta_autor_{medida}.png", mock)


def fig_delta_categoria(delta, fig_dir, mock, medida):
    """Δ médio vs. controle, por categoria de autor."""
    g = (delta.groupby("categoria")["delta_vs_neutro"]
              .agg(["mean", "std"]).reset_index())
    cores = [VERM if v < 0 else VERDE for v in g["mean"]]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(g["categoria"], g["mean"], yerr=g["std"].fillna(0),
           color=cores, capsize=4)
    ax.axhline(0, color="#444", lw=0.8)
    ax.set_ylabel(f"Δ nota vs. autor neutro [{medida}]")
    ax.set_title(f"Deslocamento da nota por categoria de autor  [{medida}]\n"
                 "(0 = invariante; ≠0 = o guardrail não se sustenta)")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    _salvar(fig, fig_dir / f"delta_por_categoria_{medida}.png", mock)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="pasta da execução (padrão: a mais recente)")
    ap.add_argument("--mock", action="store_true", help="usa results/mock/")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    arq = loader.arquivos(loader.pasta_run(cfg, args.run, args.mock))
    fig_dir = arq["figures"]
    fig_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(arq["scored"])
    med = pd.read_csv(arq["processed"] / "media_por_autor.csv")
    delta = pd.read_csv(arq["processed"] / "delta_vs_neutro.csv")

    mock = bool(df["mock"].any())
    medidas = list(dict.fromkeys(med["medida"]))
    for m in medidas:
        fig_barras_por_autor(med[med["medida"] == m], fig_dir, mock, m)
        fig_heatmap(df, fig_dir, mock, m)
        fig_delta_categoria(delta[delta["medida"] == m], fig_dir, mock, m)
    print(f"OK -> {fig_dir}/*.png  (3 figuras × {len(medidas)} medidas)")


if __name__ == "__main__":
    main()
