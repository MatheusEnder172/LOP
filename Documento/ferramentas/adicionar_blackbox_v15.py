"""Gera a v15 a partir da v14 (sem alterá-la): Resultados do modelo black-box (MLP pura) e seu apêndice.

Pedido do usuário em 10/11/2026: repetir, para a linha de base puramente orientada a dados (comitê de 10 redes MLP
da Subetapa 3.2.7, que prevê X_Zn direto), o mesmo molde usado para o híbrido serial: ajuste nos 13 ensaios, teste
cego com as métricas comuns, figura 2x2 (Ensaios 1, 7*, 8* e 14*), validação cruzada, dispersão do comitê, os quatro
ensaios novos (segunda figura 2x2) e, no Apêndice E, os resultados completos (4x4 e valores tabelados).

A seção entra depois da do híbrido serial, com numeração provisória "5.X" (destacada em amarelo): a ordem final é
do grupo. As letras dos apêndices já são as novas (A a E). Tudo em vermelho. Números lidos dos CSVs gerados por
`Código/etapas/etapa_4_2_avaliacao_indomain/gerar_resultados_mlp_pura.py` e da validação cruzada com dez sementes
(`etapa_4_5_auditoria_serial/item_3_mlp_pura_10_sementes`).

Uso: python adicionar_blackbox_v15.py
"""

from __future__ import annotations

import copy
import io
import json
import sys
from pathlib import Path

import docx
import numpy as np
import pandas as pd
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_utils import SectionWriter, pintar  # noqa: E402
from reescrever_resultados_v13 import estilo, texto, v  # noqa: E402
from reescrever_serial_v11 import trocar  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v14.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v15.docx"
OUT = DOC_DIR.parent / "Código" / "outputs"
BB = OUT / "resultados_por_modelagem" / "mlp_pura"
NOVOS = BB / "ensaios_novos"
CV10 = OUT / "etapa_4_5_auditoria_serial" / "item_3_mlp_pura_10_sementes"
CONFIG = OUT / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn" / "config_escolhida.json"
TITULO_SERIAL = "MODELAGEM HÍBRIDA SERIAL"
TITULO = "MODELO PURAMENTE ORIENTADO A DADOS (BLACK-BOX)"
SECAO, SECAO_SERIAL = "5.X", "5.4"
TESTE = (7, 8, 14)
W_P = qn("w:p")
NOME, WB = "MLP pura", "White-box (novo)"
T_FISICA = np.arange(0.0, 15.0 + 1e-9, 0.25)


def violacoes(curvas: pd.DataFrame, limites: dict) -> pd.DataFrame:
    """Por ensaio, na malha de 0,25 min: maior excesso sobre o limite estequiométrico e maior queda entre nós (p.p.)."""
    linhas = []
    for e, s in curvas.groupby("ensaio"):
        t = T_FISICA[T_FISICA >= s["t_min"].min() - 1e-9]
        x = np.interp(t, s["t_min"], s["XZn"])
        linhas.append({"ensaio": e, "excesso_pp": 100 * max(0.0, float((x - limites[e]).max())),
                       "queda_pp": 100 * max(0.0, float(-np.diff(x).min())), "x_min": float(x.min()), "x_max": float(x.max()),
                       "todos_acima": bool((x > limites[e]).all())})
    return pd.DataFrame(linhas).set_index("ensaio")


def carregar() -> dict:
    d = {}
    res = pd.read_csv(BB / "metricas_resumo.csv")
    d["res"] = res[res["modelo"] == NOME].set_index("particao")
    por = pd.read_csv(BB / "metricas_por_ensaio.csv")
    d["por"] = por[por["modelo"] == NOME].set_index("ensaio")
    d["pts"] = pd.read_csv(BB / "dados_plotados.csv")
    lim = d["pts"].groupby("ensaio")["limite_estequiometrico"].first().to_dict()
    d["viol"] = violacoes(pd.read_csv(BB / "curvas_mlp_pura.csv"), lim)
    d["mem"] = pd.read_csv(BB / "membros_teste_cego.csv")
    d["faixa"] = pd.read_csv(BB / "faixa_entre_membros_112_pontos.csv")["faixa_entre_membros"]
    d["cv"] = pd.read_csv(CV10 / "cv_mlp_pura_10_sementes.csv")["RMSE_mlp_pura"]
    d["cv_e"] = pd.read_csv(CV10 / "tabela_v2_vs_mlp_pura_por_ensaio.csv").set_index("ensaio")
    d["cfg"] = json.loads(CONFIG.read_text(encoding="utf-8"))["config"]
    met = pd.read_csv(NOVOS / "metricas_ensaios_novos.csv")
    d["nov"] = met[met["modelo"] == NOME].set_index("ensaio")
    d["nov_pts"] = pd.read_csv(NOVOS / "dados_plotados_ensaios_novos.csv")
    lim_n = d["nov_pts"].groupby("ensaio")["limite_estequiometrico"].first().to_dict()
    d["nov_viol"] = violacoes(pd.read_csv(NOVOS / "curvas_mlp_pura_ensaios_novos.csv"), lim_n)
    return d


