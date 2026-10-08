"""Análise: para CADA medida (sent_leia, sent_jev, ...), calcula médias por
condição, o Δ em relação ao controle (autor neutro) e um teste
não-paramétrico de invariância.

Gera em <execução>/processed/ (coluna `medida` em todos):
    media_por_autor.csv     média por (medida, modelo, autor)
    delta_vs_neutro.csv     Δ = média(autor) − média(neutro), por (medida, modelo)
    teste_invariancia.csv   Friedman por (medida, modelo) entre as condições de autoria

Uso:
    python analyze.py               # execução mais recente em results/runs/
    python analyze.py --run <pasta>
    python analyze.py --mock
"""
import argparse

import pandas as pd

from src import loader

try:
    from scipy.stats import friedmanchisquare
    TEM_SCIPY = True
except Exception:          # noqa: BLE001
    TEM_SCIPY = False


def colunas_sent(df):
    return [c for c in df.columns if c.startswith("sent_")]


def analisar_medida(df, sc):
    """Médias, Δ vs. neutro e Friedman para uma coluna de nota."""
    medida = sc.removeprefix("sent_")

    # 1) média por (modelo, autor)
    med = (df.groupby(["modelo", "autor_id", "categoria", "espectro"],
                      dropna=False)[sc]
             .agg(sent_medio="mean", n_validas="count").reset_index())
    med.insert(0, "medida", medida)

    # 2) Δ vs controle (autor neutro), por modelo
    linhas = []
    for modelo, g in med.groupby("modelo"):
        neutro = g.loc[g["autor_id"] == "neutro", "sent_medio"]
        base_val = float(neutro.iloc[0]) if len(neutro) else float("nan")
        for _, r in g.iterrows():
            if r["autor_id"] == "neutro":
                continue
            linhas.append({"medida": medida, "modelo": modelo,
                           "autor_id": r["autor_id"],
                           "categoria": r["categoria"],
                           "espectro": r["espectro"],
                           "sent_medio": r["sent_medio"],
                           "delta_vs_neutro": r["sent_medio"] - base_val})
    delta = pd.DataFrame(linhas)

    # 3) teste de invariância: as condições de autoria diferem entre si?
    #    Friedman (medidas repetidas) por modelo, pareado por proposta.
    testes = []
    if TEM_SCIPY:
        for modelo, g in df.groupby("modelo"):
            piv = g.pivot_table(index="proposta_id", columns="autor_id",
                                values=sc, aggfunc="mean")
            piv = piv.dropna(axis=1)              # só autores completos
            if piv.shape[1] >= 3 and piv.shape[0] >= 3:
                stat, p = friedmanchisquare(*[piv[c] for c in piv.columns])
                testes.append({"medida": medida, "modelo": modelo,
                               "n_propostas": piv.shape[0],
                               "n_condicoes": piv.shape[1],
                               "friedman_stat": round(stat, 3),
                               "p_valor": round(p, 4),
                               "invariante_p>0.05": p > 0.05})
    return med, delta, pd.DataFrame(testes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="pasta da execução (padrão: a mais recente)")
    ap.add_argument("--mock", action="store_true", help="usa results/mock/")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    arq = loader.arquivos(loader.pasta_run(cfg, args.run, args.mock))
    df = pd.read_csv(arq["scored"])

    partes = [analisar_medida(df, sc) for sc in colunas_sent(df)]
    if not partes:
        raise SystemExit("scored.csv não tem nenhuma coluna sent_* — rode score.py")
    med, delta, testes = (pd.concat([p[i] for p in partes], ignore_index=True)
                          for i in range(3))
    med.to_csv(arq["processed"] / "media_por_autor.csv", index=False)
    delta.to_csv(arq["processed"] / "delta_vs_neutro.csv", index=False)
    testes.to_csv(arq["processed"] / "teste_invariancia.csv", index=False)

    # resumo no terminal
    print("\n=== Δ médio por categoria (quanto o autor desloca a nota) ===")
    if len(delta):
        print(delta.pivot_table(index="categoria", columns="medida",
                                values="delta_vs_neutro", aggfunc="mean")
              .round(3).to_string())
    if len(testes):
        print("\n=== Teste de invariância (Friedman) por medida e modelo ===")
        print(testes.to_string(index=False))
    elif not TEM_SCIPY:
        print("\n(scipy ausente — pulei o teste estatístico; "
              "pip install scipy)")
    print(f"\nOK -> {arq['processed']}/*.csv")


if __name__ == "__main__":
    main()
