"""Análise (PLANO_ANALISE.md): Δ dentro de cada proposta, IC 95% pela
distribuição t e um teste de Friedman por modelo × dimensão (mais um Friedman
exploratório só entre os autores, que usam todos o mesmo template).

Dimensões: recusa (taxa, em %), sentimento (config `sentimento`) e postura
(Jev). Sentimento e postura usam só as não-recusas (já vêm vazias nas recusas).

Gera em <execução>/processed/:
    medias.csv              média por (modelo, dimensão, autor) — média das propostas
    delta_por_proposta.csv  Δ de cada autor vs. sem autor, proposta a proposta (F3)
    contrastes.csv          P1 (autor − sem autor) e P2 (político real − fictício
                            rotulado do mesmo espectro): Δ, IC 95% (t), n de propostas
    friedman.csv            P1: "o autor importa?" — por modelo × dimensão, em dois
                            conjuntos: "todas" (pré-registrado, inclui o sem autor)
                            e "so_autores" (exploratório: só as condições com autor,
                            todas com o mesmo template "X defende...")
    variacao_modelos.csv    P3: média de |Δ| da P1 por modelo × dimensão

Uso:
    python analyze.py               # execução mais recente em results/runs/
    python analyze.py --run <pasta>
    python analyze.py --mock
"""
import argparse

import numpy as np
import pandas as pd
from scipy import stats

from src import loader

CONTROLE = "neutro"     # autor_id da condição sem autor


def colunas_dimensoes(df, cfg):
    """dimensão -> coluna do scored.csv (só as que existem)."""
    df["recusa_pct"] = np.where(df["erro"].isna(), df["recusa"].astype(float) * 100, np.nan)
    dims = {"recusa": "recusa_pct", "sentimento": f"sent_{cfg['sentimento']}",
            "postura": "sent_jev"}
    return {d: c for d, c in dims.items() if c in df}


def celulas(df, col):
    """Média por proposta × autor (média das repetições), por modelo.
    Devolve {modelo: tabela propostas × autores}."""
    m = df.groupby(["modelo", "proposta_id", "autor_id"])[col].mean()
    return {mod: g.droplevel(0).unstack("autor_id") for mod, g in m.groupby(level=0)}


def delta_por_proposta(tab, grupo_a, grupo_b):
    """Δ em cada proposta: média dos autores de A − média dos autores de B."""
    if not set(grupo_a) <= set(tab) or not set(grupo_b) <= set(tab):
        return pd.Series(dtype=float)
    return (tab[grupo_a].mean(axis=1, skipna=False)
            - tab[grupo_b].mean(axis=1, skipna=False)).dropna()


