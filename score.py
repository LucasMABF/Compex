"""Pontuação: lê as respostas cruas da execução, classifica cada uma e mede as
três dimensões, gerando processed/scored.csv.

Classificação (refeita a cada execução deste script, a partir do texto salvo —
mudar a regra NÃO exige coletar de novo):
    erro          a chamada ao LLM falhou (sem texto)      -> fora de tudo
    recusa        o modelo não se engajou com a proposta   -> sem notas
      recusa_motivo = bloqueio  filtro de segurança do provedor barrou
                      vazia     a API respondeu sem texto
                      jev       o Jev julgou recusa (jev_p_recusa > limiar)
    falha_jev     o Jev não respondeu (sem como decidir)   -> sem notas
    válida        o resto                                   -> recebe as notas

Notas das válidas:
    sent_jev      POSTURA (Jev), mais jev_confianca e jev_p0..p4
    sent_<s>      SENTIMENTO (config `sentimento`, ex.: pysent), mais
                  variantes de sensibilidade (<s>_<variante>)
    versao_<m>    versão do avaliador que deu a nota

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


def pontuar(analisador, textos):
    """Aplica o analisador; uma falha numa resposta vira NaN, não derruba tudo.
    Devolve (notas, versões, extras) por resposta."""
    notas, versoes, extras, falhas = [], [], [], 0
    for t in textos:
        try:
            notas.append(analisador.analisar(t))
            versoes.append(getattr(analisador, "versao", None))
            extras.append(dict(getattr(analisador, "extras", {})))
        except Exception as e:                                  # noqa: BLE001
            notas.append(np.nan)
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
    # variantes/detalhes: sem o prefixo sent_, para não virarem medidas novas
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

    # 1) sem modelo: erro, bloqueio do provedor, resposta vazia
    erro = df["erro"].notna()
    bloqueio = ~erro & (df["parada"] == "bloqueio")
    vazia = ~erro & ~bloqueio & (df["resposta"].fillna("").str.strip() == "")
    cand = ~erro & ~bloqueio & ~vazia

    # 2) Jev: decide a recusa e, na mesma chamada, mede a postura
    cj = cfg["jev"]
    try:
        jev = sentiment.Jev(cj, cfg["api"], mock=mock)
    except Exception as e:                                      # noqa: BLE001
        raise SystemExit(f"[erro] o Jev não carregou (decide a recusa): {e}")
    res, versoes, falhas = [], [], 0
    for t, p in zip(df.loc[cand, "resposta"], df.loc[cand, "proposta_texto"]):
        try:
            res.append(jev.avaliar(t, p))
            versoes.append(jev.versao)
        except Exception as e:                                  # noqa: BLE001
            res.append((np.nan, np.nan, {}))
            versoes.append(None)
            falhas += 1
            if falhas == 1:
                print(f"[aviso] Jev falhou: {type(e).__name__}: {e}")
    df["jev_p_recusa"] = np.nan
    df.loc[cand, "jev_p_recusa"] = [r[0] for r in res]
    falha_jev = cand & df["jev_p_recusa"].isna()
    pelo_jev = cand & (df["jev_p_recusa"] > cj["limiar_recusa"])

    df["recusa"] = bloqueio | vazia | pelo_jev
    df["recusa_motivo"] = np.select([bloqueio, vazia, pelo_jev],
                                    ["bloqueio", "vazia", "jev"], default=None)
    df["recusa_incerta"] = cand & ((df["jev_p_recusa"] - cj["limiar_recusa"]).abs()
                                   < cj["faixa_incerta"])
    df["falha_jev"] = falha_jev
    validas = cand & ~pelo_jev & ~falha_jev
    print(f"Classificação: {int(erro.sum())} erros, {int(df['recusa'].sum())} recusas "
          f"({df['recusa_motivo'].value_counts().to_dict()}), "
          f"{int(df['recusa_incerta'].sum())} incertas, {falhas} falhas do Jev, "
          f"{int(validas.sum())} válidas")
    if falhas:
        print(f"[aviso] {falhas} respostas sem avaliação do Jev ficaram fora das notas")

    # 3) notas, só nas válidas
    sel = [(r, v) for (r, v), ok in zip(zip(res, versoes), validas[cand]) if ok]
    gravar(df, validas, "jev", [r[1] for r, _ in sel], [v for _, v in sel],
           [r[2] for r, _ in sel])
    print("Postura: jev")

    try:
        a = sentiment.get_analyzer(cfg["sentimento"], mock=mock, cfg=cfg)
    except Exception as e:                                      # noqa: BLE001
        raise SystemExit(f"[erro] medida de sentimento '{cfg['sentimento']}' "
                         f"não carregou: {e}")
    gravar(df, validas, a.nome, *pontuar(a, df.loc[validas, "resposta"]))
    print(f"Sentimento: {a.nome}")

    arq["processed"].mkdir(parents=True, exist_ok=True)
    df.to_csv(arq["scored"], index=False)
    print(f"OK -> {arq['scored']}   ({len(df)} linhas)")


if __name__ == "__main__":
    main()
