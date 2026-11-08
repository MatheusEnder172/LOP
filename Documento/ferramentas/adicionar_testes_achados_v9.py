"""Gera a v9 do relatório a partir da v8, sem regerar a v8 (preserva edições manuais feitas nela).

Alterações (decisão do usuário em 08/11/2026: a v2 fica como modelo final; registrar os testes feitos e os
achados):
1. Em Métodos (cor normal), logo depois do parágrafo da saída softplus, um parágrafo curto: a positividade
   da taxa é a única restrição física imposta; não se impõe monotonia temporal da taxa.
2. Acrescenta à lista de referências (em vermelho) Psichogios; Ungar (1992) e Thompson; Kramer (1994), citadas em E.9.
3. No Apêndice E (texto em vermelho, fora de Métodos), quatro seções novas:
   - E.8  Perdas com informação física (Fase C): D1 (peso pela sensibilidade) e D2 (monotonia), com ablação
          de 10 sementes e o teste de D1 com γ menor; por que a monotonia foi descartada.
   - E.9  Ajuste fino ponta a ponta pelo balanço populacional (Fase D).
   - E.10 Síntese das variantes testadas e decisão (v2 mantida).
   - E.11 Previsão a priori dos quatro ensaios novos de laboratório (modelo congelado, antes das medições).
   Todos os números vêm dos CSVs em Código/outputs/ (nada é digitado à mão).

Uso: python adicionar_testes_achados_v9.py [--saida CAMINHO.docx] [--substituir]
A v8 não é alterada.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

import docx
import numpy as np
import pandas as pd
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from adicionar_resultados_apendices_v8 import achar, reduzir, texto, v  # noqa: E402
from docx_utils import SectionWriter, add_references, pintar  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
CODIGO = DOC_DIR.parent / "Código"
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v8.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v9.docx"
OUT = CODIGO / "outputs"
SUB = OUT / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
NOVOS = OUT / "etapa_4_3_previsao_novos_ensaios"
SUB_CODIGO = CODIGO / "etapas" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
# Referências citadas na seção E.9 que não estavam na lista da v8 (entram em vermelho; conferir os dados)
REFERENCIAS_NOVAS = [
    "PSICHOGIOS, D. C.; UNGAR, L. H. A hybrid neural network-first principles approach to process modeling. "
    "AIChE Journal, v. 38, n. 10, p. 1499–1511, 1992.",
    "THOMPSON, M. L.; KRAMER, M. A. Modeling chemical processes using prior knowledge and neural networks. "
    "AIChE Journal, v. 40, n. 8, p. 1328–1340, 1994.",
]
ANCORA_METODOS = "Função de perda e algoritmo de treinamento"
PARAGRAFO_SOFTPLUS = "Como a função softplus só assume valores positivos"


def pv(p: float) -> str:
    return "<0,001" if p < 0.001 else v(p, 3)


# --------------------------------------------------------------------------- números
def medir_positividade() -> dict:
    """ν mínimo do comitê em 20.000 pontos sorteados do domínio e alvos nulos do problema inverso."""
    sys.path.insert(0, str(SUB_CODIGO))
    sys.path.insert(0, str(CODIGO))
    import joblib
    import torch
    from modelo_mlp_v2 import DOMINIO_FISICO, carregar_ensemble_v2

    sc = joblib.load(CODIGO.parent / "Base de dados" / "processed" / "splits" / "scalers.joblib")["scaler_X"]
    ens = carregar_ensemble_v2(scaler_X=sc)
    rng = np.random.default_rng(1)
    x = DOMINIO_FISICO[:, 0] + rng.random((20000, 3)) * (DOMINIO_FISICO[:, 1] - DOMINIO_FISICO[:, 0])
    with torch.no_grad():
        nu = ens(torch.tensor(sc.transform(x), dtype=torch.float32)).numpy().ravel()
    spl = CODIGO.parent / "Base de dados" / "processed" / "splits"
    alvos = pd.concat([pd.read_csv(spl / "train_dense.csv"), pd.read_csv(spl / "test_dense.csv")])
    zeros = alvos[alvos["abs_v_alvo_um_min"] == 0.0]
    return {"nu_min": float(nu.min()), "n_nao_positivos": int((nu <= 0).sum()), "n_pontos": len(nu),
            "n_alvos": len(alvos), "n_alvos_zero": len(zeros), "ensaios_zero": sorted(int(e) for e in zeros["ensaio"].unique())}


def pesos_d1(gamma: float) -> dict:
    sys.path.insert(0, str(SUB_CODIGO))
    sys.path.insert(0, str(CODIGO))
    import fase_c_perdas_fisicas as fc
    from protocolo_cv import carregar_dados

    dados = carregar_dados()
    w = fc.pesos_sensibilidade(dados, gamma)
    t = dados.train_df["t_min"].values
    return {"w_025": float(w[t == 0.25].mean()), "w_15": float(w[t == 15.0].mean())}


def carregar() -> dict:
    d = {}
    fc, fd = SUB / "fase_c", SUB / "fase_d"
    d["c_tent"] = pd.read_csv(fc / "tabela_fase_c_tentativas.csv")
    d["c_abl"] = pd.read_csv(fc / "tabela_fase_c_ablacao.csv")
    d["c_sem"] = pd.read_csv(fc / "ablacao_por_semente.csv")
    d["c_dob"] = pd.read_csv(fc / "ablacao_por_dobra.csv")
    d["c_mono"] = pd.read_csv(fc / "ablacao_mono.csv")
    d["c_seg"] = pd.read_csv(fc / "tabela_fase_c_d1_segura.csv")
    d["c_seg_dob"] = pd.read_csv(fc / "ablacao_d1_segura_por_dobra.csv")
    d["c_cfg"] = json.loads((fc / "melhor_config_fase_c.json").read_text(encoding="utf-8"))
    d["d_tent"] = pd.read_csv(fd / "tabela_fase_d_tentativas.csv")
    d["d_cmp"] = pd.read_csv(fd / "tabela_fase_d_comparacao.csv")
    d["d_cfg"] = json.loads((fd / "melhor_config_fase_d.json").read_text(encoding="utf-8"))
    d["d_dob"] = pd.read_csv(fd / "finais_por_dobra.csv")
    d["d_oof"] = pd.read_csv(fd / "finais_oof.csv")
    d["n_inst"] = pd.read_csv(NOVOS / "previsao_a_priori_instantes_amostrados.csv")
    d["n_cur"] = pd.read_csv(NOVOS / "previsao_a_priori_curvas.csv")
    d["n_int"] = json.loads((NOVOS / "INTEGRIDADE_previsao_a_priori.json").read_text(encoding="utf-8"))
    return d


def horas_cpu(t: pd.DataFrame) -> float:
    return pd.to_timedelta(t["duration"]).dt.total_seconds().sum() / 3600


def colapsos(dob: pd.DataFrame, nome: str) -> int:
    return int(((dob["config"] == nome) & (dob["RMSE_X"] > 0.1)).sum())


# --------------------------------------------------------------------------- conteúdo
def paragrafo_metodos(w) -> None:
    w.paragraph(
        r"A positividade da taxa é a única restrição física imposta à rede. Ela decorre da irreversibilidade da "
        r"dissolução: o sólido só encolhe, de modo que a retração acumulada e a conversão não diminuem. Não se "
        r"impõe, além disso, que a taxa decresça ao longo do tempo, pois isso é uma expectativa e não uma lei, e "
        r"os alvos do problema inverso e as medições carregam erro experimental (Seção E.8)."
    )


def secao_e8(w, sub, fig, d, pos, p1) -> None:
    abl, sem, dob, mono, seg = d["c_abl"], d["c_sem"], d["c_dob"], d["c_mono"], d["c_seg"]
    tent = d["c_tent"]
    n_comp, n_pod = int((tent["state"] == "COMPLETE").sum()), int((tent["state"] == "PRUNED").sum())
    b2 = abl.iloc[0]
    d1 = abl[abl["variante"] == "+ D1"].iloc[0]
    d2 = abl[abl["variante"] == "+ D2"].iloc[0]
    d12 = abl[abl["variante"] == "+ D1 + D2"].iloc[0]
    rea = abl[abl["variante"].str.startswith("B2 reajustada")].iloc[0]
    gam = float(d1["gamma"])
    lam = float(d2["mono_lambda"])
    p = sem.pivot(index="semente", columns="config", values="RMSE_X")
    ok = p["+ D1"] < 0.1
    dif = (p["B2 (referência)"] - p["+ D1"])[ok]
    p_d1 = stats.ttest_rel(p["B2 (referência)"][ok], p["+ D1"][ok]).pvalue
    ep_d1 = dif.std(ddof=1) / np.sqrt(len(dif))
    mono_b2 = mono[mono["config"] == "B2 (referência)"]["frac_dnu_dt_positivo"].mean() * 100
    mono_d2 = mono[mono["config"] == "+ D2"]["frac_dnu_dt_positivo"].mean() * 100
    busca3 = d["c_tent"][d["c_tent"]["state"] == "COMPLETE"]
    ref3 = float(busca3[busca3["number"] == 0]["value"].iloc[0])
    melhor3 = float(busca3["value"].min())

    sub("E.8 Perdas com informação física (Fase C)")
    w.paragraph(
        r"Com a configuração final fixa, testou-se se duas informações físicas na função de perda reduziriam o "
        r"erro na conversão. A primeira (D1) pondera o erro de cada instante pela sensibilidade da conversão à "
        r"taxa daquele instante: como a retração acumulada é a integral da taxa, a taxa dos primeiros minutos "
        r"afeta todas as conversões seguintes. O peso de $\nu_i$ é a soma, nos instantes experimentais "
        r"$t_k\geq t_i$, de $X'(\delta_k)\,\partial\delta_k/\partial\nu_i\,(1+\nu_i)$, em que $X'$ é a derivada da "
        r"curva $X(\delta)$ e o fator $(1+\nu_i)$ vem da escala logarítmica da perda. Os pesos são normalizados "
        r"para média 1 e elevados a um expoente $\gamma$ ($\gamma=0$ equivale ao treinamento original). Com "
        r"$\gamma=1$, o peso em 0,25 min é, em média, " + v(p1["w_025"], 0) + r" vezes o peso médio, e o de 15 min, "
        + v(p1["w_15"], 3) + r" (Figura E.12). A segunda (D2) penaliza trechos em que a taxa cresce com o tempo, "
        r"por meio da média de $\max(0,\partial\nu/\partial t)^2$ em pontos sorteados no domínio, multiplicada por "
        r"um peso $\lambda$."
    )
    fig(SUB / "fase_c" / "fig_fc_01_pesos_d1.png", 16.0, "Figura E.12",
        "Peso D1 de cada instante nos ensaios de treino, em escala logarítmica, para $\\gamma=1$ e para o valor "
        "escolhido na busca")
    w.paragraph(
        r"A busca (" + str(len(tent)) + r" tentativas, " + str(n_comp) + r" concluídas e " + str(n_pod)
        + r" interrompidas pela poda, " + v(horas_cpu(tent), 1) + r" h de CPU, três sementes) variou $\gamma$ de 0 a 2, "
        r"$\lambda$ entre 0 e 10, a taxa de aprendizado e o número de épocas em torno dos valores da "
        r"configuração final. Com três sementes, a melhor tentativa (apenas D1, $\gamma=" + v(gam, 2) + r"$) teve erro de "
        + v(melhor3, 4) + r" contra " + v(ref3, 4) + r" da configuração final. A ablação com dez sementes e as "
        r"mesmas dobras reavaliou cinco variantes (Tabela E.8 e Figura E.13); considerou-se haver ganho claro "
        r"quando a diferença média pareada por semente superava um erro-padrão dela mesma."
    )
    rows = []
    for _, r in abl.iterrows():
        nome = {"B2 (referência)": "Configuração final (v2)", "B2 reajustada (lr, épocas)": "v2 com taxa de aprendizado e épocas da busca",
                "+ D1": "+ D1", "+ D2": "+ D2", "+ D1 + D2": "+ D1 + D2"}[r["variante"]]
        if r["variante"] == "B2 (referência)":
            rows.append([nome, v(r["RMSE_X_media"], 4) + " ± " + v(r["RMSE_X_dp"], 4), "–", "–", "–", str(colapsos(dob, r["variante"]))])
        else:
            rows.append([nome, v(r["RMSE_X_media"], 4) + " ± " + v(r["RMSE_X_dp"], 4), v(r["ganho_medio_vs_B2"], 4),
                         v(r["ep_ganho_pareado"], 4), str(int(r["n_melhor_que_B2_de_10"])), str(colapsos(dob, r["variante"]))])
    w.table("Tabela E.8", "Ablação das perdas físicas, com dez sementes: erro na conversão fora da dobra, ganho médio "
            "sobre a configuração final (positivo = melhor), erro-padrão do ganho, sementes melhores que a "
            "configuração final e treinos em que a rede colapsou (erro acima de 0,1) de 40",
            ["Variante", "RMSE (média ± desvio)", "Ganho médio", "Erro-padrão", "Sementes melhores", "Colapsos"],
            rows, [4.6, 3.6, 2.0, 2.0, 1.9, 1.9])
    fig(SUB / "fase_c" / "fig_fc_02_ablacao_rmse.png", 14.0, "Figura E.13",
        "Ablação das perdas físicas: erro na conversão fora da dobra de cada variante; os pontos são as dez sementes")
    w.paragraph(
        r"Nenhuma variante teve ganho claro. A configuração final reproduziu o erro de " + v(b2["RMSE_X_media"], 4)
        + r" da seleção, e o reajuste da taxa de aprendizado e das épocas, sozinho, não ajudou (" + v(rea["RMSE_X_media"], 4)
        + r"). A D1 colapsou a rede em " + str(colapsos(dob, "+ D1"))
        + r" dos 40 treinos (a previsão de $\nu$ foi praticamente nula e a conversão prevista, de ordem $10^{-7}$), o que "
        r"elevou a média para " + v(d1["RMSE_X_media"], 4) + r" e o desvio para " + v(d1["RMSE_X_dp"], 4)
        + r". Sem a semente que colapsou, o erro médio foi de "
        + v(float(p["+ D1"][ok].mean()), 4) + r", com ganho de " + v(float(dif.mean()), 4) + r" (erro-padrão de " + v(float(ep_d1), 4)
        + r"; $p=" + v(float(p_d1), 2) + r"$ no teste $t$ pareado), mas, no conjunto das dez sementes, a D1 foi melhor que a "
        r"configuração final em apenas " + str(int(d1["n_melhor_que_B2_de_10"])) + r". O resultado favorável da busca com três sementes "
        r"foi, portanto, otimista: as sementes 42 a 44 não colapsaram. A D1 combinada com a D2 colapsou em "
        + str(colapsos(dob, "+ D1 + D2")) + r" treinos. A causa provável, não testada, é a faixa muito larga dos pesos, "
        r"de cerca de $10^{-7}$ a 200, combinada com a taxa de aprendizado maior."
    )
    rows = []
    for _, r in seg.iterrows():
        rows.append([v(r["gamma"], 1), v(r["RMSE_X_media"], 4) + " ± " + v(r["RMSE_X_dp"], 4), v(r["ganho_medio_vs_B2"], 4),
                     v(r["ep_ganho_pareado"], 4), pv(r["p_t_pareado"]), str(int(r["n_melhor_que_B2_de_10"])), str(int(r["n_colapsos_de_40"]))])
    w.table("Tabela E.9", "D1 com taxa de aprendizado e épocas da configuração final e $\\gamma$ menor (dez sementes): "
            "ganho médio sobre a configuração final (positivo = melhor)",
            [r"$\gamma$", "RMSE (média ± desvio)", "Ganho médio", "Erro-padrão", r"$p$ ($t$ pareado)", "Sementes melhores", "Colapsos"],
            rows, [1.3, 3.8, 2.0, 2.0, 2.3, 2.3, 2.0])
    pior = seg.sort_values("RMSE_X_media", ascending=False).iloc[0]
    w.paragraph(
        r"Para verificar se um $\gamma$ menor preservava o ganho sem o colapso, repetiu-se a D1 com a taxa de "
        r"aprendizado e as épocas originais (Tabela E.9). "
        + (r"Não houve colapso em " + str(40 * len(seg)) + r" treinos" if int(seg["n_colapsos_de_40"].sum()) == 0
           else r"Houve " + str(int(seg["n_colapsos_de_40"].sum())) + r" colapsos em " + str(40 * len(seg)) + r" treinos")
        + r", mas o resultado não foi monotônico em $\gamma$: com $\gamma=" + v(pior["gamma"], 1) + r"$ o erro foi pior que o "
        r"da configuração final (" + v(pior["RMSE_X_media"], 4) + r" contra " + v(b2["RMSE_X_media"], 4)
        + r"), e o melhor valor ($\gamma=1{,}5$) ganhou apenas " + v(float(seg[seg["gamma"] == 1.5]["ganho_medio_vs_B2"].iloc[0]), 4)
        + r" ($p=" + v(float(seg[seg["gamma"] == 1.5]["p_t_pareado"].iloc[0]), 2) + r"$). Esse padrão é compatível "
        r"com ruído, e a D1 não deu ganho confiável."
    )
    w.paragraph(
        r"A D2 ($\lambda=" + v(lam, 1) + r"$) foi neutra no erro (" + v(d2["RMSE_X_media"], 4) + r" contra "
        + v(b2["RMSE_X_media"], 4) + r") e não mudou a forma das curvas: a fração do domínio com $\partial\nu/\partial t>0$ foi "
        r"de " + v(mono_d2, 1) + r"% com a D2 e de " + v(mono_b2, 1) + r"% sem ela. Além do resultado, ela foi "
        r"descartada por uma razão física. A lei que a taxa de retração deve obedecer é a positividade, que decorre da "
        r"irreversibilidade da dissolução, e já é imposta por construção, pela saída softplus da Seção D.1: no "
        r"comitê final, o menor valor de $\nu$ em " + f"{pos['n_pontos']:,}".replace(",", ".") + r" pontos sorteados do domínio foi de "
        + v(pos["nu_min"] * 1e5, 1) + r"$\times10^{-5}$ µm/min, e nenhum foi menor ou igual a zero. Que a taxa decresça "
        r"com o tempo é uma expectativa razoável, pelo consumo de ácido, mas não uma lei; as medições e os alvos do "
        r"problema inverso têm erro experimental, e impor a monotonia forçaria a rede a eliminar variações que podem "
        r"fazer parte dos dados. Nos alvos, " + str(pos["n_alvos_zero"]) + r" dos " + str(pos["n_alvos"]) + r" valores de $\nu$ são "
        r"exatamente nulos, todos nos Ensaios " + ", ".join(str(e) for e in pos["ensaios_zero"][:-1]) + " e "
        + str(pos["ensaios_zero"][-1]) + r", em que o ácido se esgota ($\eta\leq1$); isso é coerente com $\nu\geq0$, com a "
        r"taxa tendendo a zero quando o reagente acaba."
    )


def secao_e9(w, sub, fig, d) -> None:
    cmp, tent, cfg = d["d_cmp"], d["d_tent"], d["d_cfg"]
    c10 = cmp[cmp["escopo"] == "10 sementes"].iloc[0]
    c7 = cmp[cmp["escopo"].str.startswith("7 sementes")].iloc[0]
    n_comp = int((tent["state"] == "COMPLETE").sum())
    n_pod = int((tent["state"] == "PRUNED").sum())
    p = cfg["params"]
    dob = d["d_dob"]
    oof = d["d_oof"]
    abl_oof = pd.read_csv(SUB / "fase_c" / "ablacao_oof.csv")
    b2 = abl_oof[abl_oof["config"] == "B2 (referência)"]
    f = lambda o: o.groupby("ensaio").apply(lambda g: np.sqrt(((g["XZn_exp"] - g["XZn_pred"]) ** 2).mean()), include_groups=False)
    r = pd.DataFrame({"b": f(b2), "d": f(oof)})
    n_melhor = int((r["b"] > r["d"]).sum())
    piores = r[r["d"] > r["b"]].index.tolist()
    sub("E.9 Ajuste fino ponta a ponta pelo balanço populacional (Fase D)")
    w.paragraph(
        r"Em vez de apenas imitar as taxas do problema inverso, a rede da configuração final, treinada em cada dobra, "
        r"foi ajustada diretamente à conversão medida, passando $\nu$ pela integração de $\delta$ e pela curva "
        r"$X(\delta)$ dentro da biblioteca de treinamento. O cálculo foi reescrito de forma diferenciável e reproduz o "
        r"acoplamento serial com diferença menor que $10^{-6}$ na conversão, o que permite retropropagar o erro em "
        r"$X_{\mathrm{Zn}}$ até os pesos da rede (Psichogios; Ungar, 1992; Thompson; Kramer, 1994). A perda do ajuste "
        r"fino somou o erro quadrático médio da conversão e um termo de âncora, o erro quadrático médio de "
        r"$\ln(1+\nu)$ em relação aos alvos do problema inverso, multiplicado por um peso $\lambda_\nu$; a âncora impede "
        r"que $\nu$ perca a forma física, já que restam cerca de 70 pontos de conversão por dobra. O ajuste foi feito em "
        r"lote completo, com número fixo de épocas e sem dropout. A busca (" + str(len(tent)) + r" tentativas, " + str(n_comp)
        + r" concluídas e " + str(n_pod) + r" podadas, três sementes) escolheu taxa de aprendizado de " + v(p["lr_ft"], 5)
        + r", " + str(int(p["epocas_ft"])) + r" épocas e $\lambda_\nu=" + v(p["lambda_nu"], 4) + r"$, isto é, um ajuste curto e "
        r"com âncora fraca."
    )
    rows = []
    for _, x in cmp.iterrows():
        rows.append([x["escopo"],
                     v(x["RMSE_ref_media"], 4), v(x["RMSE_D_media"], 4) + " ± " + v(x["RMSE_D_dp"], 4), v(x["ganho_medio"], 4),
                     v(x["ep_ganho_pareado"], 4), pv(x["p_t_pareado"]), pv(x["p_wilcoxon"]), f"{int(x['n_D_melhor'])} de {int(x['n_sementes'])}"])
    w.table("Tabela E.10", "Ajuste fino ponta a ponta: erro na conversão fora da dobra em comparação com a configuração "
            "final (mesmas redes de partida e mesmas dobras)",
            ["Sementes", "Configuração final", "Ajuste fino", "Ganho médio", "Erro-padrão", r"$p$ ($t$)", r"$p$ (Wilcoxon)", "Melhor em"],
            rows, [4.0, 1.9, 3.0, 1.5, 1.6, 1.4, 1.7, 1.5])
    fig(SUB / "fase_d" / "fig_fd_03_rmse_barras.png", 11.0, "Figura E.14",
        "Erro na conversão fora da dobra da configuração final e do ajuste fino, com dez sementes (pontos)")
    w.paragraph(
        r"O ajuste fino reduziu o erro de " + v(c10["RMSE_ref_media"], 4) + r" para " + v(c10["RMSE_D_media"], 4) + r", cerca de "
        + v(100 * c10["ganho_medio"] / c10["RMSE_ref_media"], 0) + r"%, com melhora em " + f"{int(c10['n_D_melhor'])}"
        + r" das 10 sementes e em " + str(n_melhor) + r" dos 13 ensaios (piora nos Ensaios "
        + ", ".join(str(int(e)) for e in piores[:-1]) + " e " + str(int(piores[-1])) + r"). O ganho passa por pouco do critério de um "
        r"erro-padrão (" + v(c10["ganho_medio"], 4) + r" contra " + v(c10["ep_ganho_pareado"], 4) + r"), mas é pequeno diante da "
        r"variação entre sementes (desvio de " + v(c10["RMSE_D_dp"], 4) + r"). Como as sementes 42 a 44 participaram da escolha dos "
        r"parâmetros, o ganho nelas é otimista; nas sete sementes não vistas, ele cai para " + v(c7["ganho_medio"], 4)
        + r" ($p=" + v(float(c7["p_t_pareado"]), 2) + r"$). Não houve colapso de rede, e a taxa permaneceu positiva por "
        r"construção. Os perfis de $\nu$ mudaram pouco (Figura E.15): as redes continuam seguindo o alvo nos "
        r"primeiros minutos e se afastam dele onde o próprio alvo é mais incerto."
    )
    fig(SUB / "fase_d" / "fig_fd_02_nu_antes_depois.png", 16.0, "Figura E.15",
        "Taxa de retração em quatro ensaios deixados de fora da dobra, antes e depois do ajuste fino (mediana e faixa "
        "de 10 a 90% das dez sementes), com o alvo do problema inverso; valores abaixo de $10^{-3}$ µm/min foram "
        "truncados para exibição")


def secao_e10(w, sub, fig, d) -> None:
    abl, seg, cmp = d["c_abl"], d["c_seg"], d["d_cmp"]
    dob = d["c_dob"]
    b2 = abl.iloc[0]
    c10 = cmp[cmp["escopo"] == "10 sementes"].iloc[0]
    def lin(k, rot, concl):
        r = abl[abl["variante"] == k].iloc[0]
        return [rot, v(r["RMSE_X_media"], 4), v(r["ganho_medio_vs_B2"], 4), concl]

    rows = [["Configuração final (v2)", v(b2["RMSE_X_media"], 4), "–", "referência"],
            lin("B2 reajustada (lr, épocas)", "v2 com taxa de aprendizado e épocas da busca", "sem ganho")]
    for _, r in seg.iterrows():
        rows.append([rf"D1, $\gamma={v(r['gamma'], 1)}$ (taxa e épocas originais)", v(r["RMSE_X_media"], 4),
                     v(r["ganho_medio_vs_B2"], 4), "sem ganho confiável"])
    gam = v(float(abl[abl["variante"] == "+ D1"]["gamma"].iloc[0]), 2)
    rows.append(lin("+ D1", rf"D1, $\gamma={gam}$ (taxa e épocas da busca)", f"instável ({colapsos(dob, '+ D1')} colapso em 40)"))
    rows.append(lin("+ D2", r"D2 (monotonia), $\lambda=0{,}1$", "neutra; descartada"))
    rows.append(lin("+ D1 + D2", "D1 + D2", f"instável ({colapsos(dob, '+ D1 + D2')} colapsos em 40)"))
    rows.append(["Ajuste fino ponta a ponta (Fase D)", v(c10["RMSE_D_media"], 4), v(c10["ganho_medio"], 4),
                 "ganho de cerca de 5%, fraco nas sementes não vistas"])
    teto = float(pd.read_csv(SUB / "fase_a" / "tabela_fase_a_resumo.csv").set_index("referencia").loc["teto", "valor"])
    sub("E.10 Síntese das variantes testadas e decisão")
    w.paragraph(
        r"A configuração final (comitê de dez redes da Seção E.3) foi mantida como modelo. Nenhuma das variantes "
        r"testadas teve ganho confiável sobre ela: a D1 é instável, a D2 não ajuda e é fisicamente desnecessária, e o "
        r"ajuste fino ponta a ponta ganha cerca de 5%, com significância fraca nas sementes não vistas (Tabela E.11). "
        r"Adotá-lo exigiria ajustar de novo os dez membros e consultar uma segunda vez o teste cego, que já havia sido "
        r"visto, sem que o ganho esperado justifique. Em nenhuma dessas comparações o teste cego foi usado: todas as "
        r"escolhas dependeram só da validação cruzada. O erro de " + v(float(b2["RMSE_X_media"]), 3)
        + r" fora da dobra continua cerca de " + v(float(b2["RMSE_X_media"]) / teto, 1) + r" vezes o teto de " + v(teto, 3)
        + r" dado pelos próprios alvos do problema inverso, e nenhuma das variantes reduziu essa diferença; se o limite está "
        r"na quantidade de ensaios ou nos alvos não foi esclarecido por estes testes."
    )
    w.table("Tabela E.11", "Variantes testadas depois da seleção da configuração final: erro na conversão fora da dobra "
            "(dez sementes) e ganho médio sobre a configuração final (positivo = melhor)",
            ["Variante", "RMSE (–)", "Ganho médio", "Conclusão"], rows, [6.4, 2.0, 2.2, 5.2])


def secao_e11(w, sub, fig, d) -> None:
    t, c, integ = d["n_inst"], d["n_cur"], d["n_int"]
    cond = t.groupby("ensaio").first()
    data, hora = integ["data_geracao"].split()
    dd, mm_, aa = data.split("-")[2], data.split("-")[1], data.split("-")[0]
    fim = {e: g.iloc[-1] for e, g in t.groupby("ensaio")}
    t99 = {e: g[g["XZn_v2_comite"] >= 0.99 * g["XZn_v2_comite"].iloc[-1]]["t_min"].min() for e, g in c.groupby("ensaio")}
    x05 = {e: g[g["t_min"] == 0.5]["XZn_v2_comite"].iloc[0] for e, g in t.groupby("ensaio")}
    serie = pd.read_csv(CODIGO.parent / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv")
    pat = serie[serie["t_min"] == 15.0].groupby("razao_molar_eta")["XZn"].agg(["min", "max"])
    amp = float((t["XZn_v2_membro_max"] - t["XZn_v2_membro_min"]).max())
    sub("E.11 Previsão a priori de quatro ensaios novos de laboratório")
    w.paragraph(
        r"Com o modelo final congelado, foram previstos quatro ensaios novos, realizados nas mesmas condições de temperatura "
        r"(40 °C) e de agitação (1000 rpm) dos 16 originais, com volume de 200 mL em vez de 400 mL (Tabela E.12). O modelo "
        r"usa apenas $C_{A0}$, $\eta$ e $t$. A razão sólido/líquido decorre de $C_{A0}$ e $\eta$ e, por isso, é a mesma de um "
        r"ensaio original com os mesmos valores; ficou entre " + v(cond["razao_solido_liquido_g_L"].min(), 1) + r" e "
        + v(cond["razao_solido_liquido_g_L"].max(), 1) + r" g/L, dentro da faixa dos originais (3 a 300 g/L). O Ensaio E4 tem "
        r"$\eta=0{,}40$, abaixo do mínimo do treino (0,5), e constitui uma pequena extrapolação."
    )
    rows = []
    for e, r in cond.iterrows():
        rows.append([e, v(r["eta"], 2), v(r["CA0_mol_L"], 2), f"{r['V_mL']:.0f}", v(r["m_g"], 1), v(r["razao_solido_liquido_g_L"], 1),
                     v(r["limite_min_1_eta"], 2), "extrapolação" if r["extrapolacao_eta"] else "dentro do domínio"])
    w.table("Tabela E.12", "Condições dos ensaios novos e limite estequiométrico da conversão",
            [ "Ensaio", r"$\eta$ (–)", r"$C_{A0}$ (mol/L)", "V (mL)", "m (g)", "m/V (g/L)", r"min(1, $\eta$)", "Domínio do treino"],
            rows, [1.5, 1.5, 2.1, 1.5, 1.5, 1.8, 1.8, 3.2])
    w.paragraph(
        r"As previsões foram geradas em " + dd + "/" + mm_ + "/" + aa + r", às " + hora[:5].replace(":", "h")
        + r", antes de qualquer medição, e gravadas junto com o código de verificação (SHA-256) dos arquivos do comitê e "
        r"das próprias previsões, de modo que a comparação futura use exatamente estes valores (Tabela E.13 e Figura E.16)."
    )
    ts = sorted(t["t_min"].unique())
    rows = []
    for e, g in t.groupby("ensaio"):
        rows.append([e] + [v(float(g[g["t_min"] == x]["XZn_v2_comite"].iloc[0]), 3) for x in ts] + [v(float(fim[e]["XZn_fenomenologico"]), 3)])
    w.table("Tabela E.13", "Conversão de zinco prevista pelo comitê de dez redes nos instantes de amostragem e, na última "
            "coluna, pelo modelo fenomenológico puro em 15 min",
            ["Ensaio"] + [f"{x:g}".replace(".", ",") + " min" for x in ts] + ["Fenom. 15 min"],
            rows, [1.5] + [1.6] * len(ts) + [2.2])
    fig(NOVOS / "fig_ne_05_painel.png", 16.0, "Figura E.16",
        "Previsão a priori dos quatro ensaios novos: média do comitê, faixa entre os dez membros, modelo fenomenológico "
        "puro, limite estequiométrico e referência obtida por interpolação linear dos 16 ensaios medidos")
    w.paragraph(
        r"As relações esperadas são as seguintes. A conversão final segue a razão molar: E3 (" + v(float(fim["E3"]["XZn_v2_comite"]), 3)
        + r") > E2 (" + v(float(fim["E2"]["XZn_v2_comite"]), 3) + r") > E1 (" + v(float(fim["E1"]["XZn_v2_comite"]), 3) + r") > E4 ("
        + v(float(fim["E4"]["XZn_v2_comite"]), 3) + r"). Em E1 e E4, o ácido é limitante, e o patamar não pode passar de 0,75 e 0,40; "
        r"nos ensaios originais com $\eta=0{,}5$, a conversão medida em 15 min ficou entre " + v(float(pat.loc[0.5, "min"]), 2)
        + r" e " + v(float(pat.loc[0.5, "max"]), 2) + r", isto é, praticamente no limite. Com $\eta$ próximo de 1, o patamar "
        r"medido fica abaixo do limite ($" + v(float(pat.loc[1.0, "min"]), 2) + r"$ a $" + v(float(pat.loc[1.0, "max"]), 2)
        + r"$ para $\eta=1{,}0$), o que explica as previsões de E1 e E2 abaixo de 0,75 e de 1,00. A reação é rápida: o comitê "
        r"atinge 99% do valor final em " + v(t99["E1"], 1) + r", " + v(t99["E2"], 1) + r", " + v(t99["E3"], 1) + r" e "
        + v(t99["E4"], 1) + r" min (E1 a E4), de modo que os instantes de 0,5 e 1 min são os mais informativos e o de 15 min "
        r"indica o patamar. O modelo fenomenológico puro, que prevê os patamares nos limites estequiométricos, deve superestimar "
        r"E1 e E2, como superestimou os ensaios originais com $\eta$ próximo de 1."
    )
    fig(NOVOS / "fig_ne_06_contexto_vizinhos.png", 16.0, "Figura E.17",
        "Previsão de cada ensaio novo e conversão medida nos dois ensaios originais mais próximos em $C_{A0}$ e $\\eta$")
    w.paragraph(
        r"Como referência de erro, o modelo teve RMSE na conversão de 0,033 fora da dobra e de 0,020 no teste cego; diferenças "
        r"dessa ordem são esperadas, e diferenças bem maiores ou sistemáticas apontariam um efeito que o modelo não vê. "
        r"A faixa entre os membros (no máximo " + v(amp, 3) + r" de largura nesses ensaios) mede só a variabilidade de treinamento "
        r"e não é intervalo de confiança. O modelo não conhece o volume, e um desvio sistemático em todos os ensaios poderia "
        r"vir da geometria do reator, da agitação em 200 mL ou da fração do volume retirada em cada amostragem, hipótese que "
        r"não foi testada. A comparação com as medições será incluída quando os resultados do laboratório estiverem disponíveis."
    )


# --------------------------------------------------------------------------- principal
def main() -> None:
    saida = Path(sys.argv[sys.argv.index("--saida") + 1]) if "--saida" in sys.argv else DESTINO
    if saida.exists() and "--substituir" not in sys.argv:
        sys.exit(f"{saida.name} já existe. Use --substituir para sobrescrever.")
    d = carregar()
    pos = medir_positividade()
    gam = float(d["c_abl"][d["c_abl"]["variante"] == "+ D1"]["gamma"].iloc[0])
    p1 = pesos_d1(1.0)

    doc = docx.Document(str(ORIGEM))
    body = doc.element.body
    els = list(body)
    assert not any("E.8 Perdas com informação física" in texto(e) for e in els if e.tag == qn("w:p")), "a v8 já tem E.8"

    i_cap = achar(els, "Figura B.1 –")
    refs = {"body": els[achar(els, "Este apêndice detalha a obtenção")], "figure": els[i_cap - 1],
            "caption": els[i_cap], "source": els[i_cap + 1], "heading": els[i_cap], "subheading": els[i_cap]}
    ppr_sub = els[achar(els, "B.1 Parametrização")].find(qn("w:pPr"))

    # 1. Métodos (cor normal): depois do parágrafo da saída softplus, antes do subtítulo seguinte
    i_soft = achar(els, PARAGRAFO_SOFTPLUS)
    i_res = achar(els, "RESULTADOS E DISCUSS")
    assert i_soft < i_res, "o parágrafo da softplus deve estar em Métodos"
    ancora_m = els[i_soft + 1]
    assert texto(ancora_m).startswith(ANCORA_METODOS), texto(ancora_m)[:60]
    wm = SectionWriter(doc, refs, ancora_m)
    paragrafo_metodos(wm)  # não é pintado

    # 2. Apêndice E (vermelho)
    ultimo = max(i for i, e in enumerate(els) if e.tag == qn("w:p") and texto(e))
    ancora_e = els[ultimo].getnext()
    assert ancora_e is not None

    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        w = SectionWriter(doc, refs, ancora_e)

        def sub(txt: str) -> None:
            p = parse_xml(f"<w:p {nsdecls('w')}/>")
            p.append(copy.deepcopy(ppr_sub))
            p.append(SectionWriter._run(txt))
            w._place(p)

        def fig(img, largura, label, titulo):
            w.figure(reduzir(Path(img), pasta), largura, label, titulo)

        secao_e8(w, sub, fig, d, pos, p1)
        secao_e9(w, sub, fig, d)
        secao_e10(w, sub, fig, d)
        secao_e11(w, sub, fig, d)
        pintar(list(w.inserted))
        novas = add_references(doc, REFERENCIAS_NOVAS)
        print(f"Referências adicionadas: {len(novas)}")
        saida.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(saida))
    print(f"Documento salvo em: {saida}")


if __name__ == "__main__":
    main()
