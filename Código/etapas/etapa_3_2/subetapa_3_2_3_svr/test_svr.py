"""Testes unitários automatizados para o modelo KineticsSVR (Subetapa 3.2.3).

Verifica integridade dimensional, restrições físicas de não-negatividade (|v| >= 0),
propriedades dos vetores de suporte, suporte a StandardScaler integrado e
serialização/carregamento de checkpoints (.joblib e .json).
"""

import sys
from pathlib import Path
import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parent.parent.parent
sys.path.insert(0, str(SUBETAPA_DIR))
sys.path.insert(0, str(CODIGO_DIR))

from modelo_svr import KineticsSVR


@pytest.fixture
def synthetic_data():
    """Gera dados sintéticos com 100 amostras e 4 features físicas."""
    rng = np.random.default_rng(42)
    # Features: [temperatura_C, CA0_mol_L, razao_molar_eta, t_min]
    X = np.column_stack([
        np.full(100, 40.0),                         # T constante
        rng.uniform(0.1, 1.5, size=100),             # CA0
        rng.choice([0.5, 1.0, 1.5, 3.1], size=100),     # eta
        rng.uniform(0.0, 15.0, size=100),            # t
    ])
    # Alvo com decaimento exponencial acentuado
    y = 400.0 * np.exp(-1.2 * X[:, 3]) + 40.0 * np.exp(-0.15 * X[:, 3]) + rng.uniform(0.01, 0.5, size=100)
    return X, y


def test_svr_forward_pass_dimensions(synthetic_data):
    """Verifica se o SVR aceita matrizes 2D e retorna predições 1D com shape (N,)."""
    X, y = synthetic_data
    scaler = StandardScaler().fit(X)
    X_s = scaler.transform(X)

    svr = KineticsSVR(C=10.0, epsilon=0.05)
    svr.fit(X_s, y)

    y_pred = svr.predict(X_s)
    y_pred_log = svr.predict_log(X_s)

    assert y_pred.shape == (len(X),)
    assert y_pred_log.shape == (len(X),)
    assert isinstance(y_pred, np.ndarray)
    assert np.all(np.isfinite(y_pred))


def test_svr_physical_non_negativity_constraint(synthetic_data):
    """Verifica a Restrição Inegociável: taxa de retração interfacial estritamente não-negativa (|v| >= 0)."""
    X, y = synthetic_data
    scaler = StandardScaler().fit(X)
    X_s = scaler.transform(X)

    svr = KineticsSVR(C=10.0, epsilon=0.05)
    svr.fit(X_s, y)

    # Teste no conjunto de treino
    pred_train = svr.predict(X_s)
    assert np.all(pred_train >= 0.0), "Predições de treino violaram a não-negatividade (|v| < 0)!"

    # Teste sob entradas extremas e extrapoladas
    X_extreme = np.array([
        [-100.0, -10.0, -5.0, -50.0],
        [100.0, 50.0, 20.0, 200.0],
        [0.0, 0.0, 0.0, 0.0],
        [-5.0, 1.0, 1.0, 1.0],
    ])
    pred_extreme = svr.predict(X_extreme)
    assert np.all(pred_extreme >= 0.0), "Predições sob condições extremas violaram a não-negatividade!"


def test_svr_support_vectors_properties(synthetic_data):
    """Verifica que o número de vetores de suporte é plausível e que a esparsidade é respeitada."""
    X, y = synthetic_data
    scaler = StandardScaler().fit(X)
    X_s = scaler.transform(X)

    svr = KineticsSVR(C=10.0, epsilon=0.1)
    svr.fit(X_s, y)

    n_sv = svr.n_support_
    ratio = svr.support_ratio_

    assert n_sv > 0, "O modelo não encontrou nenhum vetor de suporte."
    assert n_sv <= len(X), "O número de vetores de suporte não pode exceder o total de amostras."
    assert 0.0 < ratio <= 1.0, "A razão de vetores de suporte deve estar entre 0 e 1."


def test_svr_save_load_checkpoint(synthetic_data, tmp_path):
    """Verifica persistência (.joblib e .json) e exata reprodução de inferência pós-carregamento."""
    X, y = synthetic_data
    scaler = StandardScaler().fit(X)
    X_s = scaler.transform(X)

    svr = KineticsSVR(C=15.0, epsilon=0.05)
    svr.fit(X_s, y)
    y_pred_original = svr.predict(X_s)

    model_path = tmp_path / "svr_test.joblib"
    config_path = tmp_path / "svr_config.json"
    svr.save(model_path, config_path)

    assert model_path.exists()
    assert config_path.exists()

    loaded_svr = KineticsSVR.load(model_path)
    y_pred_loaded = loaded_svr.predict(X_s)

    np.testing.assert_allclose(y_pred_original, y_pred_loaded, atol=1e-12)
    assert loaded_svr.is_fitted is True


def test_svr_with_integrated_scaler(synthetic_data):
    """Verifica se o SVR funciona com scaler_X integrado recebendo dados brutos."""
    X, y = synthetic_data
    scaler = StandardScaler().fit(X)

    svr = KineticsSVR(C=10.0, epsilon=0.05, scaler_X=scaler)
    svr.fit(X, y)

    y_pred = svr.predict(X)
    assert len(y_pred) == len(X)
    assert np.all(y_pred >= 0.0)


def test_svr_linear_vs_log1p_modes(synthetic_data):
    """Verifica se ambos os modos de transformação de alvo (linear e log1p) funcionam e respeitam |v| >= 0."""
    X, y = synthetic_data
    scaler = StandardScaler().fit(X)
    X_s = scaler.transform(X)

    svr_log = KineticsSVR(C=10.0, epsilon=0.05, target_transform="log1p")
    svr_lin = KineticsSVR(C=10.0, epsilon=1.0, target_transform="linear")

    svr_log.fit(X_s, y)
    svr_lin.fit(X_s, y)

    pred_log = svr_log.predict(X_s)
    pred_lin = svr_lin.predict(X_s)

    assert np.all(pred_log >= 0.0)
    assert np.all(pred_lin >= 0.0)
