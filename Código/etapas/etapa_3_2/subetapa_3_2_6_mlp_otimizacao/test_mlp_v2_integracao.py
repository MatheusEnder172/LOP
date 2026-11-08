"""Testes da integração da MLP v2 (comitê de 10 redes) ao `SerialHybridModel` e à Etapa 4.2.

Critério de aceitação (07/11/2026): nenhum número muda.
- v1 (`model_type="mlp"`): RMSE global de X_Zn de 0,0257.
- v2 (`model_type="mlp_v2"`): reproduz a Fase E (treino 0,0145; teste cego 0,0202; global 0,0157).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parents[2]
for p in (SUBETAPA_DIR, CODIGO_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402

FASE_E_CSV = CODIGO_DIR / "outputs" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao" / "fase_e" / "predicoes_fase_e_pontos_experimentais.csv"
ENSAIOS_TESTE = [7, 8, 14]


def _rmse(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


@pytest.fixture(scope="module")
def hib_v2() -> SerialHybridModel:
    return SerialHybridModel(model_type="mlp_v2")


@pytest.fixture(scope="module")
def hib_v1() -> SerialHybridModel:
    return SerialHybridModel(model_type="mlp")


@pytest.fixture(scope="module")
def fase_e() -> pd.DataFrame:
    return pd.read_csv(FASE_E_CSV)


def test_mlp_v2_instancia_comite(hib_v2):
    assert hib_v2.model_type == "mlp"
    assert len(hib_v2.model.membros) == 10
    assert "MLP v2" in hib_v2.model_name
    assert hib_v2.scaler_X is not None


def test_mlp_v2_reproduz_fase_e_ponto_a_ponto(hib_v2, fase_e):
    lote = hib_v2.simulate_batch(use_experimental_timepoints_only=True)
    m = fase_e.merge(lote, on=["ensaio", "t_min"])
    assert len(m) == 112
    assert np.abs(m["XZn_pred"] - m["XZn_v2_ensemble"]).max() < 1e-9


def test_mlp_v2_metricas_da_fase_e(hib_v2):
    lote = hib_v2.simulate_batch(use_experimental_timepoints_only=True)
    teste = lote["ensaio"].isin(ENSAIOS_TESTE)
    rmse = lambda d: round(_rmse(d["XZn_exp"], d["XZn_pred"]), 4)  # noqa: E731
    assert rmse(lote[~teste]) == 0.0145
    assert rmse(lote[teste]) == 0.0202
    assert rmse(lote) == 0.0157


def test_v1_continua_com_rmse_global_0257(hib_v1):
    lote = hib_v1.simulate_batch(use_experimental_timepoints_only=True)
    assert round(_rmse(lote["XZn_exp"], lote["XZn_pred"]), 4) == 0.0257


@pytest.mark.parametrize("eta,ca0", [(0.40, 0.25), (0.75, 0.25), (1.25, 0.75), (2.25, 0.75), (3.1, 1.5), (0.5, 0.1)])
def test_mlp_v2_respeita_limites_fisicos(hib_v2, eta, ca0):
    t = np.linspace(0.0, 15.0, 121)
    r = hib_v2.simulate(ca0=ca0, eta=eta, t_eval=t)
    assert r["XZn"][0] == 0.0
    assert np.all(r["XZn"] >= 0.0)
    assert np.all(r["XZn"] <= min(1.0, eta) + 1e-9)
    assert np.all(np.diff(r["XZn"]) >= -1e-12)
    assert np.all(r["CAf"] >= 0.0)
    assert np.all(r["abs_v"] >= 0.0)


def test_simulate_members_formato_e_ordem(hib_v2):
    t = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0])
    r = hib_v2.simulate_members(ca0=0.75, eta=1.25, t_eval=t)
    assert r["XZn_membros"].shape == (10, 7)
    assert r["CAf_membros"].shape == (10, 7)
    assert np.all(r["XZn_min"] <= r["XZn_media"] + 1e-12)
    assert np.all(r["XZn_media"] <= r["XZn_max"] + 1e-12)
    assert np.all(r["XZn_dp"] >= 0.0)
    assert np.all(r["XZn_membros"] <= min(1.0, 1.25) + 1e-9)
    # o comitê (média de ν antes do PBM) fica dentro da faixa dos membros
    c = hib_v2.simulate(ca0=0.75, eta=1.25, t_eval=t)["XZn"]
    assert np.all(c >= r["XZn_min"] - 1e-9) and np.all(c <= r["XZn_max"] + 1e-9)


def test_simulate_members_reproduz_faixa_da_fase_e(hib_v2, fase_e):
    for ens in (3, 7, 12):
        sub = fase_e[fase_e["ensaio"] == ens].sort_values("t_min")
        meta = hib_v2.simulate_experiment(ens, use_experimental_timepoints_only=True)
        r = hib_v2.simulate_members(ca0=meta["CA0"], eta=meta["eta"], t_eval=meta["t"])
        assert np.abs(r["XZn_min"] - sub["XZn_v2_membro_min"].values).max() < 1e-9
        assert np.abs(r["XZn_max"] - sub["XZn_v2_membro_max"].values).max() < 1e-9
        assert np.abs(r["XZn_dp"] - sub["XZn_v2_membro_dp"].values).max() < 1e-9


def test_simulate_members_recusa_modelo_sem_comite(hib_v1):
    with pytest.raises(TypeError):
        hib_v1.simulate_members(ca0=0.5, eta=1.0)
