"""Pontuação: lê as respostas cruas da execução e aplica as medidas de
sentimento (primária e secundária do config), gerando processed/scored.csv
com uma coluna sent_<medida> por medida.

Recusas e chamadas com erro não são pontuadas (ficam vazias) — assim também
não se gastam chamadas do Jev com elas.

Uso:
    python score.py                 # execução mais recente em results/runs/
    python score.py --run <pasta>
    python score.py --mock          # results/mock/
"""
import argparse
import json

import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:          # noqa: BLE001
    pass

from src import loader, sentiment


def pontuar(analisador, textos, propostas):
    """Aplica o analisador; uma falha numa resposta vira NaN, não derruba tudo.
    Devolve (notas, versões, extras) por resposta: a versão do modelo avaliador
    (para os que a informam) e as variantes de sensibilidade (`extras`, ex.:
    pysent por trechos); None/{} para os demais."""
    notas, versoes, extras, falhas = [], [], [], 0
    for t, p in zip(textos, propostas):
        try:
            notas.append(analisador.analisar(t, proposta=p))
            versoes.append(getattr(analisador, "versao", None))
            extras.append(dict(getattr(analisador, "extras", {})))
        except Exception as e:                                  # noqa: BLE001
            notas.append(float("nan"))
            versoes.append(None)
            extras.append({})
            falhas += 1
            if falhas == 1:
                print(f"[aviso] {analisador.nome} falhou: {type(e).__name__}: {e}")
    if falhas:
        print(f"[aviso] {analisador.nome}: {falhas} respostas sem nota")
    return notas, versoes, extras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="pasta da execução (padrão: a mais recente)")
    ap.add_argument("--mock", action="store_true", help="usa results/mock/")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    arq = loader.arquivos(loader.pasta_run(cfg, args.run, args.mock))
    linhas = [json.loads(l) for l in open(arq["raw"], encoding="utf-8")]
    df = pd.DataFrame(linhas)
    mock = bool(df["mock"].any())

    # recusas e chamadas com erro não entram na nota de sentimento
    validas = ~df["recusa"] & df["erro"].isna()
    textos = df.loc[validas, "resposta"]
    props = df.loc[validas, "proposta_texto"]

    nomes = [cfg["sentimento_primario"], cfg.get("sentimento_secundario")]
    for i, nome in enumerate(n for n in nomes if n):
        try:
            a = sentiment.get_analyzer(nome, mock=mock)
        except Exception as e:                                  # noqa: BLE001
            print(f"[aviso] medida '{nome}' indisponível ({e}); pulando.")
            continue
        col = f"sent_{a.nome}"
        df[col] = float("nan")
        notas, versoes, extras = pontuar(a, textos, props)
        df.loc[validas, col] = notas
        # variantes de sensibilidade: colunas <medida>_<variante> (sem o
        # prefixo sent_, para não virarem medidas novas na análise)
        for k in sorted({k for e in extras for k in e}):
            df[f"{a.nome}_{k}"] = float("nan")
            df.loc[validas, f"{a.nome}_{k}"] = [e.get(k, float("nan")) for e in extras]
        if any(versoes):
            df[f"versao_{a.nome}"] = None
            df.loc[validas, f"versao_{a.nome}"] = versoes
            print(f"  versões de {a.nome}: {sorted({v for v in versoes if v})}")
        print(f"Medida {'primária' if i == 0 else 'secundária'}: {a.nome}")

    arq["processed"].mkdir(parents=True, exist_ok=True)
    df.to_csv(arq["scored"], index=False)
    print(f"OK -> {arq['scored']}   ({len(df)} linhas, "
          f"{int(df['recusa'].sum())} recusas, "
          f"{int(df['erro'].notna().sum())} erros)")


if __name__ == "__main__":
    main()
