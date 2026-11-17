"""Testes do Item 2 da Etapa 4.5, com dados sintéticos."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from erro_por_faixa_de_tempo import (  # noqa: E402
    FAIXAS,
    MODELOS,
    TODOS,
    bootstrap_diferenca,
    erro_por_faixa,
    faixa_de_tempo,
    razao_inicial_final,
    resumo_tendencia,
)


@pytest.mark.parametrize("t, esperado", [(0.5, FAIXAS[0]), (1.0, FAIXAS[1]), (3.0, FAIXAS[1]), (4.0, FAIXAS[2]), (15.0, FAIXAS[2])])
def test_faixa_de_tempo(t: float, esperado: str) -> None:
    assert faixa_de_tempo(t) == esperado


def test_faixa_de_tempo_recusa_instante_estranho() -> None:
    with pytest.raises(ValueError):
        faixa_de_tempo(3.5)


def test_erro_por_faixa_usa_previsto_menos_medido_e_media_entre_sementes() -> None:
    previsoes = pd.concat([
        pd.DataFrame({
            "conjunto": ["CV"] * 2, "modelo": ["v2"] * 2, "semente": [42, 43], "ensaio": [1, 1], "t_min": [0.5, 0.5],
            "XZn_exp": [0.5, 0.5], "XZn_pred": [0.6, 0.3], "faixa": [faixa] * 2,
        })
        for faixa in FAIXAS
    ], ignore_index=True)
    linha = erro_por_faixa(previsoes).query("faixa == @TODOS").iloc[0]
    assert linha["RMSE"] == pytest.approx((0.1 + 0.2) / 2)
    assert linha["erro_medio_com_sinal"] == pytest.approx((0.1 - 0.2) / 2)
    assert linha["n_sementes"] == 2


def test_bootstrap_de_modelos_iguais_e_zero() -> None:
    sse = np.array([[0.01, 0.02, 0.03]])
    assert bootstrap_diferenca(sse, sse, 1, np.random.default_rng(0)) == pytest.approx((0.0, 0.0))


def test_bootstrap_usa_pontos_por_ensaio() -> None:
    sse_a = np.array([[0.09, 0.09]])
    sse_b = np.zeros((1, 2))
    inferior, superior = bootstrap_diferenca(sse_a, sse_b, 3, np.random.default_rng(0))
    assert inferior == pytest.approx(np.sqrt(0.09 / 3))
    assert superior == pytest.approx(np.sqrt(0.09 / 3))


def test_razao_inicial_final() -> None:
    medicoes = pd.DataFrame({"ensaio": [1, 1, 2, 2], "t_min": [0.5, 15.0, 0.5, 15.0], "XZn_exp": [0.45, 0.5, 0.8, 1.0]})
    assert razao_inicial_final(medicoes) == pytest.approx((0.9 + 0.8) / 2)


def test_resumo_tendencia_detecta_sinal_e_efeito() -> None:
    ca0 = [0.1, 0.5, 1.0, 1.5]
    subindo = [0.5, 0.6, 0.7, 0.7]
    linhas = {"XZn_exp": subindo, "v2": subindo, "mlp_pura": subindo[::-1]}
    tabela = pd.DataFrame({"eta": [1.0] * 4, "CA0_mol_L": ca0, "XZn_exp": linhas["XZn_exp"]})
    for modelo in MODELOS:
        tabela[modelo] = linhas.get(modelo, [0.6] * 4)
    resumo = resumo_tendencia(tabela).set_index("fonte")
    assert resumo.loc["v2", "eta_com_mesmo_sinal_da_medicao"] == 1
    assert resumo.loc["v2", "RMSE_desvio_CA0"] == pytest.approx(0.0)
    assert resumo.loc["v2", "correlacao_desvio_CA0"] == pytest.approx(1.0)
    assert resumo.loc["mlp_pura", "eta_com_mesmo_sinal_da_medicao"] == 0
    assert resumo.loc["mlp_pura", "correlacao_desvio_CA0"] < 0
