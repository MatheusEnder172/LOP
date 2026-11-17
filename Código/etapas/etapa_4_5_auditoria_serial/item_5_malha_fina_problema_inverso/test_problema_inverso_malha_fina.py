"""Testes do Item 5 da Etapa 4.5."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad

sys.path.insert(0, str(Path(__file__).resolve().parent))
import problema_inverso_malha_fina as item5  # noqa: E402

THETA = np.array([30.0, 5.0, 4.0, 0.5, 0.01])


def test_delta_exato_e_a_integral_da_taxa() -> None:
    t = np.array([0.25, 1.0, 15.0])
    delta, _ = item5.perfil_exato(THETA, t)
    for valor, instante in zip(delta, t):
        integral, _ = quad(lambda s: item5.perfil_exato(THETA, np.array([s]))[1][0], 0.0, instante, epsabs=1e-12, epsrel=1e-12)
        assert valor == pytest.approx(integral, rel=1e-9)


def test_limites_e_partidas_iguais_aos_da_etapa_2_1() -> None:
    fonte = inspect.getsource(item5.etapa21.optimize_single_experiment)
    assert "bounds = [(0.0, 250.0), (0.2, 8.0), (0.0, 80.0), (0.02, 4.0), (0.0, 0.03)]" in fonte
    assert item5.LIMITES == [(0.0, 250.0), (0.2, 8.0), (0.0, 80.0), (0.02, 4.0), (0.0, 0.03)]
    for ponto in item5.PONTOS_DE_PARTIDA:
        assert str(ponto) in fonte


def test_penalizacoes_iguais_as_da_etapa_2_1() -> None:
    fonte = inspect.getsource(item5.etapa21.optimize_single_experiment)
    for trecho in ("pen_tail = 1e-4 * (v_15 ** 2)", "pen_delta = 1e-4 * (max(0.0, delta_15 - 140.0) ** 2)", "pen_smooth = 1e-7 * (a1 ** 2) + 1e-6 * ((b1 - 4.0) ** 2)"):
        assert trecho in fonte


def test_perda_exata_soma_as_penalizacoes() -> None:
    solver = item5.BatchPBMSolver(n_mesh_points=800, n_delta_points=200)
    delta, taxa = item5.perfil_exato(THETA, item5.T_DENSO)
    x = np.clip(solver.compute_conversion_from_delta(delta), 0.0, 1.0)[item5.INDICES]
    esperado = 1e-4 * taxa[-1] ** 2 + 1e-7 * THETA[0] ** 2 + 1e-6 * (THETA[1] - 4.0) ** 2
    assert item5.perda_exata(THETA, solver, x) == pytest.approx(esperado)


def test_parametros_no_limite() -> None:
    assert item5.parametros_no_limite(np.array([100.0, 8.0, 40.0, 1.0, 0.0])) == ["b1", "c"]


def test_taxas_medias_de_delta_linear() -> None:
    assert item5.taxas_medias(3.0 * item5.INSTANTES) == pytest.approx(np.full(7, 3.0))