# ------------------------------------------------------------------------------------------- Seção 5.X
def secao(w: SectionWriter, heading, d: dict) -> None:
    res, por, pts, viol, cfg = d["res"], d["por"], d["pts"], d["viol"], d["cfg"]
    tr, te, gl = res.loc["Treino"], res.loc["Teste cego"], res.loc["Global"]
    assert (tr["n_pontos"], te["n_pontos"], gl["n_pontos"]) == (91, 21, 112)
    assert cfg["hidden_dims"] == [90, 45, 22] and cfg["epocas_finais"] == 900 and len(d["mem"]) == 10 and len(d["cv"]) == 10
    assert gl["incons_fis_pct"] > 0, "o texto afirma que há inconsistência física"

    cego = pts[pts["particao"] == "teste cego"].copy()
    cego["erro"] = (cego["XZn_mlp_pura"] - cego["XZn_exp"]).abs()
    pior = cego.loc[cego["erro"].idxmax()]
    assert abs(100 * pior["erro"] - te["Emax_pp"]) < 1e-3
    e_exc, e_que = viol["excesso_pp"].idxmax(), viol["queda_pp"].idxmax()

    cv, cv_dp = 100 * d["cv"].mean(), 100 * d["cv"].std(ddof=1)
    fora = (100 * d["cv_e"]["RMSE_mlp_pura"]).sort_values(ascending=False)
    assert len(fora) == 13 and not set(fora.index) & set(TESTE)
    top = fora.index[:3].tolist()
    assert set(d["cv_e"].loc[top, "CA0_mol_L"]) <= {0.1, 1.5}, "os piores ensaios deixaram de estar nos extremos de C_A0"
    faixa, mem = 100 * d["faixa"], 100 * d["mem"]["RMSE_teste_cego"]
    assert len(faixa) == 112

    heading(TITULO)
    w.paragraph(
        r"Esta seção apresenta os resultados do modelo puramente orientado a dados (*black-box*), descrito nas Seções 4.1.4 "
        r"a 4.1.7 e adotado como linha de base das abordagens híbridas (Seção 4.2.4). O modelo avaliado é a média de dez redes MLP, com três camadas "
        r"ocultas de 90, 45 e 22 neurônios e ativação GELU, que estimam a conversão de zinco diretamente a partir de "
        r"$C_{A0}$, $\eta$ e $\ln t$, sem o balanço populacional e sem restrições físicas na saída. As redes foram "
        rf"treinadas por {cfg['epocas_finais']} épocas com os 91 pontos medidos ($t>0$) dos 13 ensaios de treino, e os erros "
        r"são expressos em pontos percentuais (p.p.) de conversão.")
    w.paragraph(
        r"Nos 13 ensaios de treino, o RMSE foi de " + v(tr["RMSE_pp"]) + r" p.p. e o $R^2$, de " + v(tr["R2"], 3)
        + rf" (Tabela {SECAO}.1). Essas métricas medem o ajuste aos pontos usados no treinamento, e não a capacidade de "
        r"previsão.")
    w.paragraph(
        r"Nos Ensaios 7, 8 e 14, reservados para o teste cego, o RMSE foi de " + v(te["RMSE_pp"]) + r" p.p., com $R^2$ de "
        + v(te["R2"], 3) + r", erro absoluto médio de " + v(te["MAE_pp"]) + r" p.p. e erro máximo de " + v(te["Emax_pp"])
        + rf" p.p., observado no Ensaio {int(pior['ensaio'])} em " + v(pior["t_min"], 1) + r" min. Por ensaio, o RMSE foi de "
        + v(por.loc[7, "RMSE_pp"]) + r" p.p. no Ensaio 7, " + v(por.loc[8, "RMSE_pp"]) + r" p.p. no Ensaio 8 e "
        + v(por.loc[14, "RMSE_pp"]) + r" p.p. no Ensaio 14. Como a rede não incorpora as restrições físicas da Seção 4.2.3, "
        + v(gl["incons_fis_pct"], 1) + r"% dos nós das curvas previstas nos 16 ensaios apresentaram conversão decrescente ou "
        r"acima do limite estequiométrico. A maior ultrapassagem do limite foi de " + v(viol.loc[e_exc, "excesso_pp"], 1)
        + rf" p.p. (Ensaio {e_exc}), e a maior queda entre nós consecutivos, de " + v(viol.loc[e_que, "queda_pp"], 1)
        + rf" p.p. (Ensaio {e_que}).")

    def linha(nome, s):
        return [nome, str(int(s["n_ensaios"])), str(int(s["n_pontos"])), v(s["R2"], 3), v(s["RMSE_pp"]), v(s["MAE_pp"]),
                v(s["Emax_pp"]), v(s["incons_fis_pct"], 1)]

    w.table(f"Tabela {SECAO}.1",
            r"Desempenho do modelo *black-box* na previsão da conversão de zinco ($t>0$): coeficiente de determinação, RMSE, "
            r"erro absoluto médio (MAE), erro máximo e inconsistência física (fração dos nós da curva prevista, em malha de "
            r"0,25 min a partir de 0,5 min, com conversão decrescente ou acima do limite estequiométrico)",
            ["Conjunto", "Ensaios", "Pontos", r"$R^2$ (–)", "RMSE (p.p.)", "MAE (p.p.)", "Erro máximo (p.p.)",
             "Inconsistência física (%)"],
            [linha("Treino", tr), linha("Teste cego", te), linha("Global", gl)],
            [2.1, 1.7, 1.5, 1.5, 1.7, 1.7, 2.1, 2.7])
    w.paragraph(
        rf"A Figura {SECAO}.1 compara as curvas previstas com as medições no Ensaio 1, de treino, e nos três ensaios de "
        r"teste cego, ao lado do modelo *white-box* da Seção 4.1. As curvas começam em 0,5 min, primeiro instante com "
        r"medição, pois a rede não recebe a condição inicial. As curvas e os valores dos 16 ensaios estão no Apêndice E.")
    w.figure(BB / "fig_mlp_pura_2x2_texto_ensaios_01_07_08_14.png", 16.0, f"Figura {SECAO}.1",
             "Conversão de zinco medida e prevista pelo modelo *black-box* (MLP pura) e pelo modelo *white-box* nos "
             "Ensaios 1, 7, 8 e 14; o asterisco indica ensaio de teste cego")
    w.paragraph(
        r"Na validação cruzada por ensaio, com as mesmas quatro dobras do modelo serial (Seção 4.5.2) e dez sementes, o "
        r"RMSE fora da dobra foi de " + v(cv) + r" ± " + v(cv_dp) + r" p.p., cerca de " + v(cv / tr["RMSE_pp"], 1)
        + rf" vezes o erro de ajuste. Os maiores erros por ensaio ocorreram nos Ensaios {top[0]}, {top[1]} e {top[2]} ("
        + v(fora.iloc[0], 1) + r"; " + v(fora.iloc[1], 1) + r" e " + v(fora.iloc[2], 1) + r" p.p.), todos com $C_{A0}$ de "
        r"0,1 ou 1,5 mol/L, extremos da faixa ensaiada.")
    w.paragraph(
        r"Entre as dez redes, a diferença entre a maior e a menor conversão prevista foi, em média, de " + v(faixa.mean())
        + r" p.p. nos 112 pontos (máximo de " + v(faixa.max(), 1) + r" p.p.), e cada rede, isoladamente, teve RMSE de "
        + v(mem.mean()) + r" ± " + v(mem.std(ddof=1)) + r" p.p. no teste cego, entre " + v(mem.min()) + r" e " + v(mem.max())
        + r" p.p.")

    # ---------------------------------------------------------------- ensaios novos
    nov, np_, nv = d["nov"], d["nov_pts"], d["nov_viol"]
    x15 = np_[np_["t_min"] == 15.0].set_index("ensaio")
    e4 = np_[np_["ensaio"] == "E4"]
    assert nov.loc["Sem E1", "n"] == 18 and nv.loc["E4", "todos_acima"] and nov.loc["E4", "incons_fis_pct"] == 100
    assert (e4["XZn_mlp_pura"] > e4["limite_estequiometrico"]).all()
    outros = nov.loc[["E1", "E2", "E3"], "incons_fis_pct"]
    assert (nv.loc[["E1", "E2", "E3"], "excesso_pp"] == 0).all() and (outros > 0).all()

    w.paragraph(
        rf"Nos quatro ensaios novos, descritos na Seção {SECAO_SERIAL}, as previsões foram calculadas com as mesmas dez "
        rf"redes, sem novo ajuste, e com os rótulos de E2 e E3 trocados (Tabela {SECAO}.2 e Figura {SECAO}.2). O RMSE foi de "
        + v(nov.loc["E2", "RMSE_pp"], 1) + r" p.p. em E2, " + v(nov.loc["E3", "RMSE_pp"], 1) + r" p.p. em E3, "
        + v(nov.loc["E4", "RMSE_pp"], 1) + r" p.p. em E4 e " + v(nov.loc["E1", "RMSE_pp"], 1) + r" p.p. em E1, ensaio com "
        r"indício de erro experimental; sem o E1, o RMSE nos " + str(int(nov.loc["Sem E1", "n"])) + r" pontos restantes foi "
        r"de " + v(nov.loc["Sem E1", "RMSE_pp"], 1) + r" p.p. Em E4, cuja razão molar (0,40) está abaixo da faixa de treino, "
        r"a conversão prevista nos instantes de amostragem ficou entre " + v(e4["XZn_mlp_pura"].min()) + r" e "
        + v(e4["XZn_mlp_pura"].max()) + r", acima do limite estequiométrico de 0,40 em toda a curva, em até "
        + v(nv.loc["E4", "excesso_pp"], 1) + r" p.p. Nos demais ensaios novos, de " + v(outros.min(), 0) + r"% a "
        + v(outros.max(), 0) + r"% dos nós das curvas apresentaram conversão decrescente.")

    def linha_n(e):
        ca0, eta = float(x15.loc[e, "CA0_mol_L"]), float(x15.loc[e, "eta"])
        return [e, v(ca0), v(eta), v(min(1.0, eta)), v(x15.loc[e, "XZn_exp"]), v(x15.loc[e, "XZn_mlp_pura"]),
                v(nov.loc[e, "RMSE_pp"]), v(nov.loc[e, "Emax_pp"])]

    w.table(f"Tabela {SECAO}.2",
            r"Ensaios novos: condições, limite estequiométrico, conversão de zinco medida e prevista pelo modelo *black-box* "
            r"em 15 min e erros da previsão nos seis instantes de amostragem",
            ["Ensaio", r"$C_{A0}$ (mol/L)", r"$\eta$ (–)", r"min(1, $\eta$)", "Medida 15 min", "Prevista 15 min",
             "RMSE (p.p.)", "Erro máximo (p.p.)"],
            [linha_n(e) for e in ("E1", "E2", "E3", "E4")],
            [1.6, 2.0, 1.3, 1.7, 2.2, 2.2, 1.8, 2.3])
    w.figure(NOVOS / "fig_mlp_pura_2x2_ensaios_novos.png", 16.0, f"Figura {SECAO}.2",
             "Conversão de zinco medida e prevista pelo modelo *black-box* (MLP pura) e pelo modelo *white-box* nos quatro "
             "ensaios novos, com os rótulos de E2 e E3 trocados em relação à planilha do laboratório")


