"""
Suíte de Testes Unitários e Validação Numérica do Resolvedor PBM Batelada (Etapa 1.3).
Testa o módulo `src/physics/pbm_batch.py` e a classe `BatchPBMSolver`
sob a Nova Abordagem Oficial (`RRB ÷ D³` e White-Box Puro sem α).
"""

import sys
from pathlib import Path
import numpy as np

# Adicionar a pasta raiz de código ao path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.physics.granulometry import RosinRammlerBennet, RosinRammlerNumeroD3, RosinRammlerMassaAntiga
from src.physics.kinetics import LeachingKinetics
from src.physics.pbm_batch import BatchPBMSolver


def test_monotonicity_and_bounds_conversion():
    """Testa se X_Zn(delta) é estritamente monótona crescente e limitada no intervalo [0, 1] na Nova Abordagem."""
    solver = BatchPBMSolver()
    assert solver.granulometry.use_number_density_d3 is True

    delta_test = np.linspace(0.0, 297.0, 300)
    x_test = solver.compute_conversion_from_delta(delta_test)

    # Limites físicos
    assert np.isclose(x_test[0], 0.0, atol=1e-5), f"X_Zn(0) deve ser 0, obtido: {x_test[0]}"
    assert np.all(x_test >= -1e-12), "X_Zn não pode ser negativo."
    assert np.all(x_test <= 1.0 + 1e-12), "X_Zn não pode exceder 1,0."
    assert np.isclose(x_test[-1], 1.0, atol=1e-4), f"X_Zn(Dmax) deve ser 1, obtido: {x_test[-1]}"

    # Monotonicidade: dX/d(delta) >= 0
    diffs = np.diff(x_test)
    assert np.all(diffs >= -1e-8), "X_Zn(delta) deve ser monótona não-decrescente."
    print("  [OK] Monotonicidade e limites [0, 1] da conversão aprovados.")


def test_whitebox_puro_stoichiometric_limits():
    """Testa se o White-Box Puro oficial (alpha = 0.0) respeita os tetos estequiométricos de conversão."""
    solver = BatchPBMSolver()  # kinetics.alpha_nominal = 0.0

    # 1. Deficiência estequiométrica severa: eta = 0.5 -> conversão deve atingir 0.50
    t_eval = np.array([0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0])
    res_05 = solver.simulate(ca0=0.50, eta=0.5, t_eval=t_eval)
    assert res_05["success"]
    assert np.isclose(res_05["XZn"][-1], 0.50, atol=1e-3), f"Esperado 0.50, obtido: {res_05['XZn'][-1]}"
    assert np.isclose(res_05["CAf"][-1], 0.0, atol=1e-3), f"Ácido deve esgotar (0.0), obtido: {res_05['CAf'][-1]}"

    # 2. Excesso estequiométrico: eta = 3.1 -> conversão deve atingir 100%
    res_31 = solver.simulate(ca0=1.00, eta=3.1, t_eval=t_eval)
    assert res_31["success"]
    assert np.isclose(res_31["XZn"][-1], 1.0, atol=1e-3), f"Esperado 1.0, obtido: {res_31['XZn'][-1]}"
    print("  [OK] Tetos estequiométricos no White-Box Puro validados com sucesso.")


def test_theoretical_stopping_historical_alpha():
    """Testa se quando alpha = 5500 µm/min é solicitado, converge para o patamar histórico de Coelho."""
    kin = LeachingKinetics(alpha_nominal=5500.0, ks=18000.0)
    solver = BatchPBMSolver(kinetics=kin)

    ca0 = 0.50
    eta = 1.0
    t_eval = np.array([0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 30.0])

    res = solver.simulate(ca0=ca0, eta=eta, t_eval=t_eval)
    assert res["success"]

    # Limite analítico esperado: X_max = 1.0 * [1 - 5500/23500] = 0.7660
    x_theoretical_max = kin.theoretical_max_conversion(eta=eta)
    caf_stopping = kin.dissolution_stopping_acid(ca0=ca0)

    x_final_sim = res["XZn"][-1]
    caf_final_sim = res["CAf"][-1]

    assert np.isclose(x_final_sim, x_theoretical_max, atol=2e-3), f"{x_final_sim} vs {x_theoretical_max}"
    assert np.isclose(caf_final_sim, caf_stopping, atol=2e-3), f"{caf_final_sim} vs {caf_stopping}"
    print(f"  [OK] Limite assintótico histórico (α = 5500) validado: X_final = {x_final_sim:.4f}.")


def test_simulate_with_v_profile():
    """Testa o método de acoplamento com perfil de velocidade arbitrário."""
    solver = BatchPBMSolver()

    t_eval = np.linspace(0.0, 10.0, 11)
    # Perfil constante v = -2 µm/min
    v_profile = np.full_like(t_eval, -2.0)

    res = solver.simulate_with_v_profile(t_eval=t_eval, v_profile=v_profile)

    # delta(10) deve ser 10 * 2 = 20 µm
    assert np.isclose(res["delta"][-1], 20.0, atol=1e-3), f"delta final esperado 20, obtido: {res['delta'][-1]}"
    assert 0.0 < res["XZn"][-1] < 1.0
    print(f"  [OK] Simulação por perfil de velocidade validada: delta(10 min) = {res['delta'][-1]:.2f} µm.")
