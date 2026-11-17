"""Gera a v13 a partir da v12 (sem alterá-la): Resultados da serial com as duas figuras 2x2 e o Apêndice F.

Pedido do usuário em 10/11/2026 sobre a v12:
- a figura 2x2 do texto passa a mostrar o Ensaio 1 (treino) e os três de teste cego (7, 8 e 14);
- em seguida, uma segunda figura 2x2 com os quatro ensaios novos (E1 a E4) e uma comparação rápida;
- um apêndice novo (F) com os resultados completos: curvas dos 16 ensaios, métricas por ensaio e a conversão
  medida e prevista em cada instante, para os 16 ensaios originais e os 4 novos.

Só exposição (a discussão é seção do grupo). Tudo em vermelho (texto novo fora de Métodos). Os números são lidos
dos CSVs de `Código/outputs/` gerados por `gerar_resultados_serial.py`. Ensaios novos: modelo congelado, rótulos E2
e E3 tratados como trocados (hipótese ainda não confirmada pelo laboratório).

Uso: python reescrever_resultados_v13.py
"""

from __future__ import annotations

import copy
import io
import sys
from pathlib import Path

import docx
import pandas as pd
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_utils import SectionWriter, pintar  # noqa: E402
from reescrever_serial_v11 import trocar  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v12.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v13.docx"
RAIZ = DOC_DIR.parent
OUT = RAIZ / "Código" / "outputs"
SERIAL = OUT / "resultados_por_modelagem" / "serial"
NOVOS = SERIAL / "ensaios_novos"
SUB = OUT / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
MED_ROTULADO = RAIZ / "Base de dados" / "Experimentos novos" / "medicoes_XZn_ensaios_novos.csv"
MED_TROCADO = RAIZ / "Base de dados" / "Experimentos novos" / "medicoes_XZn_ensaios_novos_E2_E3_trocados.csv"
CONFIG_FINAL = "B2 – tentativa 511"
TITULO = "MODELAGEM HÍBRIDA SERIAL"
TITULO_AP = "APÊNDICE F - RESULTADOS COMPLETOS DO MODELO HÍBRIDO SERIAL"
SECAO = "5.4"  # ordem do grupo: white-box (Fabrício), white-box novo, cooperativo, serial, PINN
TESTE = (7, 8, 14)
W_P = qn("w:p")
SERIAL_NOME, WB_NOME = "Híbrido serial", "White-box (novo)"


def v(x: float, n: int = 2) -> str:
    """Número com vírgula decimal e sinal de menos tipográfico."""
    return f"{x:.{n}f}".replace(".", ",").replace("-", "−")


