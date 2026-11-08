"""Gera a v10 do relatório a partir da v9, sem regerar a v9 (preserva edições manuais feitas nela).

Escreve, em vermelho (fora de Métodos), a subseção de Resultados do modelo híbrido serial, inserida no final
de RESULTADOS E DISCUSSÃO (depois dos marcadores "AA" do grupo e antes de CONCLUSÕES). O modelo é a MLP v2
(comitê de dez redes), mantida como final em 08/11/2026; não se conta com ensaios novos de laboratório.

Estrutura (curta; os detalhes ficam nos Apêndices B a E):
    taxas de retração estimadas pelo problema inverso
    desempenho nos ensaios de treino e de teste cego (Tabela 5.XX.1, Figuras 5.XX.1 e 5.XX.2)
    erro em condições não vistas (Figura 5.XX.3)
    efeito das condições operacionais (Tabela 5.XX.2, Figura 5.XX.4)
    consistência física
    discussão e limitações

Todos os números vêm dos CSVs em Código/outputs/ (nada é digitado à mão). Figuras e tabelas de apoio:
`Código/etapas/etapa_4_4_resultados_hibrido_serial/analisar_resultados.py`.

Uso: python adicionar_resultados_v10.py [--saida CAMINHO.docx] [--substituir]
A v9 não é alterada.
"""

from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

import docx
import numpy as np
import pandas as pd
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).parent))
from adicionar_resultados_apendices_v8 import LIMITES, achar, reduzir, texto, v  # noqa: E402
from docx_utils import SectionWriter, pintar  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
CODIGO = DOC_DIR.parent / "Código"
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v9.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v10.docx"
OUT = CODIGO / "outputs"
RH = OUT / "etapa_4_4_resultados_hibrido_serial"
E42 = OUT / "etapa_4_2_avaliacao_indomain"
SUB = OUT / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
TESTE = [7, 8, 14]
TITULO = "MODELAGEM HÍBRIDA SERIAL"


def pct(x: float, n: int = 0) -> str:
    return v(100 * x, n)


