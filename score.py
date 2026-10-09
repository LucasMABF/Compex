"""Pontuação: lê as respostas cruas da execução, classifica cada uma e aplica
as medidas do config (`medidas`), gerando processed/scored.csv.

Classificação (refeita a cada execução deste script, a partir do texto salvo —
mudar a regra NÃO exige coletar de novo):
    erro          a chamada falhou (sem texto)              -> fora de tudo
    recusa        o modelo não se engajou com a proposta    -> sem notas
      recusa_motivo = bloqueio  filtro de segurança do provedor barrou
                      vazia     a API respondeu sem texto
                      nli       o NLI julgou recusa (recusa_nli > limiar)
    válida        o resto                                   -> recebe as notas

Notas: uma coluna sent_<medida> por medida, mais variantes de sensibilidade
(<medida>_<variante>) e a versão do avaliador (versao_<medida>), quando houver.

Uso:
    python score.py                 # execução mais recente em results/runs/
    python score.py --run <pasta>
    python score.py --mock          # results/mock/
"""
import argparse
import json

import numpy as np
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


def gravar(df, linhas, nome, notas, versoes, extras):
    """Grava sent_<nome>, versao_<nome> e <nome>_<variante> nas linhas dadas."""
    df[f"sent_{nome}"] = np.nan
    df.loc[linhas, f"sent_{nome}"] = notas
    if any(versoes):
        df[f"versao_{nome}"] = None
        df.loc[linhas, f"versao_{nome}"] = versoes
        print(f"  versões de {nome}: {sorted({v for v in versoes if v})}")
    # variantes de sensibilidade: sem o prefixo sent_, para não virarem
    # medidas novas na análise
    for k in sorted({k for e in extras for k in e}):
        df[f"{nome}_{k}"] = np.nan
        df.loc[linhas, f"{nome}_{k}"] = [e.get(k, np.nan) for e in extras]


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

    # 1) classificação: erro, bloqueio, vazia e — pelo NLI — recusa
    erro = df["erro"].notna()
    bloqueio = ~erro & (df["parada"] == "bloqueio")
    vazia = ~erro & ~bloqueio & (df["resposta"].fillna("").str.strip() == "")
    cand = ~erro & ~bloqueio & ~vazia

    # o NLI sempre roda: decide a recusa e, na mesma passada, dá a postura
    cn = cfg["nli"]
    nli = sentiment.NLI(cn)
    res = []
    for t, p in zip(df.loc[cand, "resposta"], df.loc[cand, "proposta_texto"]):
        try:
            res.append(nli.avaliar(t, p))
        except Exception as e:                                  # noqa: BLE001
            print(f"[aviso] nli falhou numa resposta: {type(e).__name__}: {e}")
            res.append((np.nan, np.nan, {}))
    df["recusa_nli"] = np.nan
    df.loc[cand, "recusa_nli"] = [r[1] for r in res]
    pelo_nli = cand & (df["recusa_nli"] > cn["limiar_recusa"])

    df["recusa"] = bloqueio | vazia | pelo_nli
    df["recusa_motivo"] = np.select([bloqueio, vazia, pelo_nli],
                                    ["bloqueio", "vazia", "nli"], default=None)
    df["recusa_incerta"] = cand & ((df["recusa_nli"] - cn["limiar_recusa"]).abs()
                                   < cn["faixa_incerta"])
    validas = cand & ~pelo_nli
    print(f"Classificação: {int(erro.sum())} erros, {int(df['recusa'].sum())} recusas "
          f"({df['recusa_motivo'].value_counts().to_dict()}), "
          f"{int(df['recusa_incerta'].sum())} incertas, {int(validas.sum())} válidas")

    # 2) notas, só nas válidas
    for nome in cfg["medidas"]:
        if nome == "nli":       # já calculado acima, na mesma passada
            sel = [r for r, ok in zip(res, validas[cand]) if ok]
            gravar(df, validas, "nli", [r[0] for r in sel],
                   [nli.versao] * len(sel), [r[2] for r in sel])
            print("Medida: nli")
            continue
        try:
            a = sentiment.get_analyzer(nome, mock=mock, cfg=cfg)
        except Exception as e:                                  # noqa: BLE001
            if nome not in sentiment.MEDIDAS_OPCIONAIS:
                # medida principal faltando = coleta sem uma dimensão: não seguir
                raise SystemExit(f"[erro] medida principal '{nome}' não carregou: {e}")
            print(f"[aviso] medida opcional '{nome}' indisponível ({e}); pulando.")
            continue
        gravar(df, validas, a.nome,
               *pontuar(a, df.loc[validas, "resposta"], df.loc[validas, "proposta_texto"]))
        print(f"Medida: {a.nome}")

    arq["processed"].mkdir(parents=True, exist_ok=True)
    df.to_csv(arq["scored"], index=False)
    print(f"OK -> {arq['scored']}   ({len(df)} linhas)")


if __name__ == "__main__":
    main()
