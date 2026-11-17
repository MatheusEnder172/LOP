"""Testes do Item 1 da Etapa 4.5, com dados sintéticos."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from referencia_media_eta import bootstrap_diferenca, prever_referencias  # noqa: E402


def medicao(ensaio: int, ca0: float, eta: float, x: float, t: float = 0.5) -> dict:
    return {"ensaio": ensaio, "t_min": t, "CA0_mol_L": ca0, "eta": eta, "XZn_exp": x}


def tabela(*linhas: dict) -> pd.DataFrame:
    return pd.DataFrame(list(linhas))


def test_media_e_interpolacao_entre_vizinhos() -> None:
    treino = tabela(medicao(1, 0.1, 1.0, 0.2), medicao(2, 1.0, 1.0, 0.8), medicao(3, 0.5, 3.1, 0.99))
    previsto = prever_referencias(tabela(medicao(9, 0.55, 1.0, 0.0)), treino).iloc[0]
    assert previsto["media_eta"] == pytest.approx(0.5)
    assert previsto["interp_CA0"] == pytest.approx(0.5)


def test_vizinho_de_um_lado_usa_o_mais_proximo() -> None:
    treino = tabela(medicao(1, 0.5, 1.0, 0.4), medicao(2, 1.0, 1.0, 0.8))
    previsto = prever_referencias(tabela(medicao(9, 1.5, 1.0, 0.0)), treino).iloc[0]
    assert previsto["interp_CA0"] == pytest.approx(0.8)


def test_cada_instante_usa_so_o_proprio_instante() -> None:
    treino = tabela(medicao(1, 0.5, 1.0, 0.4, t=0.5), medicao(1, 0.5, 1.0, 0.9, t=15.0))
    previsto = prever_referencias(tabela(medicao(9, 0.5, 1.0, 0.0, t=15.0)), treino).iloc[0]
    assert previsto["media_eta"] == pytest.approx(0.9)


def test_ensaio_alvo_no_treino_e_erro() -> None:
    treino = tabela(medicao(1, 0.5, 1.0, 0.4))
    with pytest.raises(ValueError, match="presente no treino"):
        prever_referencias(tabela(medicao(1, 0.5, 1.0, 0.4)), treino)


def test_sem_vizinho_de_mesma_eta_e_erro() -> None:
    treino = tabela(medicao(1, 0.5, 3.1, 0.9))
    with pytest.raises(ValueError, match="Sem vizinho"):
        prever_referencias(tabela(medicao(9, 0.5, 1.0, 0.0)), treino)


def test_bootstrap_com_modelos_iguais_centra_em_zero() -> None:
    sse = np.array([0.01, 0.02, 0.005, 0.03])
    inferior, superior = bootstrap_diferenca(sse[np.newaxis, :], sse, np.random.default_rng(0))
    assert inferior == pytest.approx(0.0)
    assert superior == pytest.approx(0.0)


def test_bootstrap_com_v2_sempre_melhor_e_negativo() -> None:
    sse_ref = np.array([0.04, 0.05, 0.03, 0.06])
    inferior, superior = bootstrap_diferenca(0.25 * sse_ref[np.newaxis, :], sse_ref, np.random.default_rng(0))
    assert superior < 0
    assert inferior < superior
