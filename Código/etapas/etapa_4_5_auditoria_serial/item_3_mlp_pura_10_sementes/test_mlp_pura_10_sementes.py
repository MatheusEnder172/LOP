"""Testes do Item 3 da Etapa 4.5, sem treinar redes."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mlp_pura_10_sementes import (  # noqa: E402
    bootstrap_por_ensaio,
    comparar,
    conferir_reproducao,
    matriz_sse,
    rmse_por_semente,
)


def oof_sintetico() -> pd.DataFrame:
    return pd.DataFrame({
        "semente": [42, 42, 43, 43], "ensaio": [1, 2, 1, 2], "t_min": [0.5] * 4,
        "XZn_exp": [0.5, 0.5, 0.5, 0.5], "XZn_pred": [0.4, 0.5, 0.3, 0.5],
    })


def test_rmse_por_semente() -> None:
    resultado = rmse_por_semente(oof_sintetico())
    assert resultado.loc[42] == pytest.approx(np.sqrt(0.01 / 2))
    assert resultado.loc[43] == pytest.approx(np.sqrt(0.04 / 2))


def test_matriz_sse_respeita_ordem() -> None:
    matriz = matriz_sse(oof_sintetico(), [43, 42], [2, 1])
    assert matriz == pytest.approx(np.array([[0.0, 0.04], [0.0, 0.01]]))


def test_conferir_reproducao_aceita_valor_igual() -> None:
    conferir_reproducao(0.04214, 0.042141)


def test_conferir_reproducao_interrompe_se_diferente() -> None:
    with pytest.raises(SystemExit, match="não reproduzem"):
        conferir_reproducao(0.0430, 0.0421)


def test_bootstrap_de_modelos_iguais_e_zero() -> None:
    sse = np.array([[0.01, 0.02, 0.03], [0.02, 0.01, 0.04]])
    inferior, superior = bootstrap_por_ensaio(sse, sse, np.random.default_rng(0))
    assert (inferior, superior) == pytest.approx((0.0, 0.0))


def test_comparar_detecta_v2_melhor_em_todas_as_sementes() -> None:
    n_sementes, n_ensaios = 10, 13
    sse_pura = np.full((n_sementes, n_ensaios), 0.04) + np.random.default_rng(0).uniform(0, 0.01, (n_sementes, n_ensaios))
    sse_v2 = 0.25 * sse_pura
    v2, pura = np.sqrt(sse_v2.sum(axis=1) / 91), np.sqrt(sse_pura.sum(axis=1) / 91)
    linha = comparar("teste", v2, pura, sse_v2, sse_pura, np.random.default_rng(0))
    assert linha["sementes_v2_ganha"] == 10
    assert linha["IC95_ensaios_sup"] < 0
    assert linha["IC_ensaios_exclui_zero"] is True
    assert linha["p_wilcoxon"] < 0.01


def test_comparar_nao_testa_com_poucas_sementes() -> None:
    sse = np.array([[0.01, 0.02], [0.02, 0.01], [0.03, 0.01]])
    v2 = np.array([0.03, 0.03, 0.035])
    linha = comparar("poucas", v2, v2 + 0.01, sse, 2 * sse, np.random.default_rng(0))
    assert np.isnan(linha["p_t_pareado"])
    assert np.isnan(linha["p_wilcoxon"])
