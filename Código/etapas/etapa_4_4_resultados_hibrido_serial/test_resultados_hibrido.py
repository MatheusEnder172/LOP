"""Testes da Subetapa 4.4 (figuras e tabelas de apoio aos Resultados do híbrido serial)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[2] / "outputs" / "etapa_4_4_resultados_hibrido_serial"


def test_figuras_em_png_e_pdf():
    for nome in ("fig_rh_01_curvas_16_ensaios", "fig_rh_02_paridade", "fig_rh_03_erro_por_ensaio", "fig_rh_04_mapa_conversao"):
        for ext in ("png", "pdf"):
            assert (OUT / f"{nome}.{ext}").stat().st_size > 10_000


def test_consistencia_fisica():
    c = pd.read_csv(OUT / "tabela_consistencia_fisica.csv").iloc[0]
    assert c["n_condicoes"] == 41 * 41
    assert c["x_acima_do_limite"] <= 1e-9 and c["x_decrescente"] <= 1e-9
    assert c["caf_min"] >= 0.0 and c["nu_nao_positivo"] == 0 and c["nu_min"] > 0.0


def test_tabelas_de_apoio_batem_com_a_etapa_4_2():
    erro = pd.read_csv(OUT / "tabela_erro_por_ensaio.csv")
    assert len(erro) == 16 and erro["teste_cego"].sum() == 3
    assert erro["RMSE_v2_fora_da_dobra"].notna().sum() == 13
    # RMSE global da v2 recomposto a partir dos 112 pontos: 0,0157
    pred = pd.read_csv(OUT.parent / "etapa_4_2_avaliacao_indomain" / "tabela_predicoes_detalhadas_16_ensaios.csv")
    rmse = float(((pred["XZn_exp"] - pred["XZn_Hibrido_MLP_v2"]) ** 2).mean() ** 0.5)
    assert round(rmse, 4) == 0.0157