# ------------------------------------------------------------------------------------------- Apêndice E (E.3 e E.4)
def apendice(w: SectionWriter, sub, d: dict) -> None:
    por, pts, cv_e = d["por"], d["pts"], d["cv_e"]
    nov, np_, nv = d["nov"], d["nov_pts"], d["nov_viol"]

    def nome(e):
        return f"{e}*" if e in TESTE else str(e)

    sub("E.3 Modelo black-box: ensaios do planejamento original")
    w.paragraph(
        r"A Figura E.2 apresenta as curvas previstas pelo modelo *black-box* nos 16 ensaios, a partir de 0,5 min, e a "
        r"Tabela E.5, as métricas de cada um, com o erro da validação cruzada (dez sementes) nos ensaios de treino e a "
        r"fração dos nós da curva fisicamente inconsistentes. A Tabela E.6 lista a conversão medida e a prevista em cada "
        r"instante de amostragem.")
    w.figure(BB / "fig_mlp_pura_4x4_todos.png", 16.0, "Figura E.2",
             "Conversão de zinco medida e prevista pelo modelo *black-box* (MLP pura) e pelo modelo *white-box* nos 16 "
             "ensaios; o asterisco indica ensaio de teste cego")
    cond = pts.groupby("ensaio")[["CA0_mol_L", "eta"]].first()
    linhas = []
    for e in range(1, 17):
        assert (e in cv_e.index) != (e in TESTE)
        linhas.append([nome(e), "Teste cego" if e in TESTE else "Treino", v(cond.loc[e, "CA0_mol_L"], 1), v(cond.loc[e, "eta"], 1),
                       v(por.loc[e, "RMSE_pp"]), v(por.loc[e, "MAE_pp"]), v(por.loc[e, "Emax_pp"]),
                       "–" if e in TESTE else v(100 * cv_e.loc[e, "RMSE_mlp_pura"]), v(por.loc[e, "incons_fis_pct"], 1)])
    w.table("Tabela E.5",
            r"Métricas do modelo *black-box* em cada ensaio do planejamento original (sete pontos por ensaio); o asterisco "
            r"indica ensaio de teste cego",
            ["Ensaio", "Conjunto", r"$C_{A0}$ (mol/L)", r"$\eta$ (–)", "RMSE (p.p.)", "MAE (p.p.)", "Erro máximo (p.p.)",
             "RMSE na validação cruzada (p.p.)", "Inconsistência física (%)"],
            linhas, [1.5, 1.95, 1.65, 0.9, 1.5, 1.3, 1.7, 1.95, 2.7])
    tempos = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0]
    linhas = []
    for e in range(1, 17):
        s = pts[pts["ensaio"] == e].set_index("t_min")
        assert list(s.index) == tempos
        linhas.append([nome(e), "Medida"] + [v(s.loc[t, "XZn_exp"]) for t in tempos])
        linhas.append(["", "Prevista"] + [v(s.loc[t, "XZn_mlp_pura"], 3) for t in tempos])
    w.table("Tabela E.6",
            r"Conversão de zinco medida (Bortot Coelho, 2017) e prevista pelo modelo *black-box* em cada instante de "
            r"amostragem dos 16 ensaios; o asterisco indica ensaio de teste cego",
            ["Ensaio", "Conversão", "0,5 min", "1 min", "2 min", "3 min", "4 min", "5 min", "15 min"],
            linhas, [1.6, 2.2, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6])

    sub("E.4 Modelo black-box: ensaios novos")
    w.paragraph(
        r"A Tabela E.7 lista a conversão prevista pelo modelo *black-box* em cada instante dos quatro ensaios novos, ao "
        r"lado da medida, e a Tabela E.8, as métricas por ensaio. A conversão das medições e as hipóteses adotadas são as "
        r"da Seção E.2. Em E4, a conversão prevista supera o limite estequiométrico de 0,40 em toda a curva, em até "
        + v(nv.loc["E4", "excesso_pp"], 1) + r" p.p.")
    tempos_n = [0.5, 1.0, 2.0, 3.0, 5.0, 15.0]
    linhas = []
    for e in ("E1", "E2", "E3", "E4"):
        s = np_[np_["ensaio"] == e].set_index("t_min")
        assert list(s.index) == tempos_n
        linhas.append([e, "Medida"] + [v(s.loc[t, "XZn_exp"], 3) for t in tempos_n])
        linhas.append(["", "Prevista"] + [v(s.loc[t, "XZn_mlp_pura"], 3) for t in tempos_n])
    w.table("Tabela E.7",
            r"Conversão de zinco medida e prevista pelo modelo *black-box* em cada instante de amostragem dos quatro "
            r"ensaios novos (rótulos de E2 e E3 trocados em relação à planilha)",
            ["Ensaio", "Conversão", "0,5 min", "1 min", "2 min", "3 min", "5 min", "15 min"],
            linhas, [1.6, 2.3, 1.8, 1.8, 1.8, 1.8, 1.8, 1.8])
    rot = {"Todos": "Todos", "Sem E1": "Sem o E1"}
    linhas = [[rot.get(e, e), str(int(nov.loc[e, "n"])), v(nov.loc[e, "RMSE_pp"]), v(nov.loc[e, "MAE_pp"]), v(nov.loc[e, "Emax_pp"]),
               v(nov.loc[e, "vies_pp"]), v(nov.loc[e, "incons_fis_pct"], 1)]
              for e in ("E1", "E2", "E3", "E4", "Todos", "Sem E1")]
    w.table("Tabela E.8",
            r"Métricas do modelo *black-box* nos ensaios novos e inconsistência física das curvas previstas; o desvio médio "
            r"é a média de (medido − previsto)",
            ["Ensaio", "Pontos", "RMSE (p.p.)", "MAE (p.p.)", "Erro máximo (p.p.)", "Desvio médio (p.p.)",
             "Inconsistência física (%)"],
            linhas, [1.9, 1.6, 2.0, 2.0, 2.3, 2.4, 2.9])


