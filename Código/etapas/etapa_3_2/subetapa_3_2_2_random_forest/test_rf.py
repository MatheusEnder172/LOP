"""Testes unitários automatizados para o modelo KineticsRandomForest (Subetapa 3.2.2).

Verifica integridade dimensional, restrições físicas de não-negatividade (|v| >= 0),
consistência de importância de atributos, reproducibilidade estocástica e
serialização/carregamento de checkpoints (.joblib e .json).
"""

import sys
from pathlib import Path
import numpy as np
import pytest

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parent.parent.parent
sys.path.insert(0, str(SUBETAPA_DIR))
sys.path.insert(0, str(CODIGO_DIR))

from modelo_rf import KineticsRandomForest



@pytest.fixture
def synthetic_data():
    """Gera dados sintéticos com 100 amostras e 4 features físicas."""
    rng = np.random.default_rng(42)
    # Features: [temperatura_C, CA0_mol_L, razao_molar_eta, t_min]
    X = np.column_stack([
        np.full(100, 40.0),                     # T constante
        rng.uniform(0.1, 1.5, size=100),         # CA0
        rng.choice([0.5, 1.0, 1.5, 3.1], size=100), # eta
        rng.uniform(0.0, 15.0, size=100),        # t
    ])
    # Alvo com forte assimetria e picos iniciais (µm/min)
    y = 500.0 * np.exp(-1.5 * X[:, 3]) + 50.0 * np.exp(-0.2 * X[:, 3]) + rng.uniform(0.01, 1.0, size=100)
    return X, y


def test_rf_forward_pass_dimensions(synthetic_data):
    """Verifica se o modelo aceita matrizes 2D e retorna predições 1D com shape (N,)."""
    X, y = synthetic_data
    rf = KineticsRandomForest(n_estimators=20, max_depth=5, random_state=42)
    rf.fit(X, y)

    y_pred = rf.predict(X)
    y_pred_log = rf.predict_log(X)

    assert y_pred.shape == (len(X),)
    assert y_pred_log.shape == (len(X),)
    assert isinstance(y_pred, np.ndarray)
    assert np.all(np.isfinite(y_pred))


def test_rf_physical_non_negativity_constraint(synthetic_data):
    """Verifica a Restrição Inegociável: taxa de retração interfacial estritamente não-negativa (|v| >= 0)."""
    X, y = synthetic_data
    rf = KineticsRandomForest(n_estimators=20, max_depth=5, random_state=42)
    rf.fit(X, y)

    # Teste no conjunto de treinamento
    pred_train = rf.predict(X)
    assert np.all(pred_train >= 0.0), "Predições de treino violaram a não-negatividade (|v| < 0)!"

    # Teste sob entradas extremas e extrapoladas (espaço fora do domínio)
    X_extreme = np.array([
        [-50.0, -2.0, -1.0, -10.0],
        [100.0, 10.0, 10.0, 100.0],
        [0.0, 0.0, 0.0, 0.0],
        [40.0, 5.0, 0.2, 50.0],
    ])
    pred_extreme = rf.predict(X_extreme)
    assert np.all(pred_extreme >= 0.0), "Predições sob condições extremas violaram a não-negatividade!"


def test_rf_feature_importances(synthetic_data):
    """Verifica se o vetor de importância de atributos possui 4 elementos e soma 1.0."""
    X, y = synthetic_data
    rf = KineticsRandomForest(n_estimators=30, max_depth=6, random_state=42)
    rf.fit(X, y)

    importances = rf.feature_importances_
    assert len(importances) == 4
    assert np.all(importances >= 0.0)
    assert np.isclose(np.sum(importances), 1.0, atol=1e-5)
    # Como t_min governa o decaimento exponencial sintético, sua importância deve ser positiva
    assert importances[3] > 0.0


def test_rf_reproducibility(synthetic_data):
    """Verifica que a mesma semente aleatória produz predições exatamente idênticas."""
    X, y = synthetic_data
    rf1 = KineticsRandomForest(n_estimators=25, max_depth=5, random_state=123)
    rf2 = KineticsRandomForest(n_estimators=25, max_depth=5, random_state=123)

    rf1.fit(X, y)
    rf2.fit(X, y)

    np.testing.assert_allclose(rf1.predict(X), rf2.predict(X), atol=1e-12)


def test_rf_save_load_checkpoint(synthetic_data, tmp_path):
    """Verifica persistência (.joblib e .json) e exata reprodução de inferência pós-carregamento."""
    X, y = synthetic_data
    rf = KineticsRandomForest(n_estimators=20, max_depth=5, random_state=42)
    rf.fit(X, y)
    y_pred_original = rf.predict(X)

    model_path = tmp_path / "rf_test.joblib"
    config_path = tmp_path / "rf_config.json"
    rf.save(model_path, config_path)

    assert model_path.exists()
    assert config_path.exists()

    loaded_rf = KineticsRandomForest.load(model_path)
    y_pred_loaded = loaded_rf.predict(X)

    np.testing.assert_allclose(y_pred_original, y_pred_loaded, atol=1e-12)
    assert loaded_rf.is_fitted is True


def test_rf_linear_vs_log1p_modes(synthetic_data):
    """Verifica se ambos os modos de transformação de alvo (linear e log1p) funcionam e respeitam |v| >= 0."""
    X, y = synthetic_data
    rf_log = KineticsRandomForest(n_estimators=15, target_transform="log1p", random_state=42)
    rf_lin = KineticsRandomForest(n_estimators=15, target_transform="linear", random_state=42)

    rf_log.fit(X, y)
    rf_lin.fit(X, y)

    pred_log = rf_log.predict(X)
    pred_lin = rf_lin.predict(X)

    assert np.all(pred_log >= 0.0)
    assert np.all(pred_lin >= 0.0)
