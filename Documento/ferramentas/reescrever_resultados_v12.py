"""Gera a v12 a partir da v11 (sem alterá-la): escreve os Resultados do modelo híbrido serial no molde comum combinado com o grupo (10/11/2026).

Molde de cada modelagem: ajuste nos 13 ensaios de treino, teste cego (Ensaios 7, 8 e 14) com as métricas comuns
(R2, RMSE, MAE, erro máximo e inconsistência física), figura 2x2 dos Ensaios 3, 9, 7* e 14* e um resultado próprio
do modelo (aqui, a validação cruzada por ensaio e a dispersão do comitê). Só exposição: a comparação entre
modelagens e a discussão ficam em seção própria do grupo.

O bloco antigo de Resultados da serial (herdado da v10, mais longo) é substituído. Tudo em vermelho (texto novo
fora de Métodos). Todos os números são lidos dos CSVs de `Código/outputs/`. A v11 (seção 4.5 final) vem de
`reescrever_serial_v11.py`. Uso: python reescrever_resultados_v12.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import docx
import pandas as pd
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_utils import SectionWriter, pintar  # noqa: E402

DOC_DIR = Path(__file__).resolve().parents[1]
ORIGEM = DOC_DIR / "RELATÓRIO FINAL LOP_v11.docx"
DESTINO = DOC_DIR / "RELATÓRIO FINAL LOP_v12.docx"
OUT = DOC_DIR.parent / "Código" / "outputs"
SERIAL = OUT / "resultados_por_modelagem" / "serial"
SUB = OUT / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"
CONFIG_FINAL = "B2 – tentativa 511"
TITULO = "MODELAGEM HÍBRIDA SERIAL"
SECAO = "5.4"  # ordem do grupo: white-box (Fabrício), white-box novo, cooperativo, serial, PINN
W_P = qn("w:p")


def v(x: float, n: int = 2) -> str:
    """Número com vírgula decimal."""
    return f"{x:.{n}f}".replace(".", ",")


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
    d["res"] = res[res["modelo"] == "Híbrido serial"].set_index("particao")
    por = pd.read_csv(SERIAL / "metricas_por_ensaio.csv")
    d["por"] = por[por["modelo"] == "Híbrido serial"].set_index("ensaio")
    d["pts"] = pd.read_csv(SERIAL / "dados_plotados.csv")
    d["teto"] = pd.read_csv(SUB / "fase_a" / "tabela_fase_a_resumo.csv").set_index("referencia")["valor"]["teto"]
    fin = pd.read_csv(SUB / "fase_b2" / "tabela_fase_b2_finalistas.csv").set_index("config")
    d["vc"] = fin.loc[CONFIG_FINAL]
    dob = pd.read_csv(SUB / "fase_b2" / "finalistas_por_dobra.csv")
    dob = dob[dob["config"] == CONFIG_FINAL]
    assert dob["semente"].nunique() == 10 and sorted(dob["fold"].unique()) == [1, 2, 3, 4]
    d["dobras"] = dob.groupby("fold")["RMSE_X"].mean()
    d["erro"] = pd.read_csv(OUT / "etapa_4_4_resultados_hibrido_serial" / "tabela_erro_por_ensaio.csv").set_index("ensaio")
    d["mem"] = pd.read_csv(SUB / "fase_e" / "tabela_fase_e_membros_teste_cego.csv")
    d["pred"] = pd.read_csv(OUT / "etapa_4_2_avaliacao_indomain" / "tabela_predicoes_detalhadas_16_ensaios.csv")
    return d


def secao(w: SectionWriter, heading, d: dict) -> None:
    res, por, pts = d["res"], d["por"], d["pts"]
    tr, te, gl = res.loc["Treino"], res.loc["Teste cego"], res.loc["Global"]
    assert (tr["n_pontos"], te["n_pontos"], gl["n_pontos"]) == (91, 21, 112)
    assert res["incons_fis_pct"].max() == 0.0, "o texto afirma que não há inconsistência física"
    teto_pp = 100 * float(d["teto"])
    assert 0.9 < teto_pp / tr["RMSE_pp"] <= 1.0, "o erro de treino deixou de ficar próximo (e acima) da referência"

    # ponto de maior erro no teste cego
    cego = pts[pts["particao"] == "teste cego"].copy()
    cego["erro"] = (cego["XZn_serial"] - cego["XZn_exp"]).abs()
    pior = cego.loc[cego["erro"].idxmax()]
    assert abs(100 * pior["erro"] - te["Emax_pp"]) < 1e-3

    # validação cruzada (10 sementes, 4 dobras por ensaio)
    vc, vc_dp = 100 * float(d["vc"]["RMSE_X_media"]), 100 * float(d["vc"]["RMSE_X_dp"])
    dob = 100 * d["dobras"]
    fora = (100 * d["erro"]["RMSE_v2_fora_da_dobra"]).dropna().sort_values(ascending=False)
    assert len(fora) == 13
    top = fora.index[:3].tolist()
    assert set(d["erro"].loc[top, "CA0_mol_L"]) <= {0.1, 1.5}, "os piores ensaios deixaram de estar nos extremos de C_A0"

    # comitê
    pred = d["pred"][d["pred"]["t_min"] > 0]
    assert len(pred) == 112
    faixa = 100 * (pred["XZn_Hibrido_MLP_v2_max"] - pred["XZn_Hibrido_MLP_v2_min"])
    mem = 100 * d["mem"]["RMSE_teste_cego"]
    assert len(mem) == 10

    # patamar do Ensaio 9 (η = 1,0)
    e9 = pts[(pts["ensaio"] == 9) & (pts["t_min"] == 15.0)].iloc[0]
    assert e9["eta"] == 1.0 and e9["XZn_exp"] < 0.9

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
            [2.3, 1.5, 1.5, 1.6, 1.9, 1.9, 2.3, 2.8])

    w.paragraph(
        rf"A Figura {SECAO}.1 compara as curvas previstas com as medições em quatro ensaios, um para cada razão molar, ao "
        r"lado do modelo *white-box* da Seção 4.1; as curvas dos 16 ensaios são apresentadas no Apêndice E. O modelo "
        r"acompanha a etapa inicial rápida e o patamar de cada ensaio, inclusive com $\eta=1,0$ (Ensaio 9), em que a "
        r"conversão medida em 15 min é de " + v(e9["XZn_exp"]) + r", abaixo do limite estequiométrico, e a prevista é de "
        + v(e9["XZn_serial"]) + r".")
    w.figure(SERIAL / "fig_serial_2x2_texto_ensaios_03_09_07_14.png", 16.0, f"Figura {SECAO}.1",
             "Conversão de zinco medida e prevista pelo modelo híbrido serial e pelo modelo *white-box* nos Ensaios 3, 9, "
             "7 e 14; o asterisco indica ensaio de teste cego")
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


def aplicar(doc) -> int:
    body = doc.element.body
    els = list(body.iterchildren())

    def achar(pred, inicio=0):
        return next(i for i, e in enumerate(els) if i >= inicio and e.tag == W_P and pred(e))

    i_met = achar(lambda e: estilo(e) == "Heading3" and texto(e).strip() == TITULO)
    i_res = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip() == "RESULTADOS E DISCUSSÃO")
    i_conc = achar(lambda e: estilo(e) == "Heading2" and texto(e).strip().startswith("CONCLUS"), i_res)
    assert i_met < i_res < i_conc

    # bloco antigo da serial em Resultados (do título até CONCLUSÕES)
    antigos = [i for i in range(i_res + 1, i_conc) if els[i].tag == W_P and estilo(els[i]) == "Heading3"
               and texto(els[i]).strip() == TITULO]
    if antigos:
        for e in els[antigos[0]:i_conc]:
            body.remove(e)

    i_cap = achar(lambda e: texto(e).strip().startswith("Figura 4.5.1 –"), i_met)
    refs = {"body": els[achar(lambda e: texto(e).startswith("Com essa escolha, a rede neural fica responsável"), i_met)],
            "figure": els[i_cap - 1], "caption": els[i_cap], "source": els[i_cap + 1]}
    w = SectionWriter(doc, refs, els[i_conc])

    def heading(txt: str) -> None:
        import copy
        from docx.oxml import parse_xml
        from docx.oxml.ns import nsdecls
        p = parse_xml(f"<w:p {nsdecls('w')}/>")
        p.append(copy.deepcopy(els[i_met].find(qn("w:pPr"))))
        p.append(SectionWriter._run(txt))
        w._place(p)

    secao(w, heading, carregar())
    pintar(list(w.inserted))
    return len(w.inserted)


def main() -> None:
    with open(ORIGEM, "rb") as f:   # leitura por cópia: funciona mesmo com a v11 aberta no Word
        doc = docx.Document(io.BytesIO(f.read()))
    n = aplicar(doc)
    doc.save(str(DESTINO))
    print(f"{DESTINO.name} gravada a partir da {ORIGEM.name}: Resultados da serial (Seção {SECAO}), {n} blocos, em vermelho")


if __name__ == "__main__":
    main()
