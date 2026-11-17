"""Testes do Item 4 da Etapa 4.5, sem carregar o comitê."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delta_e_taxas_medias import INSTANTES, TODOS, inverter_g, metricas, pesos_quadratura, taxas_por_intervalo  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402


@pytest.fixture(scope="module")
def solver() -> BatchPBMSolver:
    return BatchPBMSolver(n_mesh_points=800, n_delta_points=200)


def test_inverter_g_e_a_inversa_de_g(solver: BatchPBMSolver) -> None:
    for x in (0.1, 0.5, 0.9):
        assert solver.compute_conversion_from_delta(inverter_g(x, solver)) == pytest.approx(x, abs=1e-5)


@pytest.mark.parametrize("x", [0.0, 1.0, 1.01])
def test_inverter_g_recusa_conversao_fora_do_dominio(x: float, solver: BatchPBMSolver) -> None:
    assert np.isnan(inverter_g(x, solver))


def test_taxas_com_delta_linear_sao_constantes() -> None:
    assert taxas_por_intervalo(2.0 * INSTANTES) == pytest.approx(np.full(7, 2.0))


def test_taxa_propaga_ponto_nao_determinado() -> None:
    deltas = 2.0 * INSTANTES
    deltas[2] = np.nan
    taxas = taxas_por_intervalo(deltas)
    assert np.isnan(taxas[2]) and np.isnan(taxas[3])
    assert np.isfinite(taxas[1]) and np.isfinite(taxas[4])


def test_pesos_em_0_5_min(solver: BatchPBMSolver) -> None:
    pesos = pesos_quadratura(solver)
    linha = pesos[pesos["t_medicao"] == 0.5].sort_values("t_no")
    assert linha["t_no"].tolist() == [0.25, 0.5]
    assert linha["peso"].to_numpy() == pytest.approx([0.375, 0.125])


def test_soma_dos_pesos_e_o_tempo(solver: BatchPBMSolver) -> None:
    soma = pesos_quadratura(solver).groupby("t_medicao")["peso"].sum()
    assert soma.to_numpy() == pytest.approx(INSTANTES)


def test_metricas_medem_previsto_menos_medido() -> None:
    pares = pd.DataFrame({
        "grandeza": ["delta"] * 2, "conjunto": ["CV"] * 2, "grupo": ["0,5 min"] * 2, "modelo": ["m"] * 2,
        "semente": [1, 2], "ensaio": [1, 1], "medido": [10.0, 10.0], "previsto": [12.0, 6.0],
    })
    linha = metricas(pares).query("grupo == @TODOS").iloc[0]
    assert linha["RMSE"] == pytest.approx(3.0)
    assert linha["erro_medio_com_sinal"] == pytest.approx(-1.0)