def texto(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def estilo(el) -> str:
    ppr = el.find(qn("w:pPr"))
    if ppr is None or ppr.find(qn("w:pStyle")) is None:
        return ""
    return ppr.find(qn("w:pStyle")).get(qn("w:val"))


def carregar() -> dict:
    d = {}
    res = pd.read_csv(SERIAL / "metricas_resumo.csv")
    d["res"] = res[res["modelo"] == SERIAL_NOME].set_index("particao")
    por = pd.read_csv(SERIAL / "metricas_por_ensaio.csv")
    d["por"] = por[por["modelo"] == SERIAL_NOME].set_index("ensaio")
    d["por_wb"] = por[por["modelo"] == WB_NOME].set_index("ensaio")
    d["pts"] = pd.read_csv(SERIAL / "dados_plotados.csv")
    d["teto"] = pd.read_csv(SUB / "fase_a" / "tabela_fase_a_resumo.csv").set_index("referencia")["valor"]["teto"]
    d["vc"] = pd.read_csv(SUB / "fase_b2" / "tabela_fase_b2_finalistas.csv").set_index("config").loc[CONFIG_FINAL]
    dob = pd.read_csv(SUB / "fase_b2" / "finalistas_por_dobra.csv")
    dob = dob[dob["config"] == CONFIG_FINAL]
    assert dob["semente"].nunique() == 10 and sorted(dob["fold"].unique()) == [1, 2, 3, 4]
    d["dobras"] = dob.groupby("fold")["RMSE_X"].mean()
    d["erro"] = pd.read_csv(OUT / "etapa_4_4_resultados_hibrido_serial" / "tabela_erro_por_ensaio.csv").set_index("ensaio")
    d["mem"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_membros_teste_cego.csv")
    d["pred"] = pd.read_csv(OUT / "etapa_4_2_avaliacao_indomain" / "tabela_predicoes_detalhadas_16_ensaios.csv")
    met = pd.read_csv(NOVOS / "metricas_ensaios_novos.csv")
    d["nov"] = met[met["modelo"] == SERIAL_NOME].set_index("ensaio")
    d["nov_wb"] = met[met["modelo"] == WB_NOME].set_index("ensaio")
    d["nov_pts"] = pd.read_csv(NOVOS / "dados_plotados_ensaios_novos.csv")
    d["med_rot"] = pd.read_csv(MED_ROTULADO)
    d["med_troc"] = pd.read_csv(MED_TROCADO)
    return d


# ------------------------------------------------------------------------------------------- Seção 5.4
def secao(w: SectionWriter, heading, d: dict) -> None:
    res, por, pts = d["res"], d["por"], d["pts"]
    tr, te, gl = res.loc["Treino"], res.loc["Teste cego"], res.loc["Global"]
    assert (tr["n_pontos"], te["n_pontos"], gl["n_pontos"]) == (91, 21, 112)
    assert res["incons_fis_pct"].max() == 0.0, "o texto afirma que não há inconsistência física"
    teto_pp = 100 * float(d["teto"])
    assert 0.9 < teto_pp / tr["RMSE_pp"] <= 1.0, "o erro de treino deixou de ficar próximo (e acima) da referência"

    cego = pts[pts["particao"] == "teste cego"].copy()
    cego["erro"] = (cego["XZn_serial"] - cego["XZn_exp"]).abs()
    pior = cego.loc[cego["erro"].idxmax()]
    assert abs(100 * pior["erro"] - te["Emax_pp"]) < 1e-3

    vc, vc_dp = 100 * float(d["vc"]["RMSE_X_media"]), 100 * float(d["vc"]["RMSE_X_dp"])
    dob = 100 * d["dobras"]
    fora = (100 * d["erro"]["RMSE_v2_fora_da_dobra"]).dropna().sort_values(ascending=False)
    assert len(fora) == 13
    top = fora.index[:3].tolist()
    assert set(d["erro"].loc[top, "CA0_mol_L"]) <= {0.1, 1.5}, "os piores ensaios deixaram de estar nos extremos de C_A0"

    pred = d["pred"][d["pred"]["t_min"] > 0]
    assert len(pred) == 112
    faixa = 100 * (pred["XZn_Hibrido_MLP_v2_max"] - pred["XZn_Hibrido_MLP_v2_min"])
    mem = 100 * d["mem"]["RMSE_teste_cego"]
    assert len(mem) == 10

    e8 = pts[(pts["ensaio"] == 8) & (pts["t_min"] == 15.0)].iloc[0]
    assert e8["eta"] == 1.0 and e8["XZn_exp"] < 0.9

    heading(TITULO)
    w.paragraph(
        r"Esta seção apresenta os resultados do modelo híbrido serial (Seção 4.5), cuja versão final é a média de dez "
        r"redes treinadas com os 13 ensaios de treino. Os erros são expressos em pontos percentuais (p.p.) de "
        r"conversão de zinco e calculados nos instantes com medição e $t>0$ (Seção 4.2.4).")
    w.paragraph(
        r"Nos 13 ensaios de treino, o modelo reproduziu a conversão medida com RMSE de " + v(tr["RMSE_pp"]) + r" p.p. e "
        r"$R^2$ de " + v(tr["R2"], 3) + rf" (Tabela {SECAO}.1). Como a rede aprende as taxas estimadas pelo problema "
        r"inverso, a conversão calculada diretamente com essas taxas, cujo RMSE é de " + v(teto_pp) + r" p.p. nos mesmos "
        r"pontos (Seção B.5), serve de referência para o ajuste, e o erro do modelo ficou próximo desse valor. Essas "
        r"métricas medem o ajuste às curvas usadas na construção do modelo, e não a sua capacidade de previsão.")
    w.paragraph(
        r"Nos Ensaios 7, 8 e 14, reservados para o teste cego, o RMSE foi de " + v(te["RMSE_pp"]) + r" p.p., com $R^2$ de "
        + v(te["R2"], 3) + r", erro absoluto médio de " + v(te["MAE_pp"]) + r" p.p. e erro máximo de " + v(te["Emax_pp"])
        + rf" p.p., observado no Ensaio {int(pior['ensaio'])} em " + v(pior["t_min"], 1) + r" min. Por ensaio, o RMSE foi de "
        + v(por.loc[7, "RMSE_pp"]) + r" p.p. no Ensaio 7, " + v(por.loc[8, "RMSE_pp"]) + r" p.p. no Ensaio 8 e "
        + v(por.loc[14, "RMSE_pp"]) + r" p.p. no Ensaio 14. Em nenhum dos 16 ensaios a curva prevista apresentou conversão "
        r"decrescente ou acima do limite estequiométrico, o que decorre da forma como as restrições físicas são impostas "
        r"no acoplamento (Tabela 4.2.2).")

    def linha(nome, s):
        return [nome, str(int(s["n_ensaios"])), str(int(s["n_pontos"])), v(s["R2"], 3), v(s["RMSE_pp"]), v(s["MAE_pp"]),
                v(s["Emax_pp"]), v(s["incons_fis_pct"], 1)]

    w.table(f"Tabela {SECAO}.1",
            r"Desempenho do modelo híbrido serial na previsão da conversão de zinco ($t>0$): coeficiente de determinação, "
            r"RMSE, erro absoluto médio (MAE), erro máximo e inconsistência física (fração dos nós da curva prevista, em "
            r"malha de 0,25 min, com conversão decrescente ou acima do limite estequiométrico)",
            ["Conjunto", "Ensaios", "Pontos", r"$R^2$ (–)", "RMSE (p.p.)", "MAE (p.p.)", "Erro máximo (p.p.)",
             "Inconsistência física (%)"],
            [linha("Treino", tr), linha("Teste cego", te), linha("Global", gl)],
            [2.1, 1.7, 1.5, 1.5, 1.7, 1.7, 2.1, 2.7])

    w.paragraph(
        rf"A Figura {SECAO}.1 compara as curvas previstas com as medições no Ensaio 1, de treino, e nos três ensaios de "
        r"teste cego, ao lado do modelo *white-box* da Seção 4.1; as curvas e os valores dos 16 ensaios estão no "
        r"Apêndice F. Nos ensaios de teste, o modelo acompanha a etapa inicial rápida e o patamar medido, inclusive no "
        r"Ensaio 8 ($\eta=1,0$), em que a conversão medida em 15 min é de " + v(e8["XZn_exp"]) + r" e a prevista, de "
        + v(e8["XZn_serial"]) + r", ambas abaixo do limite estequiométrico.")
    w.figure(SERIAL / "fig_serial_2x2_texto_ensaios_01_07_08_14.png", 16.0, f"Figura {SECAO}.1",
             "Conversão de zinco medida e prevista pelo modelo híbrido serial e pelo modelo *white-box* nos Ensaios 1, 7, "
             "8 e 14; o asterisco indica ensaio de teste cego")
    w.paragraph(
        r"Como o teste cego reúne apenas três ensaios, a capacidade de previsão foi avaliada também pela validação "
        r"cruzada por ensaio (Seções 4.5.2 e 4.5.5), em que cada ensaio de treino é previsto por redes treinadas sem ele. "
        r"Com dez sementes, o RMSE fora da dobra foi de " + v(vc) + r" ± " + v(vc_dp) + r" p.p., cerca de "
        + v(vc / tr["RMSE_pp"], 1) + r" vezes o erro de ajuste. Entre as quatro dobras, o erro variou de " + v(dob.min())
        + rf" p.p. (dobra {int(dob.idxmin())}) a " + v(dob.max()) + rf" p.p. (dobra {int(dob.idxmax())}), e os maiores "
        rf"erros por ensaio ocorreram nos Ensaios {top[0]}, {top[1]} e {top[2]} (" + v(fora.iloc[0], 1) + r"; "
        + v(fora.iloc[1], 1) + r" e " + v(fora.iloc[2], 1) + r" p.p.), todos com $C_{A0}$ de 0,1 ou 1,5 mol/L, extremos da "
        r"faixa ensaiada (Seção E.6).")
    w.paragraph(
        r"As dez redes do comitê forneceram previsões próximas entre si: a diferença entre a maior e a menor conversão "
        r"prevista foi, em média, de " + v(faixa.mean()) + r" p.p. nos 112 pontos (máximo de " + v(faixa.max(), 1)
        + r" p.p.), e cada rede, isoladamente, teve RMSE de " + v(mem.mean()) + r" ± " + v(mem.std(ddof=1))
        + r" p.p. no teste cego. Essa faixa expressa apenas a variabilidade do treinamento e não inclui o erro "
        r"experimental nem as simplificações do modelo fenomenológico.")

    # ---------------------------------------------------------------- ensaios novos
    nov, np_ = d["nov"], d["nov_pts"]
    x15 = np_[np_["t_min"] == 15.0].set_index("ensaio")
    e1, e4 = np_[np_["ensaio"] == "E1"].set_index("t_min"), np_[np_["ensaio"] == "E4"]
    assert nov.loc["Todos", "n"] == 24 and nov.loc["Sem E1", "n"] == 18
    assert (nov.loc[["E1", "E4"], "medido_acima_limite_pct"] == 100).all() and (nov.loc[["E2", "E3"], "medido_acima_limite_pct"] == 0).all()
    assert e1.loc[1.0, "XZn_exp"] > e1.loc[15.0, "XZn_exp"] and e1["XZn_exp"].idxmax() == 1.0, "E1 deixou de ser decrescente após 1 min"
    excesso_e4 = 100 * (e4["XZn_exp"] - e4["limite_estequiometrico"])
    dif15 = {e: 100 * abs(x15.loc[e, "XZn_exp"] - x15.loc[e, "XZn_serial"]) for e in ("E2", "E3")}
    for e in ("E2", "E3"):   # o texto diz que os maiores desvios desses ensaios ocorrem até 3 min
        s_e = np_[np_["ensaio"] == e]
        assert s_e.loc[(s_e["XZn_serial"] - s_e["XZn_exp"]).abs().idxmax(), "t_min"] <= 3.0

    w.paragraph(
        r"O modelo foi confrontado também com quatro ensaios novos (E1 a E4), realizados pelo grupo em condições "
        rf"intermediárias às do planejamento original (Tabela {SECAO}.2), com volume de 200 mL em vez de 400 mL e amostragem "
        r"em 0,5; 1; 2; 3; 5 e 15 min. As previsões foram geradas com o modelo já definido, sem novo ajuste, e registradas "
        r"antes de as medições estarem disponíveis (Seção E.11). O Ensaio E4 ($\eta=0,40$) está abaixo da menor razão "
        r"molar do treino (0,5). Os rótulos dos Ensaios E2 e E3 foram considerados trocados na planilha do laboratório, "
        r"pois as concentrações de zinco registradas em cada um só são compatíveis com a massa de sólido do outro; essa "
        r"hipótese e a conversão das medições em $X_{\mathrm{Zn}}$ estão detalhadas no Apêndice F e aguardam confirmação.")

    def linha_n(e):
        ca0, eta = float(x15.loc[e, "CA0_mol_L"]), float(x15.loc[e, "eta"])
        return [e, v(ca0), v(eta), v(min(1.0, eta)), v(x15.loc[e, "XZn_exp"]), v(x15.loc[e, "XZn_serial"]),
                v(nov.loc[e, "RMSE_pp"]), v(nov.loc[e, "Emax_pp"])]

    w.table(f"Tabela {SECAO}.2",
            r"Ensaios novos: condições, limite estequiométrico, conversão de zinco medida e prevista pelo modelo híbrido "
            r"serial em 15 min e erros da previsão nos seis instantes de amostragem",
            ["Ensaio", r"$C_{A0}$ (mol/L)", r"$\eta$ (–)", r"min(1, $\eta$)", "Medida 15 min", "Prevista 15 min",
             "RMSE (p.p.)", "Erro máximo (p.p.)"],
            [linha_n(e) for e in ("E1", "E2", "E3", "E4")],
            [1.6, 2.0, 1.3, 1.7, 2.2, 2.2, 1.8, 2.3])
    w.paragraph(
        r"Com essa correção, o RMSE foi de " + v(nov.loc["E2", "RMSE_pp"], 1) + r" p.p. em E2, " + v(nov.loc["E3", "RMSE_pp"], 1)
        + r" p.p. em E3 e " + v(nov.loc["E4", "RMSE_pp"], 1) + r" p.p. em E4, e de " + v(nov.loc["E1", "RMSE_pp"], 1)
        + rf" p.p. em E1 (Figura {SECAO}.2). Em E2 e E3, a conversão prevista em 15 min diferiu da medida em "
        + v(dif15["E2"], 1) + r" e " + v(dif15["E3"], 1) + r" p.p., e os maiores desvios ocorreram até 3 min. "
        r"O Ensaio E1 apresenta indício de erro experimental: a conversão medida diminui de " + v(e1.loc[1.0, "XZn_exp"])
        + r" em 1 min para " + v(e1.loc[15.0, "XZn_exp"]) + r" em 15 min e supera, em todos os instantes, o limite "
        r"estequiométrico de 0,75. Em E4, as medições também ficam acima do limite, de 0,40, em " + v(excesso_e4.min(), 1)
        + r" a " + v(excesso_e4.max(), 1) + r" p.p. Nesses dois ensaios, um modelo que respeita o balanço de ácido não pode "
        r"reproduzir os valores medidos. Sem o E1, o RMSE nos " + str(int(nov.loc["Sem E1", "n"])) + r" pontos restantes foi "
        r"de " + v(nov.loc["Sem E1", "RMSE_pp"], 1) + r" p.p.")
    w.figure(NOVOS / "fig_serial_2x2_ensaios_novos.png", 16.0, f"Figura {SECAO}.2",
             "Conversão de zinco medida e prevista pelo modelo híbrido serial e pelo modelo *white-box* nos quatro ensaios "
             "novos, com os rótulos de E2 e E3 trocados em relação à planilha do laboratório")


# ------------------------------------------------------------------------------------------- Apêndice F
def apendice(w: SectionWriter, heading, sub, d: dict) -> None:
    por, por_wb, erro, pts = d["por"], d["por_wb"], d["erro"], d["pts"]
    nov, nov_wb, np_ = d["nov"], d["nov_wb"], d["nov_pts"]

    def nome(e):
        return f"{e}*" if e in TESTE else str(e)

    heading(TITULO_AP)
    w.paragraph(
        r"Este apêndice reúne os resultados completos do modelo híbrido serial resumidos na Seção " + SECAO + r": as "
        r"curvas, as métricas e a conversão de zinco medida e prevista em cada instante, nos 16 ensaios de Bortot Coelho "
        r"(2017) e nos quatro ensaios novos. Os erros estão em pontos percentuais (p.p.) de conversão.")

    sub("F.1 Ensaios do planejamento original")
    w.paragraph(
        r"A Figura F.1 apresenta as curvas previstas nos 16 ensaios, e a Tabela F.1, as métricas de cada um. A coluna de "
        r"validação cruzada traz o erro obtido quando o ensaio fica fora da dobra de treino (Seção E.6) e não se aplica aos "
        r"ensaios de teste cego, que não participam das dobras. A Tabela F.2 lista a conversão medida e a prevista em cada "
        r"instante de amostragem.")
    w.figure(SERIAL / "fig_serial_4x4_todos.png", 16.0, "Figura F.1",
             "Conversão de zinco medida e prevista pelo modelo híbrido serial e pelo modelo *white-box* nos 16 ensaios; o "
             "asterisco indica ensaio de teste cego")
    linhas = []
    for e in range(1, 17):
        cv = erro.loc[e, "RMSE_v2_fora_da_dobra"]
        assert pd.isna(cv) == (e in TESTE)
        linhas.append([nome(e), "Teste cego" if e in TESTE else "Treino", v(erro.loc[e, "CA0_mol_L"], 1), v(erro.loc[e, "eta"], 1),
                       v(por.loc[e, "RMSE_pp"]), v(por.loc[e, "MAE_pp"]), v(por.loc[e, "Emax_pp"]),
                       "–" if pd.isna(cv) else v(100 * cv), v(por_wb.loc[e, "RMSE_pp"])])
    w.table("Tabela F.1",
            r"Métricas do modelo híbrido serial em cada ensaio do planejamento original (sete pontos por ensaio) e RMSE do "
            r"modelo *white-box*; o asterisco indica ensaio de teste cego",
            ["Ensaio", "Conjunto", r"$C_{A0}$ (mol/L)", r"$\eta$ (–)", "RMSE (p.p.)", "MAE (p.p.)", "Erro máximo (p.p.)",
             "RMSE na validação cruzada (p.p.)", "RMSE do *white-box* (p.p.)"],
            linhas, [1.6, 2.1, 1.7, 1.0, 1.6, 1.4, 1.8, 2.0, 1.9])

    tempos = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0]
    linhas = []
    for e in range(1, 17):
        s = pts[pts["ensaio"] == e].set_index("t_min")
        assert list(s.index) == tempos
        linhas.append([nome(e), "Medida"] + [v(s.loc[t, "XZn_exp"]) for t in tempos])
        linhas.append(["", "Prevista"] + [v(s.loc[t, "XZn_serial"], 3) for t in tempos])
    w.table("Tabela F.2",
            r"Conversão de zinco medida (Bortot Coelho, 2017) e prevista pelo modelo híbrido serial em cada instante de "
            r"amostragem dos 16 ensaios; o asterisco indica ensaio de teste cego",
            ["Ensaio", "Conversão", "0,5 min", "1 min", "2 min", "3 min", "4 min", "5 min", "15 min"],
            linhas, [1.6, 2.2, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6])

    # ---------------------------------------------------------------- ensaios novos
    mt, mr = d["med_troc"], d["med_rot"]
    w_zn = (mt["Zn_licor_g_L"] * 0.200 / (mt["m_g"] * mt["XZn"]))
    assert w_zn.std() < 1e-9
    x_e3_rot = float(mr[mr["ensaio"] == "E3"]["XZn_medido"].max())
    assert x_e3_rot > 1.0
    e1 = np_[np_["ensaio"] == "E1"].set_index("t_min")

    sub("F.2 Ensaios novos")
    w.paragraph(
        r"As medições dos quatro ensaios novos (condições na Tabela E.12) foram convertidas em conversão de zinco pela "
        r"mesma relação dos ensaios originais, $X_{\mathrm{Zn}}=C_{\mathrm{Zn}}V/(m\,w)$, em que $C_{\mathrm{Zn}}$ é a "
        r"concentração de zinco no licor, $V=0,200$ L é o volume de solução, $m$ é a massa de sólido e $w$ é o teor de zinco "
        r"do sólido, de " + v(float(w_zn.mean()), 3) + r" g/g, valor que reproduz a conversão final dos 16 ensaios "
        r"originais. Duas hipóteses foram adotadas e aguardam confirmação do laboratório. A primeira é que a coluna de "
        r"concentração da planilha está em g/L, única leitura que fornece a ordem de grandeza esperada. A segunda é que os "
        r"rótulos dos Ensaios E2 e E3 estão trocados entre si: como registrados, a conversão do E3 chegaria a "
        + v(x_e3_rot) + r", acima de 1. Não há medição em 4 min.")
    w.paragraph(
        r"A Tabela F.3 lista a conversão medida e a prevista em cada instante, e a Tabela F.4, as métricas por ensaio. Em "
        r"E1 e E4, todas as medições ficam acima do limite estequiométrico (0,75 e 0,40), o que não é possível com as "
        r"condições nominais, de modo que o desvio nesses ensaios não pode ser atribuído ao modelo antes de o dado ser "
        r"esclarecido. Em E1, além disso, a conversão medida diminui de " + v(e1.loc[1.0, "XZn_exp"]) + r" em 1 min para "
        + v(e1.loc[15.0, "XZn_exp"]) + r" em 15 min. O efeito do volume de 200 mL não pode ser separado dessas questões.")
    tempos_n = [0.5, 1.0, 2.0, 3.0, 5.0, 15.0]
    linhas = []
    for e in ("E1", "E2", "E3", "E4"):
        s = np_[np_["ensaio"] == e].set_index("t_min")
        assert list(s.index) == tempos_n
        linhas.append([e, "Medida"] + [v(s.loc[t, "XZn_exp"], 3) for t in tempos_n])
        linhas.append(["", "Prevista (serial)"] + [v(s.loc[t, "XZn_serial"], 3) for t in tempos_n])
        linhas.append(["", "Prevista (*white-box*)"] + [v(s.loc[t, "XZn_whitebox_novo"], 3) for t in tempos_n])
    w.table("Tabela F.3",
            r"Conversão de zinco medida e prevista pelo modelo híbrido serial e pelo modelo *white-box* em cada instante "
            r"de amostragem dos quatro ensaios novos (rótulos de E2 e E3 trocados em relação à planilha)",
            ["Ensaio", "Conversão", "0,5 min", "1 min", "2 min", "3 min", "5 min", "15 min"],
            linhas, [1.6, 3.9, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6])
    rot = {"Todos": "Todos", "Sem E1": "Sem o E1"}
    linhas = [[rot.get(e, e), str(int(nov.loc[e, "n"])), v(nov.loc[e, "RMSE_pp"]), v(nov.loc[e, "MAE_pp"]), v(nov.loc[e, "Emax_pp"]),
               v(nov.loc[e, "vies_pp"]), v(nov_wb.loc[e, "RMSE_pp"]), v(nov.loc[e, "medido_acima_limite_pct"], 0)]
              for e in ("E1", "E2", "E3", "E4", "Todos", "Sem E1")]
    w.table("Tabela F.4",
            r"Métricas do modelo híbrido serial nos ensaios novos, RMSE do modelo *white-box* e fração das medições acima "
            r"do limite estequiométrico; o desvio médio é a média de (medido − previsto)",
            ["Ensaio", "Pontos", "RMSE (p.p.)", "MAE (p.p.)", "Erro máximo (p.p.)", "Desvio médio (p.p.)",
             "RMSE do *white-box* (p.p.)", "Medições acima do limite (%)"],
            linhas, [1.9, 1.6, 1.7, 1.6, 1.9, 1.9, 2.3, 2.2])


# ------------------------------------------------------------------------------------------- montagem
def aplicar(doc) -> tuple[int, int]:
    body = doc.element.body
    els = list(body.iterchildren())

    def achar(pred, inicio=0):
        return next(i for i, e in enumerate(els) if i >= inicio and e.tag == W_P and pred(e))

    i_met = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == TITULO)
    i_res = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip() == "RESULTADOS E DISCUSSÃO")
    i_conc = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip().startswith("CONCLUS"), i_res)
    i_ape = achar(lambda e: estilo(e) == "Heading1" and texto(e).strip().startswith("APÊNDICE E"), i_conc)
    i_sube = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip().startswith("E.1 "), i_ape)
    assert i_met < i_res < i_conc < i_ape
    assert not any(texto(e).strip().startswith("APÊNDICE F") for e in els if e.tag == W_P), "a origem já tem Apêndice F"

    antigos = [i for i in range(i_res + 1, i_conc) if els[i].tag == W_P and estilo(els[i]) == "Heading3"
               and texto(els[i]).strip() == TITULO]
    assert antigos, "a origem não tem o bloco de Resultados da serial"
    for e in els[antigos[0]:i_conc]:
        body.remove(e)

    i_cap = achar(lambda e: texto(e).strip().startswith("Figura 4.5.1 –"), i_met)
    refs = {"body": els[achar(lambda e: texto(e).startswith("Com essa escolha, a rede neural fica responsável"), i_met)],
            "figure": els[i_cap - 1], "caption": els[i_cap], "source": els[i_cap + 1]}

    def titulo_como(modelo, escritor):
        def f(txt: str) -> None:
            p = parse_xml(f"<w:p {nsdecls('w')}/>")
            p.append(copy.deepcopy(modelo.find(qn("w:pPr"))))
            p.append(SectionWriter._run(txt))
            escritor._place(p)
        return f

    # Seção E.11: a comparação com as medições, antes prometida, agora existe
    trocar(els[achar(lambda e: texto(e).startswith("Como referência de erro, o modelo teve RMSE"), i_ape)],
           "A comparação com as medições será incluída quando os resultados do laboratório estiverem disponíveis.",
           f"A comparação com as medições é apresentada na Seção {SECAO} e no Apêndice F.")

    d = carregar()
    w1 = SectionWriter(doc, refs, els[i_conc])
    secao(w1, titulo_como(els[i_met], w1), d)

    # fim do documento: antes dos parágrafos vazios finais (ou da seção final)
    fim = len(els) - 1
    assert els[fim].tag == qn("w:sectPr")
    while els[fim - 1].tag == W_P and not texto(els[fim - 1]).strip() and not els[fim - 1].findall(".//" + qn("w:drawing")):
        fim -= 1
    w2 = SectionWriter(doc, refs, els[fim])
    apendice(w2, titulo_como(els[i_ape], w2), titulo_como(els[i_sube], w2), d)

    pintar(list(w1.inserted) + list(w2.inserted))
    return len(w1.inserted), len(w2.inserted)


def main() -> None:
    with open(ORIGEM, "rb") as f:   # leitura por cópia: funciona mesmo com a origem aberta no Word
        doc = docx.Document(io.BytesIO(f.read()))
    n1, n2 = aplicar(doc)
    doc.save(str(DESTINO))
    print(f"{DESTINO.name} gravada a partir da {ORIGEM.name}: Seção {SECAO} ({n1} blocos) e Apêndice F ({n2} blocos), em vermelho")


if __name__ == "__main__":
    main()