def resumo(deltas):
    """Δ médio e IC 95% pela distribuição t (cada proposta = uma observação)."""
    n = len(deltas)
    media = deltas.mean() if n else np.nan
    if n < 2:
        return media, np.nan, np.nan, n
    meia = stats.t.ppf(0.975, n - 1) * deltas.std(ddof=1) / np.sqrt(n)
    return media, media - meia, media + meia, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="pasta da execução (padrão: a mais recente)")
    ap.add_argument("--mock", action="store_true", help="usa results/mock/")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    arq = loader.arquivos(loader.pasta_run(cfg, args.run, args.mock))
    df = pd.read_csv(arq["scored"])
    autores = {a["id"]: a for a in loader.carregar_autores(cfg)}
    dims = colunas_dimensoes(df, cfg)

    medias, por_prop, contrastes, friedman = [], [], [], []
    for dim, col in dims.items():
        for modelo, tab in celulas(df, col).items():
            # médias por autor (média das propostas)
            for a, v in tab.mean().items():
                medias.append({"modelo": modelo, "dimensao": dim, "autor_id": a,
                               "categoria": autores[a]["categoria"],
                               "espectro": autores[a].get("espectro"),
                               "media": v, "n_propostas": int(tab[a].notna().sum())})

            # P1: cada autor − sem autor
            for a in tab.columns.drop(CONTROLE, errors="ignore"):
                d = delta_por_proposta(tab, [a], [CONTROLE])
                por_prop += [{"modelo": modelo, "dimensao": dim, "proposta_id": p,
                              "autor_id": a, "delta": v} for p, v in d.items()]
                contrastes.append(("P1", modelo, dim, f"{a} − sem autor", a,
                                   autores[a]["categoria"], autores[a].get("espectro"), d))

            # P2: político real − fictício rotulado do mesmo espectro
            for esp in sorted({v.get("espectro") for v in autores.values()} - {None}):
                pols = [a for a, v in autores.items()
                        if v["categoria"] == "politico" and v.get("espectro") == esp]
                rot = [a for a, v in autores.items()
                       if v["categoria"] == "ficticio_rotulado" and v.get("espectro") == esp]
                if not pols or not rot:
                    continue
                for a in pols:
                    contrastes.append(("P2", modelo, dim, f"{a} − {rot[0]}", a,
                                       "politico", esp, delta_por_proposta(tab, [a], rot)))
                contrastes.append(("P2", modelo, dim, f"políticos de {esp} − {rot[0]}",
                                   "(grupo)", "politico", esp,
                                   delta_por_proposta(tab, pols, rot)))

            # P1: Friedman — propostas como blocos, autores como grupos.
            # "todas" é o pré-registrado; "so_autores" (exploratório) tira o sem
            # autor, que usa outro template — separa autoria de enquadramento.
            for conjunto, t in [("todas", tab),
                                ("so_autores", tab.drop(columns=CONTROLE, errors="ignore"))]:
                completa = t.dropna()         # Friedman exige blocos completos
                if completa.shape[0] < 3 or completa.shape[1] < 3:
                    continue
                linha = {"modelo": modelo, "dimensao": dim, "conjunto": conjunto,
                         "n_propostas": completa.shape[0],
                         "n_autores": completa.shape[1],
                         "estatistica": np.nan, "p_valor": np.nan, "obs": ""}
                if completa.stack().nunique() <= 1:
                    # ex.: nenhuma recusa em lugar nenhum — não há o que testar
                    linha["obs"] = "sem variação (todos os valores iguais)"
                else:
                    est, p = stats.friedmanchisquare(*[completa[c] for c in completa])
                    linha.update(estatistica=round(est, 3), p_valor=round(p, 4))
                friedman.append(linha)

    linhas = []
    for perg, modelo, dim, nome, a, cat, esp, d in contrastes:
        media, lo, hi, n = resumo(d)
        linhas.append({"pergunta": perg, "modelo": modelo, "dimensao": dim,
                       "contraste": nome, "autor_id": a, "categoria": cat,
                       "espectro": esp, "delta": media, "ic95_inf": lo,
                       "ic95_sup": hi, "n_propostas": n,
                       "ic_cruza_zero": (lo <= 0 <= hi) if n >= 2 else None})
    contr = pd.DataFrame(linhas)

    # P3: quanto cada modelo varia — média de |Δ| da P1
    var = (contr[contr["pergunta"] == "P1"].assign(abs_delta=lambda x: x["delta"].abs())
           .groupby(["modelo", "dimensao"])["abs_delta"].mean().round(4)
           .reset_index(name="media_abs_delta"))

    out = arq["processed"]
    pd.DataFrame(medias).to_csv(out / "medias.csv", index=False)
    pd.DataFrame(por_prop).to_csv(out / "delta_por_proposta.csv", index=False)
    contr.to_csv(out / "contrastes.csv", index=False)
    pd.DataFrame(friedman).to_csv(out / "friedman.csv", index=False)
    var.to_csv(out / "variacao_modelos.csv", index=False)

    # resumo no terminal
    pd.set_option("display.width", 140)
    print("\n=== P1: o autor importa? (Friedman por modelo × dimensão) ===")
    print("    todas = pré-registrado (inclui sem autor); so_autores = exploratório")
    print(pd.DataFrame(friedman).to_string(index=False) if friedman
          else "(precisa de ≥ 3 propostas completas)")
    print("\n=== P2: reputação (político real − fictício rotulado), Δ e IC 95% ===")
    p2 = contr[(contr["pergunta"] == "P2") & (contr["autor_id"] == "(grupo)")]
    print(p2[["modelo", "dimensao", "contraste", "delta", "ic95_inf", "ic95_sup",
              "n_propostas"]].round(3).to_string(index=False))
    print("\n=== P3: média de |Δ| (P1) por modelo ===")
    print(var.pivot(index="modelo", columns="dimensao", values="media_abs_delta")
          .to_string())
    print("\n(recusa em pontos percentuais; sentimento e postura de −1 a +1)")
    print(f"OK -> {out}/*.csv")


if __name__ == "__main__":
    main()
