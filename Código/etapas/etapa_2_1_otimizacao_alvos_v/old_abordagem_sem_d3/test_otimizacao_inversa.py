"""
Testes Unitários Automatizados da Etapa 2.1: Otimização Inversa e Geração de Alvos v(t).

Valida:
1. Integridade dos arquivos de saída gerados (dimensões e colunas).
2. Restrições físicas inegociáveis:
   - v(t) <= 0 (velocidade de retração estritamente negativa ou nula).
   - delta(t) >= 0 e monotonicamente não-decrescente.
   - X_Zn_reconstruido in [0, 1].
3. Critérios de qualidade e aderência do ajuste inverso:
   - R² > 0.985 para todos os 16 ensaios individuais.
   - R² global > 0.998.
   - RMSE global < 0.015.
4. Consistência matemática da formulação analítica bi-exponencial.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT.parent / "Base de dados" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "etapa_2_1"


@pytest.fixture(scope="module")
def targets_df() -> pd.DataFrame:
    """Carrega o dataset de alvos nos tempos experimentais."""
    file_path = DATA_DIR / "alvos_v_treinamento.csv"
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    return pd.read_csv(file_path)


@pytest.fixture(scope="module")
def dense_df() -> pd.DataFrame:
    """Carrega o dataset denso de alvos."""
    file_path = DATA_DIR / "alvos_v_treinamento_denso.csv"
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    return pd.read_csv(file_path)


@pytest.fixture(scope="module")
def params_df() -> pd.DataFrame:
    """Carrega os parâmetros ótimos por ensaio."""
    file_path = DATA_DIR / "parametros_otimizacao_inversa.csv"
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    return pd.read_csv(file_path)


def test_file_structure_and_dimensions(
    targets_df: pd.DataFrame,
    dense_df: pd.DataFrame,
    params_df: pd.DataFrame,
) -> None:
    """Verifica formato, dimensões e colunas essenciais dos datasets gerados."""
    # 16 ensaios x 8 pontos experimentais = 128 registros
    assert len(targets_df) == 128, f"Esperado 128 registros, obtido {len(targets_df)}"
    # 16 ensaios x 61 nós temporais = 976 registros
    assert len(dense_df) == 976, f"Esperado 976 registros, obtido {len(dense_df)}"
    # 16 ensaios
    assert len(params_df) == 16, f"Esperado 16 parâmetros, obtido {len(params_df)}"

    required_cols = [
        "ensaio",
        "temperatura_C",
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

    assert "v_alvo_um_min" in dense_df.columns
    assert "delta_alvo_um" in dense_df.columns
    assert "R2" in params_df.columns


def test_physical_constraints(targets_df: pd.DataFrame, dense_df: pd.DataFrame) -> None:
    """Verifica o cumprimento estrito das leis de conservação física."""
    # 1. Velocidade interfacial deve ser não-positiva (retração / dissolução)
    assert np.all(targets_df["v_alvo_um_min"] <= 1e-9), "Encontrada velocidade positiva em alvos experimentais!"
    assert np.all(dense_df["v_alvo_um_min"] <= 1e-9), "Encontrada velocidade positiva em dataset denso!"

    # 2. Deslocamento acumulado delta(t) deve ser não-negativo
    assert np.all(targets_df["delta_alvo_um"] >= -1e-9), "Encontrado delta negativo em alvos experimentais!"
    assert np.all(dense_df["delta_alvo_um"] >= -1e-9), "Encontrado delta negativo em dataset denso!"

    # 3. Monotonicidade de delta(t) para cada ensaio
    for ensaio, group in dense_df.groupby("ensaio"):
        deltas = group["delta_alvo_um"].values
        diffs = np.diff(deltas)
        assert np.all(diffs >= -1e-8), f"Delta decrescente detectado no ensaio {ensaio}!"

    # 4. Conversão de zinco restrita ao intervalo físico [0, 1]
    assert np.all(targets_df["XZn_reconstruido"] >= -1e-6), "X_Zn reconstruído menor que zero!"
    assert np.all(targets_df["XZn_reconstruido"] <= 1.0 + 1e-6), "X_Zn reconstruído maior que um!"


def test_reconstruction_accuracy(targets_df: pd.DataFrame, params_df: pd.DataFrame) -> None:
    """Valida a precisão da reconstrução inversa frente aos dados experimentais reais."""
    # 1. Critério individual: R² > 0.985 para cada um dos 16 ensaios
    min_r2 = params_df["R2"].min()
    assert min_r2 >= 0.985, f"R² mínimo ({min_r2:.5f}) abaixo do piso de 0.985!"

    # 2. Métricas globais sobre os 128 pontos experimentais
    y_true = targets_df["XZn_exp"].values
    y_pred = targets_df["XZn_reconstruido"].values

    r2_global = r2_score(y_true, y_pred)
    rmse_global = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae_global = float(mean_absolute_error(y_true, y_pred))

    assert r2_global >= 0.998, f"R² global ({r2_global:.5f}) inferior a 0.998!"
    assert rmse_global <= 0.015, f"RMSE global ({rmse_global:.5f}) superior a 0.015 (1.5%)!"
    assert mae_global <= 0.010, f"MAE global ({mae_global:.5f}) superior a 0.010 (1.0%)!"


def test_analytical_consistency(params_df: pd.DataFrame, targets_df: pd.DataFrame) -> None:
    """Verifica se os valores de delta e v batem analiticamente com os parâmetros ótimos."""
    for _, row in params_df.iterrows():
        ensaio = int(row["ensaio"])
        a1, b1, a2, b2, c = row["a1"], row["b1"], row["a2"], row["b2"], row["c"]

        sub_df = targets_df[targets_df["ensaio"] == ensaio]
        t = sub_df["t_min"].values

        # Fórmula analítica
        delta_calc = (
            (a1 / b1) * (1.0 - np.exp(-b1 * t))
            + (a2 / b2) * (1.0 - np.exp(-b2 * t))
            + c * t
        )
        v_calc = -(a1 * np.exp(-b1 * t) + a2 * np.exp(-b2 * t) + c)

        # Comparação com tolerância compatível com as 4 casas decimais salvas no CSV de parâmetros
        np.testing.assert_allclose(
            sub_df["delta_alvo_um"].values,
            delta_calc,
            rtol=5e-4,
            atol=0.05,
            err_msg=f"Discrepância em delta para ensaio {ensaio}",
        )
        np.testing.assert_allclose(
            sub_df["v_alvo_um_min"].values,
            v_calc,
            rtol=1e-3,
            atol=0.05,
            err_msg=f"Discrepância em v para ensaio {ensaio}",
        )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
