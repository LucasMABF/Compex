"""EXPLORATÓRIO (não pré-registrado): respostas que contestam a atribuição de
autoria ("Lula nunca defendeu essa proposta", "a premissa está incorreta").

1. Marca as respostas que contestam (expressões regulares nos primeiros 600
   caracteres; aproximado: precisão ~13/14 numa amostra lida, deixa passar
   formulações menos comuns, então subestima).
2. Mostra quanto cada modelo contesta, por categoria de autor e por
   congruência (político com proposta do próprio espectro ou do oposto).
3. Sensibilidade: refaz a análise (analyze.py) sem essas respostas.

Saídas em <execução>/exploratorio/:
    contestacao.csv                 a marcação, resposta a resposta
    sem_contestacao/processed/*.csv a análise sem as respostas que contestam

Uso:
    python exploratorio/contestacao.py --run results/runs/<pasta>
"""
import argparse
import pathlib
import re
import subprocess
import sys
import warnings

import pandas as pd
import yaml

warnings.filterwarnings("ignore", "This pattern is interpreted")   # grupos do regex
CHAVE = ["proposta_id", "autor_id", "modelo", "rep"]
PADRAO = re.compile(
    r"não (tenho|há|encontrei|possuo|existem?) (nenhum |qualquer )?"
    r"(informaç|registro|evidênc|conhecimento|indicaç|declaraç)"
    r"|nunca (defendeu|propôs|apoiou)|não (corresponde|reflete|condiz|é compatível)"
    r"|premissa|não é conhecid|não tem histórico|posições? públicas? conhecidas?"
    r"|atribuída? a (ele|ela)|não (parece )?(ser|é) (uma )?(posição|proposta) (dele|dela|de )",
    re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    pasta = pathlib.Path(ap.parse_args().run)
    s = pd.read_csv(pasta / "processed" / "scored.csv")
    props = {p["id"]: p["orientacao"] for p in
             yaml.safe_load(open(pasta / "config" / "proposals.yaml"))["propostas"]}

    com_autor = s["categoria"] != "controle"
    s["contesta"] = com_autor & s["resposta"].fillna("").str[:600].str.contains(PADRAO)
    orient = s["proposta_id"].map(props)
    s["congruencia"] = None
    pol = s["categoria"] == "politico"
    s.loc[pol, "congruencia"] = (orient[pol] == s.loc[pol, "espectro"]).map(
        {True: "mesmo espectro", False: "espectro oposto"})
    s.loc[pol & (orient == "transversal"), "congruencia"] = "transversal"

    pct = lambda d, col: (d.pivot_table(index="modelo", columns=col, values="contesta",
                                        aggfunc="mean") * 100).round(0)
    print("% das respostas que contestam a autoria, por categoria do autor:")
    print(pct(s[com_autor], "categoria"))
    print("\n% com políticos reais, pela orientação da proposta:")
    print(pct(s[pol], "congruencia"))
    print("\n% das recusas que contestam:",
          s[s["recusa"]].groupby("modelo")["contesta"].mean().mul(100).round(0).to_dict())

    out = pasta / "exploratorio"
    out.mkdir(exist_ok=True)
    s[CHAVE + ["contesta", "congruencia"]].to_csv(out / "contestacao.csv", index=False)

    # sensibilidade: a mesma análise sem as respostas que contestam
    sens = out / "sem_contestacao"
    (sens / "processed").mkdir(parents=True, exist_ok=True)
    s[~s["contesta"]].drop(columns=["contesta", "congruencia"]).to_csv(
        sens / "processed" / "scored.csv", index=False)
    print(f"\nremovidas na sensibilidade: {s.groupby('modelo')['contesta'].sum().to_dict()}")
    raiz = pathlib.Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(raiz / "analyze.py"), "--run", str(sens)],
                   check=True, cwd=raiz, stdout=subprocess.DEVNULL)
    print(f"OK -> {out}/")


if __name__ == "__main__":
    main()
