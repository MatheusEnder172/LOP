"""Testes unitários automatizados para o modelo KineticsXGBoost (Subetapa 3.2.4).

Verifica integridade dimensional, restrições físicas de não-negatividade (|v| >= 0),
importâncias de atributos (Ganho), reproducibilidade estocástica e
serialização/carregamento de checkpoints (.json e .joblib).
"""

import sys
from pathlib import Path
import numpy as np
import pytest

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parent.parent.parent
sys.path.insert(0, str(SUBETAPA_DIR))
sys.path.insert(0, str(CODIGO_DIR))

from modelo_xgb import KineticsXGBoost


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
    # Alvo com decaimento exponencial
    y = 450.0 * np.exp(-1.4 * X[:, 3]) + 45.0 * np.exp(-0.18 * X[:, 3]) + rng.uniform(0.01, 0.8, size=100)
    return X, y


def test_xgb_forward_pass_dimensions(synthetic_data):
    """Verifica se o modelo aceita matrizes 2D e retorna predições 1D com shape (N,)."""
    X, y = synthetic_data
    xgb_model = KineticsXGBoost(n_estimators=25, max_depth=4, random_state=42)
    xgb_model.fit(X, y)

    y_pred = xgb_model.predict(X)
    y_pred_log = xgb_model.predict_log(X)

    assert y_pred.shape == (len(X),)
    assert y_pred_log.shape == (len(X),)
    assert isinstance(y_pred, np.ndarray)
    assert np.all(np.isfinite(y_pred))


def test_xgb_physical_non_negativity_constraint(synthetic_data):
    """Verifica a Restrição Inegociável: taxa de retração interfacial estritamente não-negativa (|v| >= 0)."""
    X, y = synthetic_data
    xgb_model = KineticsXGBoost(n_estimators=25, max_depth=4, random_state=42)
    xgb_model.fit(X, y)

    # Teste no conjunto de treino
    pred_train = xgb_model.predict(X)
    assert np.all(pred_train >= 0.0), "Predições de treino violaram a não-negatividade (|v| < 0)!"

    # Teste sob entradas extremas e extrapoladas
    X_extreme = np.array([
        [-50.0, -2.0, -1.0, -10.0],
        [100.0, 10.0, 10.0, 100.0],
        [0.0, 0.0, 0.0, 0.0],
        [40.0, 5.0, 0.2, 50.0],
    ])
    pred_extreme = xgb_model.predict(X_extreme)
    assert np.all(pred_extreme >= 0.0), "Predições sob condições extremas violaram a não-negatividade!"


def test_xgb_feature_importances(synthetic_data):
    """Verifica se o vetor de importância de atributos possui 4 elementos e soma 1.0."""
    X, y = synthetic_data
    xgb_model = KineticsXGBoost(n_estimators=30, max_depth=4, random_state=42)
    xgb_model.fit(X, y)

    importances = xgb_model.feature_importances_
    assert len(importances) == 4
    assert np.all(importances >= 0.0)
    assert np.isclose(np.sum(importances), 1.0, atol=1e-5)
    # t_min deve ter alta importância no decaimento cinético
    assert importances[3] > 0.0


def test_xgb_reproducibility(synthetic_data):
    """Verifica que a mesma semente aleatória produz predições exatamente idênticas."""
    X, y = synthetic_data
    xgb1 = KineticsXGBoost(n_estimators=25, max_depth=4, random_state=123)
    xgb2 = KineticsXGBoost(n_estimators=25, max_depth=4, random_state=123)

    xgb1.fit(X, y)
    xgb2.fit(X, y)

    np.testing.assert_allclose(xgb1.predict(X), xgb2.predict(X), atol=1e-6)


def test_xgb_save_load_checkpoint(synthetic_data, tmp_path):
    """Verifica persistência (.joblib e .json) e exata reprodução de inferência pós-carregamento."""
    X, y = synthetic_data
    xgb_model = KineticsXGBoost(n_estimators=20, max_depth=4, random_state=42)
    xgb_model.fit(X, y)
    y_pred_original = xgb_model.predict(X)

    # Teste de salvamento em .joblib
    model_path = tmp_path / "xgb_test.joblib"
    config_path = tmp_path / "xgb_config.json"
    xgb_model.save(model_path, config_path)

    assert model_path.exists()
    assert config_path.exists()

    loaded_xgb = KineticsXGBoost.load(model_path)
    y_pred_loaded = loaded_xgb.predict(X)

    np.testing.assert_allclose(y_pred_original, y_pred_loaded, atol=1e-6)
    assert loaded_xgb.is_fitted is True

    # Teste de salvamento em .json nativo do XGBoost
    json_model_path = tmp_path / "xgb_model.json"
    xgb_model.save(json_model_path, config_path)
    assert json_model_path.exists()

    loaded_xgb_json = KineticsXGBoost.load(json_model_path, config_path)
    y_pred_json = loaded_xgb_json.predict(X)
    np.testing.assert_allclose(y_pred_original, y_pred_json, atol=1e-6)


def test_xgb_linear_vs_log1p_modes(synthetic_data):
    """Verifica se ambos os modos de transformação de alvo (linear e log1p) funcionam e respeitam |v| >= 0."""
    X, y = synthetic_data
    xgb_log = KineticsXGBoost(n_estimators=15, target_transform="log1p", random_state=42)
    xgb_lin = KineticsXGBoost(n_estimators=15, target_transform="linear", random_state=42)

    xgb_log.fit(X, y)
    xgb_lin.fit(X, y)

    pred_log = xgb_log.predict(X)
    pred_lin = xgb_lin.predict(X)

    assert np.all(pred_log >= 0.0)
    assert np.all(pred_lin >= 0.0)
