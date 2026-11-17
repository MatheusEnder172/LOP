"""Testes do modelo de gráficos de Resultados (resultados_lop): 16 ensaios, 3 formatos, métricas, CSV de curvas."""

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import padrao_graficos_lop as pg  # noqa: E402
import resultados_lop as rl  # noqa: E402


@pytest.fixture(scope="module")
def exp():
    return rl.carregar_experimentos()


@pytest.fixture(scope="module")
def curvas(exp):
    """Dois 'modelos' sintéticos (sem solver): um simples e um perfeito nos pontos experimentais."""
    sint = rl.curvas_de_funcao(lambda ca0, eta, t: min(1.0, eta) * (1 - np.exp(-3 * np.asarray(t))), exp)
    return {"novo": sint, "pinn": rl.curvas_de_funcao(lambda ca0, eta, t: 0.8 * min(1.0, eta) * (1 - np.exp(-2 * np.asarray(t))), exp)}


def test_dados_16_ensaios_13_treino_3_cegos(exp):
    assert exp["ensaio"].nunique() == 16 and len(exp) == 112 and (exp["t_min"] > 0).all()
    assert exp.loc[exp["particao"] == "treino", "ensaio"].nunique() == 13 and len(exp[exp["particao"] == "treino"]) == 91
    assert sorted(exp.loc[exp["particao"] == "teste cego", "ensaio"].unique()) == [7, 8, 14]


def test_tres_formatos_tem_o_numero_certo_de_paineis(exp, curvas):
    f1 = rl.grafico_individual(9, exp, curvas)
    f2 = rl.grafico_2x2([1, 2, 3, 4], exp, curvas)
    f4 = rl.grafico_4x4(exp, curvas)
    assert [len(f.axes) for f in (f1, f2, f4)] == [1, 4, 16]
    assert all(abs(f.get_figwidth() * 2.54 - 16) < 1e-6 for f in (f1, f2, f4))
    for f in (f1, f2, f4):
        assert all(a.get_title() == "" for a in f.axes)
        assert f.legends and len(f.legends[0].get_texts()) == 4   # white-box, modelagem, limite, experimental
    textos = [t.get_text() for t in f4.axes[6].texts]
    assert "Ensaio 7*" in textos   # teste cego com asterisco
    pg.plt.close("all")


def test_cores_das_modelagens_sao_as_do_padrao(exp, curvas):
    fig = rl.grafico_individual(3, exp, curvas)
    cores = {l.get_color().lower() for l in fig.axes[0].lines}
    assert pg.MODELOS["novo"].cor.lower() in cores and pg.MODELOS["pinn"].cor.lower() in cores
    pg.plt.close(fig)


def test_metricas_particoes_e_modelo_perfeito(exp):
    perfeito = {e: rl.Curva(np.array([0.0, 15.0]), np.array([0.0, 1.0]), exp.loc[exp["ensaio"] == e, "XZn"].to_numpy()) for e in range(1, 17)}
    por, res = rl.metricas(exp, {"hib": perfeito})
    assert res["n_pontos"].tolist() == [91, 21, 112] and res["n_ensaios"].tolist() == [13, 3, 16]
    assert res["RMSE_pp"].abs().max() < 1e-9 and np.allclose(res["R2"], 1.0)
    assert len(por) == 16
    for tabela in (por, res):   # métricas comuns do grupo
        assert {"Emax_pp", "incons_fis_pct"} <= set(tabela.columns) and tabela["Emax_pp"].abs().max() < 1e-9


def test_inconsistencia_fisica_conta_queda_e_excesso_sobre_o_limite():
    t = np.array([0.0, 1.0, 2.0, 15.0])
    sobe_passa_e_cai = rl.Curva(t, np.array([0.0, 0.6, 0.5, 0.5]), np.array([]))
    # com η = 0,5: nó de 1,00 min acima do limite; 1,25 a 1,75 acima e caindo; 2,00 caindo; depois constante no limite
    assert rl.inconsistencia_fisica(sobe_passa_e_cai, eta=0.5) == (5, 61)
    assert rl.inconsistencia_fisica(sobe_passa_e_cai, eta=3.1) == (4, 61)   # sem limite de ácido, só a queda conta
    consistente = rl.Curva(t, np.array([0.0, 0.4, 0.5, 0.5]), np.array([]))
    assert rl.inconsistencia_fisica(consistente, eta=0.5) == (0, 61)


def test_csv_de_curvas_ida_e_volta(exp, curvas, tmp_path):
    rl.salvar_curvas_csv(curvas["pinn"], tmp_path / "curvas_pinn.csv")
    volta = rl.curvas_de_csv(tmp_path / "curvas_pinn.csv", exp)
    for e in (1, 7, 16):
        assert np.allclose(volta[e].x_pts, curvas["pinn"][e].x_pts, atol=2e-3)   # interpolação na grade densa


def test_prever_com_formato_errado_da_erro_claro(exp):
    with pytest.raises(ValueError, match="mesmo tamanho"):
        rl.curvas_de_funcao(lambda ca0, eta, t: np.zeros(3), exp)


def test_gerar_figuras_grava_22_arquivos_png_e_pdf(exp, curvas, tmp_path):
    png = rl.gerar_figuras(curvas, exp, tmp_path, "pinn")
    assert len(png) == 22 and len(list(tmp_path.glob("*.pdf"))) == 22
    assert (tmp_path / "fig_pinn_2x2_texto_ensaios_01_07_08_14.png").exists()   # figura do texto de Resultados
    w, h = Image.open(tmp_path / "fig_pinn_4x4_todos.png").size
    assert abs(w - round(16 / 2.54 * 300)) <= 1 and h > w


def test_gerar_do_modelo_recusa_referencias():
    with pytest.raises(ValueError):
        rl.gerar_do_modelo("novo", prever=lambda a, b, t: t)


def test_modelagens_disponiveis_e_juntar_curvas_usam_pontos_exatos(exp, curvas, tmp_path):
    assert rl.modelagens_disponiveis(tmp_path) == []
    pasta = tmp_path / "pinn"
    pasta.mkdir()
    rl.salvar_curvas_csv(curvas["pinn"], pasta / "curvas_pinn.csv")
    import pandas as pd
    linhas = [{"ensaio": e, "XZn_pinn": v} for e in range(1, 17) for v in curvas["pinn"][e].x_pts]
    pd.DataFrame(linhas).to_csv(pasta / "dados_plotados.csv", index=False)
    assert rl.modelagens_disponiveis(tmp_path) == ["pinn"]
    juntas = rl.juntar_curvas(tmp_path, exp=exp, wb=curvas["novo"])
    assert list(juntas) == ["novo", "pinn"]
    for e in (1, 9, 14):
        assert np.allclose(juntas["pinn"][e].x_pts, curvas["pinn"][e].x_pts, rtol=0, atol=1e-9)   # exatos (só ruído de CSV), não interpolados
    assert len(rl.grafico_2x2([1, 2, 3, 4], exp, juntas).axes) == 4
    pg.plt.close("all")
