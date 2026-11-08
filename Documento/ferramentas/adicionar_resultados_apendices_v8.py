"""Gera a v8 do relatório a partir da v7, sem regerar a v7 (preserva edições manuais feitas nela).

Alterações:
1. Remove da Metodologia o parágrafo de abertura do híbrido serial que repete a revisão bibliográfica
   (decisão do usuário em 07/11/2026).
2. Acrescenta aos apêndices (texto em vermelho) os resultados das análises já concluídas, para
   justificar as escolhas de modelagem:
   - Apêndice B, seção B.5: qualidade da reconstrução do problema inverso (16 ensaios) e parâmetros
     ótimos, com os limites atingidos.
   - Apêndice D, seção D.3: resultados do treinamento do comitê de 10 redes.
   - Apêndice E, seções E.5 a E.7: linha de base com o protocolo corrigido (Fase A), resultados da busca
     de hiperparâmetros (Fases B e B2) e desempenho do modelo final no teste cego (Fase E mínima).
   Todos os números vêm dos CSVs em Código/outputs/ (nada é digitado à mão).
3. As análises ainda em andamento (Fases C e D, escolha dos pesos do problema inverso, ensaios novos de
   laboratório) entram depois, quando terminarem.

Uso: python adicionar_resultados_apendices_v8.py [--saida CAMINHO.docx] [--substituir]
A v7 não é alterada.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import docx
import numpy as np
import pandas as pd
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from PIL import Image
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from docx_utils import SectionWriter, pintar  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
CODIGO = DOC_DIR.parent / "Código"
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v7.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v8.docx"
OUT = CODIGO / "outputs"
SUB = OUT / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
FIG_RES = DOC_DIR / "figuras_resultados"

ABERTURA_REMOVIDA = "Conforme discutido na revisão bibliográfica, na arquitetura híbrida serial"
LIMITES = {"a1": (0.0, 250.0), "b1": (0.2, 8.0), "a2": (0.0, 80.0), "b2": (0.02, 4.0), "c": (0.0, 0.03)}


# --------------------------------------------------------------------------- formatação
def v(x: float, n: int = 4) -> str:
    return f"{x:.{n}f}".replace(".", ",").replace("-", "−")


def pct(x: float, n: int = 1) -> str:
    return v(100 * x, n)


def mm(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def mediana_por(df: pd.DataFrame, col: str) -> dict:
    comp = df[df["state"] == "COMPLETE"]
    return comp.groupby(col)["value"].median().to_dict()


# --------------------------------------------------------------------------- dados
def numeros_parametros(configs: dict) -> dict:
    """Número real de parâmetros de cada configuração (modelo montado)."""
    sys.path.insert(0, str(CODIGO / "etapas" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"))
    sys.path.insert(0, str(CODIGO))
    from protocolo_cv import carregar_dados, criar_trainer  # noqa: E402

    dados = carregar_dados()
    return {k: sum(p.numel() for p in criar_trainer(cfg, dados, 42).build_model().parameters())
            for k, cfg in configs.items()}


def carregar_tudo() -> dict:
    import json

    d = {}
    d["inv"] = pd.read_csv(OUT / "etapa_2_1" / "tabela_metricas_otimizacao_inversa.csv").set_index("ensaio")
    d["fa_resumo"] = pd.read_csv(SUB / "fase_a" / "tabela_fase_a_resumo.csv").set_index("referencia")["valor"]
    d["fa_antigo"] = pd.read_csv(SUB / "fase_a" / "tabela_fase_a_protocolo_antigo_por_dobra.csv")
    d["fa_ens"] = pd.read_csv(SUB / "fase_a" / "tabela_fase_a_rmse_por_ensaio.csv").set_index("ensaio")
    d["fb_tent"] = pd.read_csv(SUB / "fase_b" / "tabela_fase_b_tentativas.csv")
    d["fb_fin"] = pd.read_csv(SUB / "fase_b" / "tabela_fase_b_finalistas.csv")
    d["fb2_tent"] = pd.read_csv(SUB / "fase_b2" / "tabela_fase_b2_tentativas.csv")
    d["fb2_fin"] = pd.read_csv(SUB / "fase_b2" / "tabela_fase_b2_finalistas.csv")
    d["fb2_sem"] = pd.read_csv(SUB / "fase_b2" / "finalistas_por_semente.csv")
    d["fe_met"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_metricas_XZn.csv")
    d["fe_ens"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_rmse_por_ensaio.csv")
    d["fe_nu"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_metricas_nu_teste_cego.csv").set_index("Modelo")
    d["fe_mem"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_membros_teste_cego.csv")
    d["fe_trein"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_treino_membros.csv")
    d["cfg_b2"] = json.loads((SUB / "fase_b2" / "melhor_config_fase_b2.json").read_text(encoding="utf-8"))
    return d


# --------------------------------------------------------------------------- utilitários do documento
def texto(e) -> str:
    return "".join(t.text or "" for t in e.iter(qn("w:t"))).strip()


def achar(els, comeco: str, depois_de: int = 0):
    for i in range(depois_de, len(els)):
        if els[i].tag == qn("w:p") and texto(els[i]).startswith(comeco):
            return i
    raise ValueError(f"Parágrafo não encontrado: {comeco!r}")


def reduzir(imagem: Path, pasta: Path, largura: int = 2200) -> Path:
    """Cópia da figura com no máximo `largura` px (≈ 300 DPI em 16 cm), para não inchar o .docx."""
    dest = pasta / imagem.name
    with Image.open(imagem) as im:
        if im.width > largura:
            im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
        im.save(dest, optimize=True)
    return dest


# --------------------------------------------------------------------------- conteúdo
def secao_b5(w, sub, fig, d) -> None:
    inv = d["inv"]
    rmse_glob = float(np.sqrt((inv["RMSE"] ** 2).mean()))
    sub("B.5 Resultados da reconstrução das curvas de conversão")
    w.paragraph(
        r"Com os parâmetros ótimos de cada ensaio, a conversão reconstruída reproduz as sete medições com "
        r"RMSE entre " + v(inv["RMSE"].min(), 4) + r" (Ensaio " + str(int(inv["RMSE"].idxmin())) + r") e "
        + v(inv["RMSE"].max(), 4) + r" (Ensaio " + str(int(inv["RMSE"].idxmax())) + r"), e RMSE global de "
        + v(rmse_glob, 4) + r" nos 112 pontos (Tabela B.4 e Figura B.3). Esse valor é o erro mínimo que o "
        r"modelo híbrido pode ter ao reproduzir as curvas, pois a rede aprende justamente as taxas estimadas "
        r"nesta etapa, e serve de teto de referência nas seções E.5 a E.7."
    )
    fig(FIG_RES / "fig_res_01_reconstrucao_problema_inverso.png", 16.0, "Figura B.3",
        "Conversão de zinco medida (marcadores) e reconstruída pelo problema inverso (linhas) nos 16 ensaios, "
        "agrupados por razão molar; as linhas tracejadas indicam os ensaios de teste cego")
    rows = []
    for e, r in inv.iterrows():
        rows.append([str(e), v(r["CA0_mol_L"], 2), v(r["razao_molar_eta"], 1), v(r["RMSE"], 4), v(r["R2"], 2),
                     v(r["delta_final_um"], 1)])
    w.table("Tabela B.4", "Qualidade da reconstrução da conversão em cada ensaio (7 instantes experimentais) e "
            "retração acumulada ao final",
            ["Ensaio", r"$C_{A0}$ (mol/L)", r"$\eta$ (–)", "RMSE (–)", r"$R^2$ (–)", r"$\delta$(15 min) (µm)"],
            rows, [1.8, 2.6, 2.0, 2.6, 2.4, 3.6])
    ruim = inv.sort_values("R2").head(3)
    w.paragraph(
        r"O coeficiente de determinação por ensaio varia de " + v(inv["R2"].min(), 2) + r" a "
        + v(inv["R2"].max(), 2) + r" e não deve ser lido isoladamente: em ensaios nos quais a conversão medida "
        r"praticamente não varia depois do primeiro minuto, a variância dos dados é pequena e o $R^2$ fica baixo "
        r"ou negativo mesmo com erro absoluto pequeno (nos Ensaios "
        + ", ".join(str(int(e)) for e in ruim.index[:-1]) + " e " + str(int(ruim.index[-1]))
        + r", o RMSE é de no máximo " + v(float(ruim["RMSE"].max()), 3) + r"). Por isso, o RMSE foi adotado como "
        r"medida principal."
    )
    # limites atingidos
    sup, inf = {}, {}
    for e, r in inv.iterrows():
        for p, (lo, hi) in LIMITES.items():
            if abs(r[p] - hi) <= 1e-3 * max(1.0, hi):
                sup.setdefault(e, []).append(p)
            elif abs(r[p] - lo) <= 1e-3 * max(1.0, abs(hi)) and p != "c":
                inf.setdefault(e, []).append(p)
    nome = {"a1": "a₁", "b1": "b₁", "a2": "a₂", "b2": "b₂", "c": "c"}
    rows = []
    for e, r in inv.iterrows():
        marc = ["↑ " + ", ".join(nome[p] for p in sup.get(e, []))] if e in sup else []
        marc += ["↓ " + ", ".join(nome[p] for p in inf.get(e, []))] if e in inf else []
        rows.append([str(e), v(r["a1"], 1), v(r["b1"], 2), v(r["a2"], 1), v(r["b2"], 2), v(r["c"], 3),
                     "; ".join(marc) if marc else "–"])
    w.table("Tabela B.5", "Parâmetros ótimos da taxa de retração em cada ensaio e limites atingidos (↑ limite "
            "superior; ↓ limite inferior)",
            ["Ensaio", r"$a_1$ (µm/min)", r"$b_1$ (min$^{-1}$)", r"$a_2$ (µm/min)", r"$b_2$ (min$^{-1}$)",
             r"$c$ (µm/min)", "Limites"], rows, [1.6, 2.2, 2.2, 2.2, 2.2, 2.0, 3.6])
    n_sup = len(sup)
    n_b2 = sum("b2" in p for p in sup.values())
    n_a2 = sum("a2" in p for p in sup.values())
    n_c = sum("c" in p for p in sup.values())
    w.paragraph(
        r"Em " + str(n_sup) + r" dos 16 ensaios algum parâmetro ficou no limite superior de sua faixa: $b_2$ em "
        + str(n_b2) + r" ensaios, $a_2$ em " + str(n_a2) + r" e $c$ em " + str(n_c) + r" (Tabela B.5). Esses "
        r"parâmetros descrevem a etapa lenta, que ocorre depois de cerca de 5 min, intervalo em que há apenas uma "
        r"medição (15 min); isso sugere que os dados determinam mal essa etapa e que os limites passam a atuar como "
        r"uma regularização adicional. Como a taxa nesse trecho é pequena e pesa pouco na conversão, o efeito sobre "
        r"as curvas reconstruídas é limitado, mas ele define parte dos alvos que a rede aprende (Figura B.4) e é um "
        r"ponto a investigar em uma revisão dos limites e dos pesos de penalização."
    )
    fig(FIG_RES / "fig_res_02_taxas_alvo.png", 16.0, "Figura B.4",
        "Taxas de retração estimadas pelo problema inverso nos 16 ensaios, em escala logarítmica (alvos de "
        "treinamento da rede)")


def secao_d3(w, sub, fig, d) -> None:
    t = d["fe_trein"]
    sub("D.3 Resultados do treinamento do comitê")
    w.paragraph(
        r"Os dez membros do comitê foram treinados com a configuração final, uma semente por membro, nos 780 "
        r"registros dos 13 ensaios de treino. A perda final na escala transformada ficou entre " + v(t["perda_final"].min(), 5)
        + r" e " + v(t["perda_final"].max(), 5) + r" (média de " + v(t["perda_final"].mean(), 5) + r"), o que "
        r"corresponde a uma raiz do erro quadrático médio da ordem de " + v(float(np.sqrt(t["perda_final"].mean())), 3)
        + r" em $y=\ln(1+\nu)$, e cada membro levou cerca de " + v(t["segundos"].mean() / 60, 1) + r" min em uma "
        r"CPU (Tabela D.1). A perda de treino mede apenas o ajuste aos alvos do problema inverso; a capacidade de "
        r"prever ensaios não vistos é avaliada pelos critérios da Seção E.1."
    )
    rows = [[str(int(r["semente"])), v(r["perda_final"], 5), v(r["segundos"], 0)] for _, r in t.iterrows()]
    w.table("Tabela D.1", "Perda final de treino e tempo de treinamento de cada membro do comitê",
            ["Semente", r"Perda final (MSE em $y$)", "Tempo (s)"], rows, [3.0, 6.0, 4.0])


def secao_e5(w, sub, fig, d) -> None:
    r = d["fa_resumo"]
    ant = d["fa_antigo"]
    ens = d["fa_ens"]
    t1 = d["fb_tent"].set_index("number")
    sub("E.5 Linha de base com o protocolo de validação corrigido (Fase A)")
    w.paragraph(
        r"Antes da busca, a configuração de referência da rede ([64, 32], GELU, com normalização de camada, "
        r"parada antecipada) foi avaliada nos dois protocolos descritos na Seção E.1: o antigo, em que a própria "
        r"dobra de validação decide a parada e dá a nota, e o novo, com dois ensaios internos para a parada, nota "
        r"na conversão de zinco e três sementes. No protocolo antigo, o $R^2$ médio da taxa nas quatro dobras foi "
        r"de " + v(ant["R2_nu"].mean(), 3) + r", mas o erro na conversão nos ensaios deixados de fora foi de "
        + v(r["antigo"], 3) + r"; no protocolo novo, foi de " + v(r["novo_RMSE_X_media"], 3) + r" ± "
        + v(r["novo_RMSE_X_dp"], 3) + r", contra " + v(r["v1_treino"], 3) + r" no próprio treino e "
        + v(r["teto"], 3) + r" no teto dado pelos alvos do problema inverso (Tabela E.3 e Figura E.4)."
    )
    w.table("Tabela E.3", "Erro na conversão de zinco (RMSE) da configuração de referência em diferentes "
            "situações, nos 91 pontos experimentais dos 13 ensaios de treino",
            ["Situação", "RMSE (–)"],
            [["Teto: conversão calculada com os próprios alvos de $\\nu$", v(r["teto"], 4)],
             ["Modelo final de referência, avaliado no próprio treino", v(r["v1_treino"], 4)],
             ["Validação cruzada, protocolo antigo (1 semente)", v(r["antigo"], 4)],
             ["Validação cruzada, protocolo novo (3 sementes, média ± desvio)",
              v(r["novo_RMSE_X_media"], 4) + " ± " + v(r["novo_RMSE_X_dp"], 4)]],
            [11.0, 4.0])
    fig(SUB / "fase_a" / "fig_fa_01_protocolo_antigo_vs_novo.png", 16.0, "Figura E.4",
        "Configuração de referência nos dois protocolos: (a) $R^2$ da taxa $\\nu$ por dobra; (b) RMSE da "
        "conversão de zinco em comparação com o teto e com o erro no próprio treino")
    pior = ens["RMSE_X_novo_media"].sort_values(ascending=False).head(3)
    w.paragraph(
        r"O resultado mostra que a nota em $\nu$ escondia um erro grande na conversão, o que justifica adotar o "
        r"RMSE de $X_{\mathrm{Zn}}$ fora da dobra como critério de seleção. Os maiores erros ocorreram nos "
        r"Ensaios " + ", ".join(str(int(e)) for e in pior.index) + r" (RMSE de "
        + ", ".join(v(float(x), 2) for x in pior.values) + r"), com grande variação entre sementes, o que indica "
        r"que a configuração de referência era instável com tão poucos ensaios. O protocolo novo ficou pior que o "
        r"antigo por dois efeitos que não foram separados: ele remove o viés de parar o treino na própria "
        r"validação e treina com oito ensaios, em vez de dez, por reservar dois para a parada. A Seção E.6 mostra "
        r"que treinar com todos os ensaios de cada dobra, por número fixo de épocas, reduz muito esse erro: com a "
        r"mesma configuração e 350 épocas fixas, ele caiu para " + v(float(t1.loc[1, "value"]), 3) + r"."
    )


def _tab_finalistas(w, fin, params, rotulo, titulo, ref_nome):
    rows = []
    for _, r in fin.iterrows():
        nome = r["config"].replace("B2 – tentativa", "Tentativa B2")
        if nome.startswith("v1"):
            nome = "Referência (v1)"
        rows.append([nome, v(r["RMSE_X_media"], 4) + " ± " + v(r["RMSE_X_dp"], 4), v(r["R2_X_media"], 3),
                     mm(params[r["config"]]), "sim" if bool(r["escolhida"]) else ""])
    w.table(rotulo, titulo, ["Configuração", "RMSE (média ± desvio)", r"$R^2$ (–)", "Parâmetros", "Escolhida"],
            rows, [4.2, 4.6, 2.0, 2.6, 2.2])


def secao_e6(w, sub, fig, d, params) -> None:
    t1, t2 = d["fb_tent"], d["fb2_tent"]
    dur1 = pd.to_timedelta(t1["duration"]).dt.total_seconds().sum() / 3600
    dur2 = pd.to_timedelta(t2["duration"]).dt.total_seconds().sum() / 3600
    c1 = t1[t1["state"] == "COMPLETE"]
    c2 = t2[t2["state"] == "COMPLETE"]
    m_par = mediana_por(t1, "params_modo_parada")
    m_act = mediana_por(t1, "params_activation")
    m_cam = mediana_por(t1, "params_n_camadas")
    sub("E.6 Resultados da busca de hiperparâmetros (Fases B e B2)")
    w.paragraph(
        r"No primeiro estágio, foram realizadas " + str(len(t1)) + r" tentativas (" + str(len(c1))
        + r" concluídas e " + str(int((t1["state"] == "PRUNED").sum())) + r" interrompidas pela poda), com " + v(dur1, 1)
        + r" h de tempo de CPU. A estratégia de parada foi o fator mais decisivo: a mediana do erro foi de "
        + v(m_par["epocas_fixas"], 3) + r" com número fixo de épocas e de " + v(m_par["interna"], 3)
        + r" com parada antecipada, pois reservar dois dos 13 ensaios para decidir a parada custa mais do que o "
        r"risco de sobreajuste que ela evita (Figura E.5). A ativação tanh teve mediana de " + v(m_act["Tanh"], 3)
        + r", contra " + v(m_act["GELU"], 3) + r" da GELU e " + v(m_act["SiLU"], 3) + r" da SiLU, e redes de quatro "
        r"camadas, o limite do espaço, tiveram mediana de " + v(m_cam[4], 3) + r", contra " + v(m_cam[1], 3)
        + r" e " + v(m_cam[2], 3) + r" com uma e duas camadas, respectivamente. Como o limite de profundidade foi atingido, o "
        r"segundo estágio ampliou o espaço."
    )
    fig(SUB / "fase_b" / "fig_fb_04_hiperparametros_categoricos.png", 16.0, "Figura E.5",
        "Primeiro estágio da busca: distribuição do erro na conversão (fora da dobra, 3 sementes) segundo a "
        "estratégia de parada, a ativação, a normalização de camada e a profundidade")
    params1 = {r["config"]: params[r["config"]] for _, r in d["fb_fin"].iterrows()}
    w.paragraph(
        r"As cinco melhores tentativas e a configuração de referência foram reavaliadas com dez sementes "
        r"(Tabela E.4 e Figura E.6). A melhor tentativa da busca, com três sementes, tinha erro de "
        + v(float(c1["value"].min()), 4) + r", mas, com dez sementes, as finalistas ficaram entre "
        + v(float(d["fb_fin"][~d["fb_fin"]["config"].str.startswith("v1")]["RMSE_X_media"].min()), 4) + r" e "
        + v(float(d["fb_fin"][~d["fb_fin"]["config"].str.startswith("v1")]["RMSE_X_media"].max()), 4)
        + r", o que ilustra o otimismo da melhor de muitas tentativas. As três primeiras finalistas empataram "
        r"dentro de um erro-padrão e, pela regra de escolha, ficou a de menos parâmetros (tentativa "
        + str(int(d["fb_fin"][d["fb_fin"]["escolhida"]]["config"].iloc[0].split()[-1])) + r")."
    )
    _tab_finalistas(w, d["fb_fin"], params1, "Tabela E.4",
                    "Primeiro estágio: reavaliação das finalistas com dez sementes (erro na conversão fora da dobra)",
                    "v1")
    fig(SUB / "fase_b" / "fig_fb_05_finalistas_10_sementes.png", 16.0, "Figura E.6",
        "Primeiro estágio: erro na conversão das finalistas e da configuração de referência (v1) com dez "
        "sementes; cada ponto é uma semente")
    # segundo estágio
    m_cam2 = mediana_por(t2, "params_n_camadas")
    m_act2 = mediana_por(t2, "params_activation")
    m_lnt = mediana_por(t2, "params_entrada_log_t")
    m_ini = mediana_por(t2, "params_inicializacao")
    m_res = mediana_por(t2, "params_use_residual")
    w.paragraph(
        r"O segundo estágio teve " + str(len(t2)) + r" tentativas (" + str(len(c2)) + r" concluídas), com "
        + v(dur2, 1) + r" h de CPU. Em relação às novas opções, a entrada em $\ln t$ reduziu a mediana do erro de "
        + v(m_lnt[False], 3) + r" para " + v(m_lnt[True], 3) + r", a inicialização de Glorot a elevou de "
        + v(m_ini["padrao"], 3) + r" para " + v(m_ini["xavier"], 3) + r", e as conexões residuais pouco alteraram "
        r"a mediana (" + v(m_res[False], 3) + r" sem e " + v(m_res[True], 3) + r" com), embora estejam presentes "
        r"em todas as finalistas. Redes mais profundas não ajudaram: a mediana foi de " + v(m_cam2[3], 3)
        + r" com três camadas e de " + v(min(m_cam2[k] for k in (5, 6, 7, 8)), 3) + r" a " + v(max(m_cam2[k] for k in (5, 6, 7, 8)), 3)
        + r" com cinco a oito (Figura E.7). "
        r"Entre as ativações, GELU e tanh ficaram próximas (" + v(m_act2["GELU"], 3) + r" e " + v(m_act2["Tanh"], 3)
        + r"), e a SiLU foi pior (" + v(m_act2["SiLU"], 3) + r")."
    )
    fig(SUB / "fase_b2" / "fig_fb2_03_hiperparametros_categoricos.png", 16.0, "Figura E.7",
        "Segundo estágio da busca: distribuição do erro na conversão segundo a profundidade, a ativação, a "
        "entrada temporal, a inicialização, as conexões residuais e a normalização de camada")
    fin2 = d["fb2_fin"]
    sem = d["fb2_sem"].pivot(index="semente", columns="config", values="RMSE_X")
    b = sem[[c for c in sem.columns if c.startswith("Fase B")][0]]
    esc = fin2[fin2["escolhida"]]["config"].iloc[0]
    x = sem[esc]
    dif = x - b
    params2 = {r["config"]: params[r["config"]] for _, r in fin2.iterrows()}
    w.paragraph(
        r"A Tabela E.5 reúne as finalistas do segundo estágio, junto com a escolhida do primeiro e a "
        r"configuração de referência. A escolhida, de " + mm(params2[esc]) + r" parâmetros, reduziu o erro de "
        + v(float(d["fb2_fin"][d["fb2_fin"]["config"].str.startswith("Fase B")]["RMSE_X_media"].iloc[0]), 4) + r" para "
        + v(float(fin2[fin2["escolhida"]]["RMSE_X_media"].iloc[0]), 4) + r" e foi melhor em " + str(int((dif < 0).sum()))
        + r" das 10 sementes (diferença média de " + v(float(dif.mean()), 4) + r"; teste $t$ pareado com $p="
        + v(float(stats.ttest_rel(x, b).pvalue), 3) + r"$ e teste de Wilcoxon com $p=" + v(float(stats.wilcoxon(x, b).pvalue), 3)
        + r"$). A tentativa 478 empatou dentro de um erro-padrão, mas tem mais parâmetros (" + mm(params2[[c for c in params2 if "478" in c][0]])
        + r"), e uma das finalistas teve uma semente que divergiu (erro de "
        + v(float(d["fb2_sem"][d["fb2_sem"]["RMSE_X"] > 0.3]["RMSE_X"].max()), 2) + r"), o que reforça o uso de "
        r"vários membros no modelo final. O ganho sobre o primeiro estágio é moderado e não uniforme entre os "
        r"ensaios (Figura E.9), e a ressalva é que as sementes 42 a 44 também foram usadas durante as buscas."
    )
    _tab_finalistas(w, fin2, params2, "Tabela E.5",
                    "Segundo estágio: reavaliação das finalistas com dez sementes (erro na conversão fora da dobra)",
                    "B")
    fig(SUB / "fase_b2" / "fig_fb2_05_finalistas_10_sementes.png", 16.0, "Figura E.8",
        "Segundo estágio: erro na conversão da escolhida do primeiro estágio e das finalistas, com dez sementes "
        "(uma semente da tentativa 449 divergiu e está fora da escala)")
    fig(SUB / "fase_b2" / "fig_fb2_07_rmse_XZn_por_ensaio.png", 16.0, "Figura E.9",
        "Erro na conversão em cada ensaio de treino (quando fora da dobra) para o teto, a escolhida do primeiro "
        "estágio e a do segundo, com dez sementes")


def secao_e7(w, sub, fig, d) -> None:
    met = d["fe_met"]
    ens = d["fe_ens"]
    nu = d["fe_nu"]
    mem = d["fe_mem"]

    def lin(mod, part):
        r = met[(met["Modelo"] == mod) & (met["Particao"] == part)].iloc[0]
        return r

    v2t, v1t, fpt = lin("MLP v2 (ensemble)", "Teste cego"), lin("MLP v1", "Teste cego"), lin("Fenomenológico puro", "Teste cego")
    sub("E.7 Desempenho do modelo final no teste cego (Fase E)")
    w.paragraph(
        r"O comitê de dez redes foi avaliado uma única vez nos três ensaios de teste cego (21 pontos com $t>0$), "
        r"depois de o modelo estar salvo. O erro na conversão foi de " + v(v2t["RMSE"], 4) + r" ($R^2="
        + v(v2t["R2"], 3) + r"$), contra " + v(v1t["RMSE"], 4) + r" ($R^2=" + v(v1t["R2"], 3)
        + r"$) da configuração de referência e " + v(fpt["RMSE"], 4) + r" ($R^2=" + v(fpt["R2"], 3)
        + r"$) do modelo fenomenológico puro (Tabela E.6 e Figura E.10). Nos ensaios de treino, os erros foram de "
        + v(lin("MLP v2 (ensemble)", "Treino")["RMSE"], 4) + r", " + v(lin("MLP v1", "Treino")["RMSE"], 4) + r" e "
        + v(lin("Fenomenológico puro", "Treino")["RMSE"], 4) + r", respectivamente. O erro do teste cego ficou "
        r"abaixo do da validação cruzada (0,0326), o que é coerente com a composição das dobras: a primeira reúne "
        r"vértices do planejamento, e o teste avalia apenas condições internas."
    )
    rows = []
    for mod, rot in (("Fenomenológico puro", "Fenomenológico puro"), ("MLP v1", "MLP de referência (v1)"),
                     ("MLP v2 (ensemble)", "MLP final (comitê de dez redes)")):
        for part in ("Treino", "Teste cego", "Global"):
            r = lin(mod, part)
            rows.append([rot, part, str(int(r["n_pontos"])), v(r["R2"], 3), v(r["RMSE"], 4), v(r["MAE"], 4), v(r["MaxErro"], 4)])
    w.table("Tabela E.6", "Desempenho na conversão de zinco ($t>0$) do modelo fenomenológico puro, da "
            "configuração de referência e do modelo final",
            ["Modelo", "Conjunto", "Pontos", r"$R^2$ (–)", "RMSE (–)", "MAE (–)", "Erro máx. (–)"],
            rows, [4.2, 2.2, 1.5, 1.8, 2.0, 1.9, 2.2])
    fig(SUB / "fase_e" / "fig_fe_01_XZn_teste_cego.png", 16.0, "Figura E.10",
        "Conversão de zinco nos três ensaios de teste cego: medida, prevista pelo comitê (com a faixa entre os "
        "dez membros), pela configuração de referência e pelo modelo fenomenológico puro")
    e_t = ens[ens["particao"] == "Teste cego"]
    piv = e_t.pivot(index="ensaio", columns="Modelo", values="RMSE")
    rows = [[str(int(e)), v(r["Fenomenológico puro"], 4), v(r["MLP v1"], 4), v(r["MLP v2 (ensemble)"], 4)]
            for e, r in piv.iterrows()]
    w.table("Tabela E.7", "Erro na conversão (RMSE) em cada ensaio de teste cego",
            ["Ensaio", "Fenomenológico puro", "MLP de referência (v1)", "MLP final"], rows, [2.0, 4.4, 4.6, 3.4])
    w.paragraph(
        r"O modelo final foi melhor que a referência nos Ensaios 8 e 14 e pior no Ensaio 7, o de maior excesso "
        r"de ácido ($\eta=3{,}1$), com erros de " + v(float(piv.loc[7, "MLP v2 (ensemble)"]), 3) + r" contra "
        + v(float(piv.loc[7, "MLP v1"]), 3) + r". Um único membro teve erro de " + v(float(mem["RMSE_teste_cego"].mean()), 4)
        + r" ± " + v(float(mem["RMSE_teste_cego"].std(ddof=1)), 4) + r" (de " + v(float(mem["RMSE_teste_cego"].min()), 4)
        + r" a " + v(float(mem["RMSE_teste_cego"].max()), 4) + r"), valor praticamente igual ao do comitê, de modo que o "
        r"ganho do comitê está mais na incerteza que ele informa do que na redução do erro. Na taxa de retração, "
        r"medida contra os alvos do problema inverso no teste cego, o modelo final teve $R^2$ de "
        + v(float(nu.loc["MLP v2 (ensemble)", "R2_nu"]), 3) + r" na escala de $\nu$ e de "
        + v(float(nu.loc["MLP v2 (ensemble)", "R2_log_nu"]), 3) + r" na escala logarítmica, contra "
        + v(float(nu.loc["MLP v1", "R2_nu"]), 3) + r" e " + v(float(nu.loc["MLP v1", "R2_log_nu"]), 3)
        + r" da referência. Ou seja, o modelo final não é melhor em $\nu$, e sim na conversão, que é a "
        r"grandeza de interesse: a diferença em $\nu$ concentra-se depois de cerca de 4 min nos Ensaios 8 e 14, "
        r"onde os alvos ficam no limite superior de $c$ ($0{,}03$ µm/min) e a taxa pesa pouco na conversão."
    )
    w.paragraph(
        r"Duas ressalvas devem acompanhar esses números. Primeiro, o teste cego da configuração de referência já "
        r"havia sido calculado e usado em etapas anteriores do projeto, de modo que ele não é independente para "
        r"ela; para o modelo final, é a primeira e única avaliação. Segundo, com apenas três ensaios e 21 pontos, "
        r"diferenças pequenas de erro não são conclusivas, e a validação cruzada, com 13 ensaios, é a evidência "
        r"principal para a escolha da configuração. A Figura E.11 resume a evolução do erro da configuração de "
        r"referência até o modelo final."
    )
    fig(SUB / "fase_e" / "fig_fe_05_evolucao_e_teste.png", 16.0, "Figura E.11",
        "Evolução do erro na conversão: (a) validação cruzada por ensaio, com dez sementes, da configuração de "
        "referência até a escolhida do segundo estágio; (b) modelos finais no treino e no teste cego")


# --------------------------------------------------------------------------- principal
def main() -> None:
    saida = Path(sys.argv[sys.argv.index("--saida") + 1]) if "--saida" in sys.argv else DESTINO
    if saida.exists() and "--substituir" not in sys.argv:
        sys.exit(f"{saida.name} já existe. Use --substituir para sobrescrever.")
    import json

    d = carregar_tudo()
    # número real de parâmetros de cada configuração (modelo montado, incluindo blocos residuais)
    configs = {}
    for fin in (d["fb_fin"], d["fb2_fin"]):
        for _, r in fin.iterrows():
            configs[r["config"]] = json.loads(r["config_json"])
    params = numeros_parametros(configs)

    doc = docx.Document(str(ORIGEM))
    body = doc.element.body
    els = list(body)

    # 1. remove o parágrafo de abertura que repete a revisão (dentro de Métodos)
    i_ab = achar(els, ABERTURA_REMOVIDA)
    i_res = achar(els, "RESULTADOS E DISCUSS")
    assert i_ab < i_res, "o parágrafo a remover deve estar na Metodologia"
    body.remove(els[i_ab])

    # 2. estilos de referência, copiados de elementos já existentes no apêndice B
    i_cap = achar(els, "Figura B.1 –")
    refs = {"body": els[achar(els, "Este apêndice detalha a obtenção")], "figure": els[i_cap - 1],
            "caption": els[i_cap], "source": els[i_cap + 1], "heading": els[i_cap], "subheading": els[i_cap]}
    ppr_sub = els[achar(els, "B.1 Parametrização")].find(qn("w:pPr"))

    ancora_b = els[achar(els, "APÊNDICE C - ")]
    ancora_d = els[achar(els, "APÊNDICE E - ")]
    ultimo = max(i for i, e in enumerate(els) if e.tag == qn("w:p") and texto(e))
    ancora_e = els[ultimo].getnext()
    assert ancora_e is not None

    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        escritores = []

        def montar(ancora):
            w = SectionWriter(doc, refs, ancora)
            escritores.append(w)

            def sub(txt: str) -> None:
                import copy

                p = parse_xml(f"<w:p {nsdecls('w')}/>")
                p.append(copy.deepcopy(ppr_sub))
                p.append(SectionWriter._run(txt))
                w._place(p)

            def fig(img, largura, label, titulo):
                w.figure(reduzir(Path(img), pasta), largura, label, titulo)

            return w, sub, fig

        w, sub, fig = montar(ancora_b)
        secao_b5(w, sub, fig, d)
        w, sub, fig = montar(ancora_d)
        secao_d3(w, sub, fig, d)
        w, sub, fig = montar(ancora_e)
        secao_e5(w, sub, fig, d)
        secao_e6(w, sub, fig, d, params)
        secao_e7(w, sub, fig, d)

        for w in escritores:  # fora de Métodos: vermelho
            pintar(list(w.inserted))
        saida.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(saida))
    print(f"Documento salvo em: {saida}")


if __name__ == "__main__":
    main()
