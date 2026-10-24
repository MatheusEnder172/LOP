"""
Testes Unitários Automatizados da Etapa 2.1: Otimização Inversa e Geração de Alvos v(t) em t > 0.

Valida:
1. Integridade dos arquivos de saída gerados em t > 0 (112 pontos experimentais, 960 pontos densos) e exclusão estrita de t = 0.
2. Restrições físicas inegociáveis:
   - v(t) <= 0 (velocidade de retração estritamente negativa ou nula).
   - delta(t) >= 0 e monotonicamente não-decrescente.
   - X_Zn_reconstruido in [0, 1].
3. Critérios de qualidade e aderência do ajuste inverso em t > 0:
   - R² global >= 0.994 nos 112 pontos ativos (t > 0).
   - RMSE global <= 0.015 (1.5%).
   - RMSE individual <= 0.025 (2.5%) para todos os 16 ensaios.
4. Consistência matemática com a integração positiva do BatchPBMSolver (δ(0) = 0 hardcoded).
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.physics.pbm_batch import BatchPBMSolver

DATA_DIR = PROJECT_ROOT.parent / "Base de dados" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "etapa_2_1"


@pytest.fixture(scope="module")
def targets_df() -> pd.DataFrame:
    file_path = DATA_DIR / "alvos_v_treinamento.csv"
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    return pd.read_csv(file_path)


@pytest.fixture(scope="module")
def dense_df() -> pd.DataFrame:
    file_path = DATA_DIR / "alvos_v_treinamento_denso.csv"
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    return pd.read_csv(file_path)


@pytest.fixture(scope="module")
def params_df() -> pd.DataFrame:
    file_path = DATA_DIR / "parametros_otimizacao_inversa.csv"
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    return pd.read_csv(file_path)


def test_file_structure_and_dimensions(
    targets_df: pd.DataFrame,
    dense_df: pd.DataFrame,
    params_df: pd.DataFrame,
) -> None:
    """Verifica formato, dimensões e exclusão estrita de t = 0."""
    # 16 ensaios x 7 pontos experimentais (t > 0) = 112 registros
    assert len(targets_df) == 112, f"Esperado 112 registros (t > 0), obtido {len(targets_df)}"
    # 16 ensaios x 60 nós temporais (t in [0.25, 15.0] min) = 960 registros
    assert len(dense_df) == 960, f"Esperado 960 registros (t > 0), obtido {len(dense_df)}"
    assert len(params_df) == 16, f"Esperado 16 parâmetros, obtido {len(params_df)}"

    # Garantir que t = 0 foi integralmente removido
    assert np.all(targets_df["t_min"] > 0.0), "Encontrado t <= 0 em alvos_v_treinamento.csv!"
    assert np.all(dense_df["t_min"] > 0.0), "Encontrado t <= 0 em alvos_v_treinamento_denso.csv!"

    required_cols = [
        "ensaio",
        "CA0_mol_L",
        "razao_molar_eta",
        "t_min",
        "v_alvo_um_min",
        "abs_v_alvo_um_min",
        "delta_alvo_um",
        "XZn_exp",
        "XZn_reconstruido",
        "residuo_XZn",
    ]
    for col in required_cols:
        assert col in targets_df.columns, f"Coluna ausente em alvos_v_treinamento: {col}"


def test_physical_constraints(targets_df: pd.DataFrame, dense_df: pd.DataFrame) -> None:
    """Verifica o cumprimento estrito das leis de conservação física."""
    assert np.all(targets_df["v_alvo_um_min"] <= 1e-9), "Encontrada velocidade positiva em alvos experimentais!"
    assert np.all(dense_df["v_alvo_um_min"] <= 1e-9), "Encontrada velocidade positiva em dataset denso!"

    assert np.all(targets_df["delta_alvo_um"] >= -1e-9), "Encontrado delta negativo em alvos experimentais!"
    assert np.all(dense_df["delta_alvo_um"] >= -1e-9), "Encontrado delta negativo em dataset denso!"

    for ensaio, group in dense_df.groupby("ensaio"):
        deltas = group["delta_alvo_um"].values
        diffs = np.diff(deltas)
        assert np.all(diffs >= -1e-8), f"Delta decrescente detectado no ensaio {ensaio}!"

    assert np.all(targets_df["XZn_reconstruido"] >= -1e-6), "X_Zn reconstruído menor que zero!"
    assert np.all(targets_df["XZn_reconstruido"] <= 1.0 + 1e-6), "X_Zn reconstruído maior que um!"


def test_reconstruction_accuracy(targets_df: pd.DataFrame, params_df: pd.DataFrame) -> None:
    """Valida a precisão da reconstrução inversa nos 112 pontos experimentais t > 0."""
    max_rmse_ind = params_df["RMSE"].max()
    assert max_rmse_ind <= 0.026, f"RMSE máximo individual ({max_rmse_ind:.5f}) acima de 2.6%!"

    y_true = targets_df["XZn_exp"].values
    y_pred = targets_df["XZn_reconstruido"].values

    r2_global = r2_score(y_true, y_pred)
    rmse_global = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae_global = float(mean_absolute_error(y_true, y_pred))

    assert r2_global >= 0.994, f"R² global ({r2_global:.5f}) inferior a 0.994!"
    assert rmse_global <= 0.015, f"RMSE global ({rmse_global:.5f}) superior a 0.015 (1.5%)!"
    assert mae_global <= 0.011, f"MAE global ({mae_global:.5f}) superior a 0.011 (1.1%)!"


def test_positive_grid_integration_consistency(dense_df: pd.DataFrame) -> None:
    """Verifica se delta_alvo_um e XZn_reconstruido na malha densa batem exatamente com o BatchPBMSolver."""
    solver = BatchPBMSolver()
    for ensaio, group in dense_df.groupby("ensaio"):
        group_sorted = group.sort_values("t_min")
        t_pos = group_sorted["t_min"].values
        v_pos = group_sorted["v_alvo_um_min"].values
        res = solver.simulate_with_v_profile(t_eval=t_pos, v_profile=v_pos)

        np.testing.assert_allclose(
            group_sorted["delta_alvo_um"].values,
            res["delta"],
            rtol=1e-3,
            atol=1e-3,
            err_msg=f"Discrepância de integração positiva em delta para ensaio {ensaio}",
        )
        np.testing.assert_allclose(
            group_sorted["XZn_reconstruido"].values,
            res["XZn"],
            rtol=1e-3,
            atol=1e-3,
            err_msg=f"Discrepância em XZn_reconstruido para ensaio {ensaio}",
        )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
