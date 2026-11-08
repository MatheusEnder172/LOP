"""Testes das Fases C e D (Subetapa 3.2.6): pesos D1 e PBM diferenciável."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parents[2]
for p in (SUBETAPA_DIR, CODIGO_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import fase_c_perdas_fisicas as fc  # noqa: E402
from modelo_mlp_v2 import carregar_ensemble_v2  # noqa: E402
from protocolo_cv import carregar_dados  # noqa: E402
from src.hybrid.pbm_torch import PBMTorch, montar_lote, nu_da_rede  # noqa: E402
from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402


@pytest.fixture(scope="module")
def dados():
    return carregar_dados()


def test_pesos_d1_com_gamma_zero_sao_unitarios(dados):
    w = fc.pesos_sensibilidade(dados, 0.0)
    assert np.all(w == 1.0) and len(w) == len(dados.train_df)


def test_pesos_d1_media_um_e_priorizam_o_inicio(dados):
    bruto = fc.pesos_brutos(dados)
    assert np.all(bruto >= 0.0)
    for g in (0.5, 1.0, 2.0):
        w = fc.pesos_sensibilidade(dados, g, bruto)
        assert abs(w.mean() - 1.0) < 1e-9 and np.all(w > 0.0)
    w = fc.pesos_sensibilidade(dados, 1.0, bruto)
    t = dados.train_df["t_min"].values
    assert w[t == 0.25].mean() > w[t == 5.0].mean() > w[t == 15.0].mean()


def test_matriz_dos_deltas_reproduz_o_esquema_serial():
    t = np.linspace(0.25, 15.0, 60)
    nu = np.abs(np.random.default_rng(0).normal(size=60)) * 5
    d_ref = np.zeros(60)
    d_ref[0] = nu[0] * t[0]
    for j in range(1, 60):
        d_ref[j] = d_ref[j - 1] + 0.5 * (nu[j] + nu[j - 1]) * (t[j] - t[j - 1])
    assert np.allclose(fc.matriz_dos_deltas(t) @ nu, d_ref)


def test_pbm_torch_reproduz_serial_hybrid(dados):
    ens = carregar_ensemble_v2(scaler_X=dados.scaler_X)
    pbm = PBMTorch(dados.solver)
    membro = ens.membros[0]
    ensaios = list(range(1, 17))
    x_lote, eta = montar_lote(dados.scaler_X, dados.meta, ensaios)
    with torch.no_grad():
        x_t = pbm(nu_da_rede(membro, x_lote), eta).numpy()
    hib = SerialHybridModel(ddm_model=membro, scaler_X=dados.scaler_X, solver=dados.solver)
    for k, e in enumerate(ensaios):
        m = dados.meta[dados.meta["ensaio"] == e].iloc[0]
        ref = hib.simulate(ca0=float(m["CA0_mol_L"]), eta=float(m["razao_molar_eta"]), t_eval=pbm.t_obs)["XZn"]
        assert np.abs(x_t[k] - ref).max() < 1e-6, f"ensaio {e}"


def test_pbm_torch_respeita_teto_e_tem_gradiente(dados):
    pbm = PBMTorch(dados.solver)
    nu = torch.full((2, 60), 50.0, dtype=torch.float64, requires_grad=True)
    x = pbm(nu, torch.tensor([0.4, 3.0], dtype=torch.float64))
    assert torch.all(x[0] <= 0.4 + 1e-12) and torch.all(x[1] <= 1.0 + 1e-12)
    x[1].sum().backward()
    assert torch.isfinite(nu.grad).all() and nu.grad[1].abs().sum() > 0
