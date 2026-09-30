"""
Suíte de Testes Unitários e Validação Numérica do Resolvedor PBM Batelada.
Testa o módulo `src/physics/pbm_batch.py` e a classe `BatchPBMSolver`.
"""

import sys
from pathlib import Path
import numpy as np

# Adicionar a pasta raiz de código ao path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.physics.granulometry import RosinRammlerBennet
from src.physics.kinetics import LeachingKinetics
from src.physics.pbm_batch import BatchPBMSolver


def test_monotonicity_and_bounds_conversion():
    """Testa se X_Zn(delta) é estritamente monótona crescente e limitada no intervalo [0, 1]."""
    solver = BatchPBMSolver()

    delta_test = np.linspace(0.0, 300.0, 100)
    x_test = solver.compute_conversion_from_delta(delta_test)

    # Limites físicos
    assert np.isclose(x_test[0], 0.0, atol=1e-5), f"X_Zn(0) deve ser 0, obtido: {x_test[0]}"
    assert np.all(x_test >= 0.0), "X_Zn não pode ser negativo."
    assert np.all(x_test <= 1.0), "X_Zn não pode exceder 1,0."
    assert np.isclose(x_test[-1], 1.0, atol=1e-3), f"X_Zn(Dmax) deve ser 1, obtido: {x_test[-1]}"

    # Monotonicidade: dX/d(delta) >= 0
    diffs = np.diff(x_test)
    assert np.all(diffs >= -1e-8), "X_Zn(delta) deve ser monótona não-decrescente."
    print("  [OK] Monotonicidade e limites [0, 1] da conversão aprovados.")


def test_theoretical_stopping_equilibrium():
    """Testa se a simulação com solver EDO converge exatamente para o limite analítico de parada."""
    kin = LeachingKinetics(alpha_nominal=5500.0, ks=18000.0)
    solver = BatchPBMSolver(kinetics=kin)

    ca0 = 0.50
    eta = 1.0
    t_eval = np.array([0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 30.0])

    res = solver.simulate(ca0=ca0, eta=eta, t_eval=t_eval)

    assert res["success"], f"Solver EDO falhou: {res['message']}"

    # Limite analítico esperado: X_max = eta * [1 - alpha / (ks + alpha)] = 1.0 * [1 - 5500/23500] = 0.7660
    x_theoretical_max = kin.theoretical_max_conversion(eta=eta)
    caf_stopping = kin.dissolution_stopping_acid(ca0=ca0)

    x_final_sim = res["XZn"][-1]
    caf_final_sim = res["CAf"][-1]

    assert np.isclose(
        x_final_sim, x_theoretical_max, atol=1e-3
    ), f"Conversão assintótica diverge do teórico: {x_final_sim:.4f} vs {x_theoretical_max:.4f}"

    assert np.isclose(
        caf_final_sim, caf_stopping, atol=1e-3
    ), f"Acidez final diverge da acidez crítica: {caf_final_sim:.4f} vs {caf_stopping:.4f}"

    print(f"  [OK] Limite assintótico validado: X_final = {x_final_sim:.4f} (Teórico: {x_theoretical_max:.4f}), CAf = {caf_final_sim:.4f} mol/L.")


def test_excess_acid_complete_conversion():
    """Testa se com excesso estequiométrico alto (eta=3.1) o modelo atinge conversão completa."""
    kin = LeachingKinetics(alpha_nominal=5500.0, ks=18000.0)
    solver = BatchPBMSolver(kinetics=kin)

    ca0 = 1.00
    eta = 3.1
    t_eval = np.array([0.0, 0.5, 1.0, 2.0, 5.0, 15.0])

    res = solver.simulate(ca0=ca0, eta=eta, t_eval=t_eval)

    assert res["success"]
    assert np.isclose(res["XZn"][-1], 1.0, atol=1e-2), f"Deveria converter 100%, obtido: {res['XZn'][-1]}"
    print(f"  [OK] Conversão completa sob excesso de ácido: X_final = {res['XZn'][-1]:.4f}.")


def test_simulate_with_v_profile():
    """Testa o método de acoplamento com perfil de velocidade arbitrário."""
    solver = BatchPBMSolver()

    t_eval = np.linspace(0.0, 10.0, 11)
    # Perfil constante v = -10 µm/min
    v_profile = np.full_like(t_eval, -10.0)

    res = solver.simulate_with_v_profile(t_eval=t_eval, v_profile=v_profile)

    # delta(10) deve ser 10 * 10 = 100 µm
    assert np.isclose(res["delta"][-1], 100.0, atol=1e-3), f"delta final esperado 100, obtido: {res['delta'][-1]}"
    assert 0.0 < res["XZn"][-1] < 1.0
    print(f"  [OK] Simulação por perfil de velocidade validada: delta(10 min) = {res['delta'][-1]:.2f} µm.")


if __name__ == "__main__":
    print("\nIniciando suíte de testes unitários do BatchPBMSolver...")
    test_monotonicity_and_bounds_conversion()
    test_theoretical_stopping_equilibrium()
    test_excess_acid_complete_conversion()
    test_simulate_with_v_profile()
    print("\nTodos os testes unitários do BatchPBMSolver foram APROVADOS com sucesso!\n")