# ------------------------------------------------------------------------------------------- montagem
def aplicar(doc) -> tuple[int, int]:
    body = doc.element.body
    els = list(body.iterchildren())

    def achar(pred, inicio=0):
        return next(i for i, e in enumerate(els) if i >= inicio and e.tag == W_P and pred(e))

    i_met = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == TITULO_SERIAL)
    i_res = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip() == "RESULTADOS E DISCUSSÃO")
    i_conc = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip().startswith("CONCLUS"), i_res)
    i_ape = achar(lambda e: estilo(e) == "Heading1" and texto(e).strip().startswith("APÊNDICE E"), i_conc)
    i_e1 = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip().startswith("E.1 "), i_ape)
    i_e2 = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip().startswith("E.2 "), i_e1)
    assert not any(texto(e).strip() == TITULO for e in els if e.tag == W_P), "a origem já tem a seção do black-box"
    assert not any(texto(e).strip().startswith("E.3 ") for e in els[i_ape:] if e.tag == W_P), "a origem já tem E.3"

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

    d = carregar()
    w1 = SectionWriter(doc, refs, els[i_conc])
    secao(w1, titulo_como(els[i_met], w1), d)

    # Apêndice E passa a reunir os dois modelos: título, parágrafo de abertura e títulos de E.1 e E.2
    trocar(els[i_ape], "RESULTADOS COMPLETOS DO MODELO HÍBRIDO SERIAL", "RESULTADOS COMPLETOS DOS MODELOS HÍBRIDO SERIAL E BLACK-BOX")
    p_intro = els[i_ape + 1]
    assert texto(p_intro).startswith("Este apêndice reúne os resultados completos do modelo híbrido serial")
    for ch in list(p_intro):
        if ch.tag != qn("w:pPr"):
            p_intro.remove(ch)
    w1._fill(p_intro,
             rf"Este apêndice reúne os resultados completos do modelo híbrido serial e do modelo *black-box*, resumidos nas "
             rf"Seções {SECAO_SERIAL} e {SECAO}: as curvas, as métricas e a conversão de zinco medida e prevista em cada "
             r"instante, nos 16 ensaios de Bortot Coelho (2017) e nos quatro ensaios novos. Os erros estão em pontos "
             r"percentuais (p.p.) de conversão.")
    trocar(els[i_e1], "E.1 Ensaios do planejamento original", "E.1 Modelo híbrido serial: ensaios do planejamento original")
    trocar(els[i_e2], "E.2 Ensaios novos", "E.2 Modelo híbrido serial: ensaios novos")

    fim = len(els) - 1
    assert els[fim].tag == qn("w:sectPr")
    while els[fim - 1].tag == W_P and not texto(els[fim - 1]).strip() and not els[fim - 1].findall(".//" + qn("w:drawing")):
        fim -= 1
    w2 = SectionWriter(doc, refs, els[fim])
    apendice(w2, titulo_como(els[i_e1], w2), d)

    pintar(list(w1.inserted) + list(w2.inserted) + [p_intro])
    return len(w1.inserted), len(w2.inserted)


def main() -> None:
    with open(ORIGEM, "rb") as f:
        doc = docx.Document(io.BytesIO(f.read()))
    n1, n2 = aplicar(doc)
    doc.save(str(DESTINO))
    print(f"{DESTINO.name} gravada a partir da {ORIGEM.name}: Seção {SECAO} do black-box ({n1} blocos) e Seções E.3 e E.4 ({n2} blocos)")


if __name__ == "__main__":
    main()