def carregar() -> dict:
    d = {}
    d["inv"] = pd.read_csv(OUT / "etapa_2_1" / "tabela_metricas_otimizacao_inversa.csv").set_index("ensaio")
    d["cmp"] = pd.read_csv(E42 / "tabela_comparativo_quatro_hibridos_XZn.csv")
    d["pred"] = pd.read_csv(E42 / "tabela_predicoes_detalhadas_16_ensaios.csv")
    d["erro"] = pd.read_csv(RH / "tabela_erro_por_ensaio.csv")
    d["tend"] = pd.read_csv(RH / "tabela_tendencias.csv")
    d["cons"] = pd.read_csv(RH / "tabela_consistencia_fisica.csv").iloc[0]
    d["fa"] = pd.read_csv(SUB / "fase_a" / "tabela_fase_a_resumo.csv").set_index("referencia")["valor"]
    d["fb2"] = pd.read_csv(SUB / "fase_b2" / "tabela_fase_b2_finalistas.csv")
    d["mem"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_membros_teste_cego.csv")
    d["nu"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_metricas_nu_teste_cego.csv").set_index("Modelo")
    return d


def linha(cmp: pd.DataFrame, modelo: str, part: str) -> pd.Series:
    return cmp[(cmp["Modelo"].str.startswith(modelo)) & (cmp["Particao"].str.startswith(part))].iloc[0]


# --------------------------------------------------------------------------- conteúdo
def secao(w, heading, sub, fig, d) -> None:
    inv, cmp, pred, erro, tend, cons, fa, fb2, mem = (d[k] for k in ("inv", "cmp", "pred", "erro", "tend", "cons", "fa", "fb2", "mem"))
    FPM, V1, V2 = "FPM Puro", "Híbrido Serial (MLP Campeão)", "Híbrido Serial (MLP v2"
    g = {m: {p: linha(cmp, m, p) for p in ("Treino", "Teste", "Global")} for m in (FPM, V1, V2)}
    rmse_glob_inv = float(np.sqrt((inv["RMSE"] ** 2).mean()))
    n_inv_lim = sum(any(abs(r[k] - hi) <= 1e-3 * max(1.0, hi) for k, (lo, hi) in LIMITES.items()) for _, r in inv.iterrows())
    _t = d["erro"].dropna(subset=["RMSE_v2_fora_da_dobra"])
    assert (_t["RMSE_v2_fora_da_dobra"] > _t["RMSE_v2"]).all(), "o erro fora da dobra deixou de superar o de ajuste; revisar o texto"
    teto = float(fa["teto"])
    cv = fb2[fb2["config"] == "B2 – tentativa 511"].iloc[0]
    cv_ref = fb2[fb2["config"].str.startswith("v1")].iloc[0]
    red_glob = 1 - g[V2]["Global"]["RMSE"] / g[FPM]["Global"]["RMSE"]
    red_teste = 1 - g[V2]["Teste"]["RMSE"] / g[FPM]["Teste"]["RMSE"]
    menor = erro[erro["RMSE_v2"] < erro["RMSE_fenomenologico"]]
    excecoes = erro[erro["RMSE_v2"] >= erro["RMSE_fenomenologico"]]["ensaio"].astype(int).tolist()
    et = erro[erro["teste_cego"]].set_index("ensaio")
    largura = (pred["XZn_Hibrido_MLP_v2_max"] - pred["XZn_Hibrido_MLP_v2_min"])
    assert float(largura.mean()) < 0.6 * float(g[V2]["Global"]["RMSE"]), "a faixa entre membros deixou de ser pequena; revisar o texto"
    assert float(cons["x_acima_do_limite"]) <= 1e-9 and float(cons["x_decrescente"]) <= 1e-9 and float(cons["caf_min"]) >= 0.0 \
        and int(cons["nu_nao_positivo"]) == 0, "a verificação física falhou; revisar o texto"
    cvmax = erro.dropna(subset=["RMSE_v2_fora_da_dobra"]).sort_values("RMSE_v2_fora_da_dobra", ascending=False).head(3)
    cvmax_ca0 = cvmax["CA0_mol_L"].tolist()
    borda = all(c in (0.1, 1.5) for c in cvmax_ca0)
    assert borda, "os três maiores erros fora da dobra deixaram de estar nas bordas de C_A0; revisar o texto"
    cvmax_ens = cvmax["ensaio"].astype(int).tolist()
    cvmax_val = cvmax["RMSE_v2_fora_da_dobra"].tolist()
    p15 = tend.set_index("ensaio")

    heading(TITULO)
    w.paragraph(
        r"Esta seção apresenta o desempenho do modelo híbrido serial com o comitê de dez redes, descrito na Seção 4.XX e nos "
        r"Apêndices B a E. Os resultados seguem a ordem do fluxo de trabalho: as taxas estimadas pelo problema inverso, o "
        r"desempenho nos ensaios de treino e de teste cego, o erro em condições não vistas, a resposta às condições "
        r"operacionais e a consistência física. Os testes feitos depois da seleção da configuração estão nas Seções E.8 a E.10."
    )

    # ------------------------------------------------------------------ problema inverso
    sub("Taxas de retração estimadas pelo problema inverso")
    w.paragraph(
        r"As taxas que a rede aprende foram estimadas ensaio a ensaio e reproduzem as curvas medidas com RMSE de "
        + v(rmse_glob_inv, 4) + r" nos 112 pontos experimentais, entre " + v(inv["RMSE"].min(), 4) + r" e " + v(inv["RMSE"].max(), 4)
        + r" por ensaio (Seção B.5 e Figura B.3). Como a rede aprende justamente essas taxas, a conversão calculada com elas nos "
        r"13 ensaios de treino, cujo RMSE é de " + v(teto, 4) + r" nos 91 pontos, serve de teto de referência para o híbrido (Seção E.5), "
        r"e os resultados seguintes devem ser lidos em relação a ele."
    )

    # ------------------------------------------------------------------ desempenho
    sub("Desempenho nos ensaios de treino e de teste cego")
    w.paragraph(
        r"O modelo híbrido com o comitê de redes reproduziu a conversão de zinco com RMSE de " + v(g[V2]["Global"]["RMSE"], 4)
        + r" nos 112 pontos, contra " + v(g[FPM]["Global"]["RMSE"], 4) + r" do modelo fenomenológico puro, uma redução de "
        + pct(red_glob) + r"% (Tabela 5.XX.1). Nos três ensaios de teste cego, que não participaram de nenhuma etapa do "
        r"desenvolvimento, o erro foi de " + v(g[V2]["Teste"]["RMSE"], 4) + r" ($R^2=" + v(g[V2]["Teste"]["R2"], 3) + r"$), contra "
        + v(g[FPM]["Teste"]["RMSE"], 4) + r" ($R^2=" + v(g[FPM]["Teste"]["R2"], 3) + r"$) do fenomenológico puro e "
        + v(g[V1]["Teste"]["RMSE"], 4) + r" ($R^2=" + v(g[V1]["Teste"]["R2"], 3) + r"$) da configuração de referência da rede. "
        r"O valor de $R^2$ negativo do fenomenológico puro indica que ele erra mais que a média das medições nesses ensaios."
    )
    rows = []
    for rot, m in (("Fenomenológico puro", FPM), ("Híbrido, configuração de referência", V1), ("Híbrido, comitê de dez redes", V2)):
        rows.append([rot] + [x for p in ("Treino", "Teste", "Global") for x in (v(g[m][p]["R2"], 3), v(g[m][p]["RMSE"], 4))])
    w.table("Tabela 5.XX.1", "Coeficiente de determinação e RMSE da conversão de zinco ($t>0$) nos 13 ensaios de treino "
            "(91 pontos), nos 3 de teste cego (21 pontos) e no conjunto global (112 pontos)",
            ["Modelo", r"Treino $R^2$", "Treino RMSE", r"Teste $R^2$", "Teste RMSE", r"Global $R^2$", "Global RMSE"],
            rows, [4.6, 1.8, 2.0, 1.8, 2.0, 1.8, 2.0])
    fig(RH / "fig_rh_01_curvas_16_ensaios.png", 16.0, "Figura 5.XX.1",
        "Conversão de zinco medida e prevista nos 16 ensaios (tempo em escala logarítmica); a faixa azul é a variação entre "
        "os dez membros do comitê e a linha pontilhada é o limite estequiométrico; abaixo de 0,25 min, a curva é a "
        "interpolação linear entre a condição inicial e o primeiro nó da malha de cálculo")
    w.paragraph(
        r"A Figura 5.XX.1 mostra que o modelo reproduz a etapa inicial rápida e o patamar de cada ensaio. O patamar medido "
        r"depende da razão molar: ele termina em cerca de 0,50 quando $\eta=0{,}5$, em 0,85 a 0,87 quando $\eta=1{,}0$, em 0,97 a 0,98 "
        r"quando $\eta=1{,}5$ e em 1,0 quando $\eta=3{,}1$ (Tabela 5.XX.2). O fenomenológico puro prevê patamares próximos de 1 "
        r"nos ensaios com $\eta=1{,}0$ e erra muito neles (RMSE de " + v(float(erro.set_index("ensaio").loc[9, "RMSE_fenomenologico"]), 3)
        + r" e " + v(float(erro.set_index("ensaio").loc[10, "RMSE_fenomenologico"]), 3) + r" nos Ensaios 9 e 10, contra "
        + v(float(erro.set_index("ensaio").loc[9, "RMSE_v2"]), 3) + r" e " + v(float(erro.set_index("ensaio").loc[10, "RMSE_v2"]), 3)
        + r" do híbrido). No conjunto, o híbrido teve erro menor que o fenomenológico em " + str(len(menor)) + r" dos 16 ensaios"
        + (r"; a exceção foi o Ensaio " + str(excecoes[0]) + r" (Figura 5.XX.3)." if len(excecoes) == 1 else r".")
    )
    fig(RH / "fig_rh_02_paridade.png", 16.0, "Figura 5.XX.2",
        "Conversão prevista em função da conversão medida para o fenomenológico puro, a configuração de referência e o "
        "comitê; a faixa cinza indica ±0,05 em torno da reta 1:1")
    w.paragraph(
        r"Nos ensaios de teste cego, o comitê foi melhor que a configuração de referência nos Ensaios 8 e 14 e pior no Ensaio 7 "
        r"(RMSE de " + v(float(et.loc[7, "RMSE_v2"]), 4) + r" contra " + v(float(et.loc[7, "RMSE_v1"]), 4) + r"), o de maior excesso de "
        r"ácido ($\eta=3{,}1$) e $C_{A0}$ de 0,5 mol/L, em que a conversão prevista em 0,5 min (" + v(float(p15.loc[7, "X_prev_0_5"]), 2)
        + r") ficou acima da medida (" + v(float(p15.loc[7, "X_medido_0_5"]), 2) + r"). Um único membro do comitê teve erro de "
        + v(float(mem["RMSE_teste_cego"].mean()), 4) + r" ± " + v(float(mem["RMSE_teste_cego"].std(ddof=1)), 4)
        + r" no teste cego, praticamente igual ao do comitê (" + v(g[V2]["Teste"]["RMSE"], 4) + r"); o comitê serve, portanto, mais para "
        r"informar a variabilidade de treinamento do que para reduzir o erro. Essa variabilidade é pequena: a largura da faixa "
        r"entre os membros foi, em média, de " + v(float(largura.mean()), 4) + r" nos 112 pontos (máximo de " + v(float(largura.max()), 3)
        + r"), o equivalente a " + pct(float(largura.mean()) / float(g[V2]["Global"]["RMSE"])) + r"% do RMSE global do comitê, de modo que a "
        r"escolha das sementes explica só uma parte pequena do erro. Os resultados por ensaio de teste e as métricas complementares estão nas "
        r"Tabelas E.6 e E.7."
    )

    # ------------------------------------------------------------------ erro fora da dobra
    sub("Erro em condições não vistas")
    w.paragraph(
        r"Como o teste cego tem apenas três ensaios, a validação cruzada por ensaio, que cobre os 13 ensaios de treino, é a medida "
        r"principal da capacidade de previsão em condições não vistas. Com dez sementes, o erro fora da dobra do modelo escolhido foi "
        r"de " + v(cv["RMSE_X_media"], 4) + r" ± " + v(cv["RMSE_X_dp"], 4) + r", contra " + v(cv_ref["RMSE_X_media"], 3)
        + r" da configuração de referência (Seção E.6), e é cerca de " + v(float(cv["RMSE_X_media"]) / teto, 1)
        + r" vezes o teto de " + v(teto, 4) + r". O erro fora da dobra superou o erro de ajuste em todos os ensaios (Figura 5.XX.3), e os "
        r"maiores ocorreram nos Ensaios " + ", ".join(str(e) for e in cvmax_ens[:-1]) + r" e " + str(cvmax_ens[-1]) + r" ("
        + ", ".join(v(x, 3) for x in cvmax_val[:-1]) + r" e " + v(cvmax_val[-1], 3) + r"), todos com $C_{A0}$ de 0,1 ou 1,5 mol/L, isto é, "
        r"nas bordas do domínio, o que é compatível com a necessidade de extrapolar quando o ensaio é deixado de fora. Os ensaios de teste cego têm $C_{A0}$ "
        r"de 0,5 e 1,0 mol/L, condições interiores, o que explica em parte por que o erro do teste (" + v(g[V2]["Teste"]["RMSE"], 3)
        + r") ficou abaixo do da validação cruzada (Seção E.7)."
    )
    fig(RH / "fig_rh_03_erro_por_ensaio.png", 16.0, "Figura 5.XX.3",
        "RMSE da conversão em cada ensaio para o fenomenológico puro, a configuração de referência e o comitê (escala "
        "logarítmica); os losangos mostram o erro do comitê quando o ensaio é deixado de fora da dobra")

    # ------------------------------------------------------------------ condições operacionais
    sub("Efeito das condições operacionais")
    rows = []
    for e, r in tend.sort_values(["eta", "CA0_mol_L"]).iterrows():
        rows.append([str(int(r["ensaio"])), v(r["eta"], 1), v(r["CA0_mol_L"], 1), v(r["X_medido_0_5"], 2), v(r["X_prev_0_5"], 2),
                     v(r["X_medido_15"], 2), v(r["X_prev_15"], 2)])
    w.table("Tabela 5.XX.2", "Conversão de zinco medida e prevista pelo comitê em 0,5 e 15 min nos 16 ensaios, ordenados por $\\eta$ "
            "e $C_{A0}$", ["Ensaio", r"$\eta$ (–)", r"$C_{A0}$ (mol/L)", "Medida 0,5 min", "Prevista 0,5 min", "Medida 15 min",
                           "Prevista 15 min"], rows, [1.6, 1.6, 2.4, 2.4, 2.4, 2.4, 2.4])
    x15_05 = tend[tend["eta"] == 0.5]
    x15_10 = tend[tend["eta"] == 1.0]
    c01 = tend[tend["CA0_mol_L"] == 0.1].sort_values("eta")
    w.paragraph(
        r"A razão molar $\eta$ é a variável que mais afeta a conversão. Em 15 min, o modelo prevê " + v(float(x15_05["X_prev_15"].min()), 2)
        + r" a " + v(float(x15_05["X_prev_15"].max()), 2) + r" com $\eta=0{,}5$, isto é, o patamar coincide com o limite estequiométrico, "
        r"imposto pelo acoplamento e confirmado pelas medições; com $\eta=1{,}0$, prevê " + v(float(x15_10["X_prev_15"].min()), 2) + r" a "
        + v(float(x15_10["X_prev_15"].max()), 2) + r" (medido, " + v(float(x15_10["X_medido_15"].min()), 2) + r" a "
        + v(float(x15_10["X_medido_15"].max()), 2) + r"), abaixo do limite de 1, e só com $\eta\geq1{,}5$ a conversão se aproxima da "
        r"completa (Figura 5.XX.4). O patamar abaixo de 1 para $\eta=1{,}0$ não decorre do balanço de ácido, e sim das taxas aprendidas, "
        r"que se tornam muito pequenas antes da conversão completa; o modelo reproduz esse comportamento medido, que o fenomenológico puro não "
        r"captura, mas não identifica sua causa."
    )
    fig(RH / "fig_rh_04_mapa_conversao.png", 16.0, "Figura 5.XX.4",
        "Conversão de zinco prevista pelo comitê em 0,5 min e em 15 min no plano ($C_{A0}$, $\\eta$), com as medições dos 16 "
        "ensaios sobre o mesmo mapa de cores; as linhas tracejadas marcam conversões de 0,50, 0,75, 0,90 e 0,95")
    w.paragraph(
        r"Em 0,5 min, a conversão depende também de $C_{A0}$: aumenta de 0,1 para 0,5 a 1,0 mol/L e depois se estabiliza, como mostram "
        r"os valores medidos com $\eta=3{,}1$ ($" + v(float(p15.loc[2, "X_medido_0_5"]), 2) + r"$ em 0,1 mol/L e $" + v(float(p15.loc[12, "X_medido_0_5"]), 2)
        + r"$ em 1,0 mol/L) e com $\eta=1{,}0$ ($" + v(float(p15.loc[6, "X_medido_0_5"]), 2) + r"$ e $" + v(float(p15.loc[9, "X_medido_0_5"]), 2)
        + r"$). Com $\eta=3{,}1$ e $C_{A0}\geq1{,}0$ mol/L, a conversão medida já é de " + v(float(p15.loc[[12, 16], "X_medido_0_5"].min()), 2)
        + r" a " + v(float(p15.loc[[12, 16], "X_medido_0_5"].max()), 2) + r" em 0,5 min, e os instantes seguintes pouco informam sobre "
        r"a cinética. O comitê subestima a conversão em 0,5 min nos ensaios com $\eta=1{,}0$ e $C_{A0}\geq0{,}5$ mol/L "
        r"(diferença de " + v(float((p15.loc[[8, 9, 10], "X_medido_0_5"] - p15.loc[[8, 9, 10], "X_prev_0_5"]).min()), 2) + r" a "
        + v(float((p15.loc[[8, 9, 10], "X_medido_0_5"] - p15.loc[[8, 9, 10], "X_prev_0_5"]).max()), 2) + r")."
    )

    # ------------------------------------------------------------------ consistência física
    sub("Consistência física")
    w.paragraph(
        r"A consistência física foi verificada em " + f"{int(cons['n_condicoes']):,}".replace(",", ".") + r" condições distribuídas em "
        r"uma malha regular de $C_{A0}$ (0,1 a 1,5 mol/L) e $\eta$ (0,5 a 3,1), com o tempo de 0 a 15 min em passos de 0,25 min. Em "
        r"nenhuma delas a conversão superou o limite min(1, $\eta$) ou diminuiu com o tempo, nem a concentração de ácido ficou "
        r"negativa. A taxa prevista pela rede foi sempre positiva, com mínimo de " + v(float(cons["nu_min"]) * 1e5, 1) + r"$\times10^{-5}$ µm/min. Essas "
        r"propriedades decorrem da estrutura do modelo (saída softplus, conversão acumulada e limitada, Seção 4.XX) e valem, portanto, "
        r"também fora das condições ensaiadas; elas não garantem, porém, que as previsões nessas condições estejam corretas."
    )

    # ------------------------------------------------------------------ discussão
    sub("Discussão e limitações")
    w.paragraph(
        r"O ganho do modelo híbrido sobre o fenomenológico puro vem de substituir a lei cinética pela taxa aprendida, mantendo os "
        r"balanços populacional e de ácido: o erro caiu " + pct(red_glob) + r"% no conjunto global e " + pct(red_teste) + r"% no teste cego, "
        r"e as restrições físicas continuam valendo. O erro de " + v(cv["RMSE_X_media"], 3) + r" fora da dobra permanece, porém, "
        r"maior que o teto de " + v(teto, 3) + r", e os testes de perdas com informação física e de ajuste fino ponta a ponta (Seções E.8 "
        r"a E.10) não reduziram essa diferença, de modo que a configuração adotada parece estar perto do que os 13 ensaios permitem "
        r"distinguir. Se o limite está na quantidade de ensaios ou na qualidade dos alvos não foi esclarecido: em " + str(n_inv_lim)
        + r" dos 16 ensaios algum parâmetro do problema inverso ficou no limite da sua faixa (Seção B.5), e os pesos das penalizações "
        r"foram definidos empiricamente, sem otimização (Seção B.3), o que pode afetar os alvos."
    )
    w.paragraph(
        r"Há limitações que restringem o alcance dos resultados. Os 16 ensaios cobrem quatro níveis de $C_{A0}$ e de $\eta$ a 40 °C e "
        r"1000 rpm, com uma única amostra de calcina e volume de 400 mL, e o modelo não tem temperatura, agitação, granulometria ou volume "
        r"como entrada; fora do domínio de $C_{A0}$ de 0,1 a 1,5 mol/L e de $\eta$ de 0,5 a 3,1, as previsões não foram avaliadas. O teste "
        r"cego reúne três ensaios interiores (21 pontos), e diferenças pequenas entre modelos nele não são conclusivas; o teste da "
        r"configuração de referência, além disso, já havia sido usado em etapas anteriores. Por fim, a faixa entre os membros do comitê "
        r"mede só a variabilidade de treinamento e não é intervalo de confiança da conversão, pois não inclui o erro experimental nem "
        r"as simplificações do modelo fenomenológico."
    )


# --------------------------------------------------------------------------- principal
def main() -> None:
    saida = Path(sys.argv[sys.argv.index("--saida") + 1]) if "--saida" in sys.argv else DESTINO
    if saida.exists() and "--substituir" not in sys.argv:
        sys.exit(f"{saida.name} já existe. Use --substituir para sobrescrever.")
    d = carregar()
    doc = docx.Document(str(ORIGEM))
    body = doc.element.body
    els = list(body)
    assert not any(texto(e).startswith("Taxas de retração estimadas pelo problema inverso") for e in els if e.tag == qn("w:p")), \
        "a v9 já tem a subseção de Resultados"

    i_cap = achar(els, "Figura B.1 –")
    i_res = achar(els, "RESULTADOS E DISCUSS")
    i_conc = achar(els, "CONCLUS", i_res)
    i_head = next(i for i, e in enumerate(els) if e.tag == qn("w:p") and texto(e) == TITULO and i < i_res)
    i_sub = achar(els, "Obtenção da taxa de retração por problema inverso")
    refs = {"body": els[achar(els, "Este apêndice detalha a obtenção")], "figure": els[i_cap - 1], "caption": els[i_cap],
            "source": els[i_cap + 1], "heading": els[i_head], "subheading": els[i_sub]}
    ancora = els[i_conc]
    assert texto(ancora).startswith("CONCLUS")

    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        w = SectionWriter(doc, refs, ancora)

        def heading(txt: str) -> None:
            p = parse_xml(f"<w:p {nsdecls('w')}/>")
            p.append(copy.deepcopy(els[i_head].find(qn("w:pPr"))))
            p.append(SectionWriter._run(txt))
            w._place(p)

        def sub(txt: str) -> None:
            p = parse_xml(f"<w:p {nsdecls('w')}/>")
            p.append(copy.deepcopy(els[i_sub].find(qn("w:pPr"))))
            p.append(SectionWriter._run(txt))
            w._place(p)

        def fig(img, largura, label, titulo):
            w.figure(reduzir(Path(img), pasta), largura, label, titulo)

        secao(w, heading, sub, fig, d)
        pintar(list(w.inserted))
        saida.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(saida))
    print(f"Documento salvo em: {saida}")


if __name__ == "__main__":
    main()
