"""Testes Unitários Automatizados para o Modelo MLP Evoluído (Subetapa 3.2.1 — Opção 1 + Autograd).

Verifica:
1. Dimensões corretas dos tensores (input_dim = 3: [CA0_mol_L, razao_molar_eta, t_min]) nas Arquiteturas Padrão e ResNet-MLP.
2. Garantia física estrita de não-negatividade (|v(t)| >= 0) sob entradas extremas.
3. Fluxo de gradientes e convergência em camadas ocultas e blocos residuais.
4. Extração de derivadas parciais analíticas exatas via torch.autograd (∂|v|/∂C_A0, ∂|v|/∂η, ∂|v|/∂t).
5. Determinismo, reprodutibilidade e serialização de pesos (.pt).
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parent.parent.parent
sys.path.insert(0, str(SUBETAPA_DIR))
sys.path.insert(0, str(CODIGO_DIR))

from modelo_mlp import KineticsMLP, MLPTrainer, set_seed


def test_forward_pass_dimensions_and_residual() -> None:
    """Verifica dimensões de saída para input_dim=3 em MLP padrão e ResNet-MLP."""
    batch_size = 16
    x = torch.randn(batch_size, 3)

    mlp_b = KineticsMLP(input_dim=3, hidden_dims=[64, 32], activation="GELU", use_residual=False)
    out_b = mlp_b(x)
    assert out_b.shape == (batch_size, 1), f"Shape incorreto para MLP-B: {out_b.shape}"

    mlp_res = KineticsMLP(input_dim=3, hidden_dims=[64, 64, 32], activation="SiLU", use_residual=True)
    out_res = mlp_res(x)
    assert out_res.shape == (batch_size, 1), f"Shape incorreto para ResNet-MLP: {out_res.shape}"


def test_physical_non_negativity_constraint() -> None:
    """Valida que |v(t)| >= 0 para entradas aleatórias e condições extremas."""
    mlp = KineticsMLP(input_dim=3, hidden_dims=[64, 32], use_residual=True)

    x_rand = torch.randn(100, 3)
    assert (mlp(x_rand) >= 0.0).all().item()

    x_neg = torch.full((20, 3), -100.0)
    assert (mlp(x_neg) >= 0.0).all().item()

    x_pos = torch.full((20, 3), 100.0)
    assert (mlp(x_pos) >= 0.0).all().item()


def test_gradient_flow_and_convergence() -> None:
    """Verifica se os gradientes fluem por todas as camadas e a loss decresce."""
    set_seed(42)
    mlp = KineticsMLP(input_dim=3, hidden_dims=[64, 32], dropout_rate=0.0, use_residual=True)
    optimizer = torch.optim.Adam(mlp.parameters(), lr=1e-2)
    criterion = torch.nn.SmoothL1Loss()

    x_dummy = torch.randn(32, 3)
    y_dummy = torch.abs(torch.randn(32, 1)) * 25.0

    initial_loss = float(criterion(mlp(x_dummy), y_dummy).item())
    for _ in range(15):
        optimizer.zero_grad()
        loss = criterion(mlp(x_dummy), y_dummy)
        loss.backward()
        optimizer.step()

    final_loss = float(criterion(mlp(x_dummy), y_dummy).item())
    assert final_loss < initial_loss, f"Loss não decresceu: inicial {initial_loss}, final {final_loss}"


def test_autograd_analytical_sensitivities() -> None:
    """Valida a extração de derivadas parciais ∂|v|/∂C_A0, ∂|v|/∂η e ∂|v|/∂t via autograd."""
    set_seed(42)
    mlp = KineticsMLP(input_dim=3, hidden_dims=[64, 32], activation="GELU")
    x_scaled = np.random.randn(12, 3)
    scales = np.array([0.55, 0.98, 4.33])

    sens = mlp.compute_sensitivities_autograd(x_scaled, scales)
    assert sens["abs_v"].shape == (12,)
    assert sens["dv_dCA0"].shape == (12,)
    assert sens["dv_deta"].shape == (12,)
    assert sens["dv_dt"].shape == (12,)
    assert np.all(np.isfinite(sens["dv_dt"]))


def test_reproducibility_and_checkpoint() -> None:
    """Verifica determinismo e serialização/recarga do state_dict."""
    x = torch.randn(10, 3)

    set_seed(123)
    mlp1 = KineticsMLP(input_dim=3, hidden_dims=[64, 32])
    out1 = mlp1(x).detach().numpy()

    set_seed(123)
    mlp2 = KineticsMLP(input_dim=3, hidden_dims=[64, 32])
    out2 = mlp2(x).detach().numpy()

    np.testing.assert_allclose(out1, out2, atol=1e-6)

    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        torch.save(mlp1.state_dict(), tmp_path)
        mlp_loaded = KineticsMLP(input_dim=3, hidden_dims=[64, 32])
        mlp_loaded.load_state_dict(torch.load(tmp_path, weights_only=True))
        mlp_loaded.eval()
        pred_loaded = mlp_loaded(x).detach().numpy()
        np.testing.assert_allclose(out1, pred_loaded, atol=1e-6)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
