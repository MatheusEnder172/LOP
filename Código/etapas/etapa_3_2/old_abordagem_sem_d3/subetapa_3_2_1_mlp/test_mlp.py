"""Testes Unitários Automatizados para o Modelo MLP (Subetapa 3.2.1).

Verifica:
1. Dimensões corretas dos tensores nas Arquiteturas B (3 camadas) e C (5 camadas).
2. Garantia física estrita de não-negatividade (|v(t)| >= 0) sob entradas extremas.
3. Fluxo de gradientes e convergência em todas as camadas ocultas.
4. Determinismo e reproducibilidade com semente fixa.
5. Serialização e recarga de pesos (.pt).
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

# Adicionar caminhos ao sys.path
SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parent.parent.parent
sys.path.insert(0, str(SUBETAPA_DIR))
sys.path.insert(0, str(CODIGO_DIR))

from modelo_mlp import KineticsMLP, MLPTrainer, set_seed


def test_forward_pass_dimensions() -> None:
    """Verifica dimensões de saída para as Arquiteturas B e C."""
    batch_size = 16
    x = torch.randn(batch_size, 4)

    # Arquitetura B (3 camadas)
    mlp_b = KineticsMLP(input_dim=4, hidden_dims=[128, 64, 32])
    out_b = mlp_b(x)
    assert out_b.shape == (batch_size, 1), f"Shape incorreto para MLP-B: {out_b.shape}"

    # Arquitetura C (5 camadas)
    mlp_c = KineticsMLP(input_dim=4, hidden_dims=[256, 128, 64, 32, 16])
    out_c = mlp_c(x)
    assert out_c.shape == (batch_size, 1), f"Shape incorreto para MLP-C: {out_c.shape}"


def test_physical_non_negativity_constraint() -> None:
    """Valida que |v(t)| >= 0 para entradas aleatórias e condições extremas."""
    mlp = KineticsMLP(input_dim=4, hidden_dims=[128, 64, 32])

    # 1. Entradas aleatórias uniformes
    x_rand = torch.randn(100, 4)
    pred_rand = mlp(x_rand)
    assert (pred_rand >= 0.0).all().item(), "Violação física: predição negativa encontrada!"

    # 2. Entradas extremas negativas (simulando extrapoladores extremos)
    x_neg = torch.full((20, 4), -100.0)
    pred_neg = mlp(x_neg)
    assert (pred_neg >= 0.0).all().item(), "Violação física sob entrada negativa extrema!"

    # 3. Entradas extremas positivas
    x_pos = torch.full((20, 4), 100.0)
    pred_pos = mlp(x_pos)
    assert (pred_pos >= 0.0).all().item(), "Violação física sob entrada positiva extrema!"


def test_gradient_flow_and_convergence() -> None:
    """Verifica se os gradientes fluem por todas as camadas e a loss decresce."""
    set_seed(42)
    mlp = KineticsMLP(input_dim=4, hidden_dims=[128, 64, 32], dropout_rate=0.0)
    optimizer = torch.optim.Adam(mlp.parameters(), lr=1e-2)
    criterion = torch.nn.SmoothL1Loss()

    # Mini-batch sintético
    x_dummy = torch.randn(32, 4)
    y_dummy = torch.abs(torch.randn(32, 1)) * 50.0

    initial_loss = float(criterion(mlp(x_dummy), y_dummy).item())

    # 15 passos de otimização
    for _ in range(15):
        optimizer.zero_grad()
        loss = criterion(mlp(x_dummy), y_dummy)
        loss.backward()
        optimizer.step()

    final_loss = float(criterion(mlp(x_dummy), y_dummy).item())
    assert final_loss < initial_loss, f"Loss não decresceu: inicial {initial_loss}, final {final_loss}"

    # Verificar que todas as camadas lineares receberam gradientes
    for name, param in mlp.named_parameters():
        if "weight" in name and param.requires_grad:
            assert param.grad is not None, f"Gradiente ausente em {name}"
            assert torch.norm(param.grad).item() > 0.0, f"Gradiente nulo em {name}"


def test_reproducibility() -> None:
    """Verifica que sementes fixas geram exatamente as mesmas predições."""
    x = torch.randn(10, 4)

    set_seed(123)
    mlp1 = KineticsMLP(input_dim=4, hidden_dims=[64, 32])
    out1 = mlp1(x).detach().numpy()

    set_seed(123)
    mlp2 = KineticsMLP(input_dim=4, hidden_dims=[64, 32])
    out2 = mlp2(x).detach().numpy()

    np.testing.assert_allclose(out1, out2, atol=1e-6, err_msg="Determinismo violado com mesma semente!")


def test_save_load_checkpoint() -> None:
    """Verifica se o salvamento e recarga do state_dict preservam predições exatas."""
    mlp = KineticsMLP(input_dim=4, hidden_dims=[128, 64, 32])
    mlp.eval()
    x = torch.randn(8, 4)
    pred_orig = mlp(x).detach().numpy()

    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        torch.save(mlp.state_dict(), tmp_path)

        mlp_loaded = KineticsMLP(input_dim=4, hidden_dims=[128, 64, 32])
        mlp_loaded.load_state_dict(torch.load(tmp_path, weights_only=True))
        mlp_loaded.eval()

        pred_loaded = mlp_loaded(x).detach().numpy()
        np.testing.assert_allclose(pred_orig, pred_loaded, atol=1e-6)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
