"""
Suíte de Testes Unitários — Etapa 0.3: Transformação da Distribuição RRB (Divisão por D³)
e Validação do Acoplamento ao White-Box (BatchPBMSolver) sem Alterar a Equação de Conversão.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from sklearn.metrics import r2_score

PROJECT_CODE_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_CODE_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_CODE_ROOT))

from src.physics.granulometry import RosinRammlerBennet
from src.physics.pbm_batch import BatchPBMSolver
from etapas.etapa_0_3_transformacao_rrb_d3.avaliar_transformacao_rrb_d3 import RosinRammlerNumeroD3


def test_normalizacao_densidade_numerica_d3() -> None:
    """Verifica se a densidade dividida por D³ está devidamente normalizada (integral = 1.0)."""
    rrb_num = RosinRammlerNumeroD3()
    d_mesh, f0_mesh, m3_0 = rrb_num.generate_mesh(d_min=0.01, d_max=297.0, n_points=5000)
    integral_f0 = float(trapezoid(f0_mesh, d_mesh))
    assert np.isclose(integral_f0, 1.0, rtol=1e-5)
    assert m3_0 > 0.0


def test_recuperacao_exata_distribuicao_massica_no_pbm() -> None:
    """Verifica se D³ · f_n(D) normalizado recupera exatamente a densidade mássica f_m(D) da RRB."""
    rrb_massa = RosinRammlerBennet()
    rrb_num = RosinRammlerNumeroD3()
    d_mesh, fn_mesh, m3_0 = rrb_num.generate_mesh(d_min=0.01, d_max=297.0, n_points=5000)

    # Peso volumétrico relativo na integral de conversão do PBM: (D³ · f_n(D)) / M3(0)
    peso_vol_pbm = (d_mesh ** 3) * fn_mesh / m3_0
    fm_esperada = rrb_massa.probability_density(d_mesh)
    fm_esperada_norm = fm_esperada / float(trapezoid(fm_esperada, d_mesh))

    max_diff = float(np.max(np.abs(peso_vol_pbm - fm_esperada_norm)))
    assert max_diff < 1e-12


def test_conservacao_massa_e_monotonicidade_conversao() -> None:
    """Confirma que X_Zn(δ) permanece estritamente em [0, 1] e monotonicamente crescente."""
    solver_novo = BatchPBMSolver(granulometry=RosinRammlerNumeroD3(), n_mesh_points=5000)
    deltas = np.linspace(0.0, 297.0, 300)
    x_vals = solver_novo.compute_conversion_from_delta(deltas)

    assert np.isclose(x_vals[0], 0.0, atol=1e-9)
    assert np.isclose(x_vals[-1], 1.0, atol=1e-6)
    assert np.all((x_vals >= -1e-12) & (x_vals <= 1.0 + 1e-12))
    assert np.all(np.diff(x_vals) >= -1e-12)


def test_ganho_expressivo_whitebox_16_ensaios() -> None:
    """Verifica se a divisão da RRB por D³ eleva o R² global do White-Box (α=5500) de ~0,9030 para > 0,955."""
    base_dir = PROJECT_CODE_ROOT.parent
    cin_csv = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    df_exp = pd.read_csv(cin_csv)

    solver_antigo = BatchPBMSolver(granulometry=RosinRammlerBennet(use_number_density_d3=False), n_mesh_points=5000)
    solver_novo = BatchPBMSolver(granulometry=RosinRammlerNumeroD3(), n_mesh_points=5000)

    y_true, y_old, y_new = [], [], []
    for ens in sorted(df_exp["ensaio"].unique()):
        sub = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
        ca0 = float(sub["CA0_mol_L"].iloc[0])
        eta = float(sub["razao_molar_eta"].iloc[0])
        t_exp = sub["t_min"].values
        x_exp = sub["XZn"].values

        res_old = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=5500.0)
        res_new = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=5500.0)

        y_true.extend(x_exp)
        y_old.extend(res_old["XZn"])
        y_new.extend(res_new["XZn"])

    r2_old = float(r2_score(y_true, y_old))
    r2_new = float(r2_score(y_true, y_new))

    assert np.isclose(r2_old, 0.9030, atol=1e-3)
    assert r2_new > 0.9550
    assert r2_new > r2_old + 0.050
