"""Pontuação: lê as respostas cruas da execução, classifica cada uma e mede as
três dimensões, gerando processed/scored.csv.

INCREMENTAL, como a coleta: o scored.csv guarda as notas já calculadas e só as
respostas que ainda não têm nota (novas, ou recoletadas depois de um erro)
chamam o Jev e o pysentimiento. A configuração das medidas usada fica em
processed/medidas.json; se ela mudar, o script para — misturar notas de duas
configurações seria como misturar templates. Para repontuar tudo: --refazer.

Classificação (refeita para todas a partir das notas — não chama API):
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
    python score.py --run <pasta> --refazer   # ignora as notas já calculadas
"""
import argparse
import json

import numpy as np
import pandas as pd
import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:          # noqa: BLE001
    pass

from src import loader, sentiment

CHAVE = ["proposta_id", "autor_id", "modelo", "rep"]


def assinatura(cfg):
    """O que define as notas: se isto mudar, as notas antigas não valem mais."""
    return json.loads(json.dumps({"jev": cfg["jev"], "sentimento": cfg["sentimento"]}))


def notas_anteriores(arq, pasta, cfg):
    """Notas já calculadas nesta pasta, se a configuração das medidas for a
    mesma de quando foram calculadas; senão, para."""
    if not arq["scored"].exists():
        return None
    arq_ass = arq["processed"] / "medidas.json"
    if arq_ass.exists():
        antes = json.loads(arq_ass.read_text(encoding="utf-8"))
    else:   # pontuado antes de existir o medidas.json: vale a cópia do config
        antes = assinatura(yaml.safe_load(
            open(pasta / "config" / "config.yaml", encoding="utf-8")))
    if antes != assinatura(cfg):
        raise SystemExit("[erro] a configuração das medidas (bloco `jev` ou "
                         "`sentimento`) mudou desde a última pontuação desta pasta. "
                         "Use --refazer para repontuar tudo com a configuração atual.")
    return pd.read_csv(arq["scored"])


def colunas_de_nota(colunas, nome_sent):
    """Colunas que guardam notas (não a classificação, que é refeita)."""
    return [c for c in colunas
            if c.startswith(("jev_", "sent_", "versao_", f"{nome_sent}_"))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="pasta da execução (padrão: a mais recente)")
    ap.add_argument("--mock", action="store_true", help="usa results/mock/")
    ap.add_argument("--refazer", action="store_true",
                    help="ignora as notas já calculadas e repontua tudo")
    args = ap.parse_args()

    cfg = loader.carregar_config()
    pasta = loader.pasta_run(cfg, args.run, args.mock)
    arq = loader.arquivos(pasta)
    linhas = [json.loads(l) for l in open(arq["raw"], encoding="utf-8")]
    df = pd.DataFrame(linhas)
    mock = bool(df["mock"].any())
    cj = cfg["jev"]

    try:
        sent = sentiment.get_analyzer(cfg["sentimento"], mock=mock, cfg=cfg)
    except Exception as e:                                      # noqa: BLE001
        raise SystemExit(f"[erro] medida de sentimento '{cfg['sentimento']}' "
                         f"não carregou: {e}")
    s = sent.nome

    # notas já calculadas (por proposta × autor × modelo × repetição)
    ant = None if args.refazer else notas_anteriores(arq, pasta, cfg)
    if ant is not None:
        cols = colunas_de_nota(ant.columns, s)
        df = df.merge(ant[CHAVE + cols], on=CHAVE, how="left")
    for c in ["jev_p_recusa", "sent_jev", f"sent_{s}"]:
        if c not in df:
            df[c] = np.nan
    for c in ["versao_jev", f"versao_{s}"]:
        if c not in df:
            df[c] = None
        df[c] = df[c].astype(object)

    # 1) sem modelo: erro, bloqueio do provedor, resposta vazia
    erro = df["erro"].notna()
    bloqueio = ~erro & (df["parada"] == "bloqueio")
    vazia = ~erro & ~bloqueio & (df["resposta"].fillna("").str.strip() == "")
    cand = ~erro & ~bloqueio & ~vazia

    # 2) Jev, só onde ainda não há nota: decide a recusa e mede a postura
    faltam = df.index[cand & df["jev_p_recusa"].isna()]
    postura_nova, extras_novos, falhas = {}, {}, 0
    if len(faltam):
        try:
            jev = sentiment.Jev(cj, cfg["api"], mock=mock)
        except Exception as e:                                  # noqa: BLE001
            raise SystemExit(f"[erro] o Jev não carregou (decide a recusa): {e}")
        for i in faltam:
            try:
                p_rec, postura, extras = jev.avaliar(df.at[i, "resposta"],
                                                     df.at[i, "proposta_texto"])
            except Exception as e:                              # noqa: BLE001
                falhas += 1
                if falhas == 1:
                    print(f"[aviso] Jev falhou: {type(e).__name__}: {e}")
                continue
            df.at[i, "jev_p_recusa"] = p_rec
            postura_nova[i], extras_novos[i] = postura, extras
            df.at[i, "versao_jev"] = jev.versao
    print(f"Jev: {int(cand.sum()) - len(faltam)} notas reaproveitadas, "
          f"{len(faltam)} chamadas novas")

    # 3) classificação (todas, a partir das notas)
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
          f"{int(df['recusa_incerta'].sum())} incertas, {int(falha_jev.sum())} sem "
          f"avaliação do Jev, {int(validas.sum())} válidas")

    # 4) postura das respostas novas válidas (as recusas ficam sem nota)
    for i, postura in postura_nova.items():
        if validas[i]:
            df.at[i, "sent_jev"] = postura
            for k, v in extras_novos[i].items():
                df.loc[i, f"jev_{k}"] = v

    # 5) sentimento, só nas válidas ainda sem nota
    faltam_s = df.index[validas & df[f"sent_{s}"].isna()]
    for i in faltam_s:
        try:
            df.at[i, f"sent_{s}"] = sent.analisar(df.at[i, "resposta"])
        except Exception as e:                                  # noqa: BLE001
            print(f"[aviso] {s} falhou: {type(e).__name__}: {e}")
            continue
        df.at[i, f"versao_{s}"] = getattr(sent, "versao", None)
        for k, v in getattr(sent, "extras", {}).items():
            df.loc[i, f"{s}_{k}"] = v
    print(f"Sentimento ({s}): {int(validas.sum()) - len(faltam_s)} notas "
          f"reaproveitadas, {len(faltam_s)} calculadas")

    arq["processed"].mkdir(parents=True, exist_ok=True)
    df.to_csv(arq["scored"], index=False)
    (arq["processed"] / "medidas.json").write_text(
        json.dumps(assinatura(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {arq['scored']}   ({len(df)} linhas)")


if __name__ == "__main__":
    main()
