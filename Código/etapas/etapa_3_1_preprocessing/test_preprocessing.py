"""Suíte de Testes Unitários para Pré-Processamento e Partição (Etapa 3.1).

Verifica:
1. Ausência de vazamento de dados (zero data leakage) entre Treino e Teste Cego.
2. Contagem exata de amostras densas (793 treino / 183 teste) e pontuais (104 / 24).
3. Integridade do GroupKFold (nenhum ensaio compartilhado entre dobras).
4. Propriedades estatísticas do StandardScaler (ajustado estritamente no treino).
5. Exatidão da inversão de escala (X e y).
6. Serialização e restauração íntegra de scalers (.joblib).
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Garantir import de src
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ml.preprocessing import DataPartitioner, FeatureTargetScaler


@pytest.fixture
def dense_df() -> pd.DataFrame:
    """Carrega o dataset denso de alvos gerado na Etapa 2.1."""
    data_path = BASE_DIR.parent / "Base de dados" / "processed" / "alvos_v_treinamento_denso.csv"
    assert data_path.exists(), f"Arquivo não encontrado: {data_path}"
    return pd.read_csv(data_path)


@pytest.fixture
def exp_df() -> pd.DataFrame:
    """Carrega o dataset pontual experimental de alvos gerado na Etapa 2.1."""
    data_path = BASE_DIR.parent / "Base de dados" / "processed" / "alvos_v_treinamento.csv"
    assert data_path.exists(), f"Arquivo não encontrado: {data_path}"
    return pd.read_csv(data_path)


def test_partition_strictness_zero_leakage(dense_df: pd.DataFrame) -> None:
    """Valida se não há intersecção de ensaios entre treino e teste (zero leakage)."""
    partitioner = DataPartitioner(test_ensaios=[7, 8, 14])
    train_df, test_df = partitioner.split_dataframe(dense_df)

    train_ensaios = set(train_df["ensaio"].unique())
    test_ensaios = set(test_df["ensaio"].unique())

    intersection = train_ensaios.intersection(test_ensaios)
    assert len(intersection) == 0, f"Vazamento detectado! Ensaios em ambos: {intersection}"

    assert test_ensaios == {7, 8, 14}
    assert len(train_ensaios) == 13
    assert len(train_df) + len(test_df) == len(dense_df)


def test_partition_sample_counts(dense_df: pd.DataFrame, exp_df: pd.DataFrame) -> None:
    """Valida a contagem exata de amostras nos datasets denso e pontual."""
    partitioner = DataPartitioner(test_ensaios=[7, 8, 14])

    # Dataset denso (61 pontos por ensaio)
    train_dense, test_dense = partitioner.split_dataframe(dense_df)
    assert len(train_dense) == 13 * 61 == 793, f"Esperado 793 amostras de treino denso, obtido {len(train_dense)}"
    assert len(test_dense) == 3 * 61 == 183, f"Esperado 183 amostras de teste denso, obtido {len(test_dense)}"
    assert len(dense_df) == 976

    # Dataset pontual (8 pontos por ensaio)
    train_exp, test_exp = partitioner.split_dataframe(exp_df)
    assert len(train_exp) == 13 * 8 == 104, f"Esperado 104 amostras de treino pontual, obtido {len(train_exp)}"
    assert len(test_exp) == 3 * 8 == 24, f"Esperado 24 amostras de teste pontual, obtido {len(test_exp)}"
    assert len(exp_df) == 128


def test_groupkfold_integrity(dense_df: pd.DataFrame) -> None:
    """Valida a separação estrita por ensaio nas 4 dobras de validação cruzada."""
    partitioner = DataPartitioner(test_ensaios=[7, 8, 14])
    train_df, _ = partitioner.split_dataframe(dense_df)

    folds = partitioner.get_cv_folds(train_df, n_splits=4)
    assert len(folds) == 4

    validated_ensaios = set()
    for fold_idx, (train_idx, val_idx) in enumerate(folds):
        fold_train_ens = set(train_df.iloc[train_idx]["ensaio"].unique())
        fold_val_ens = set(train_df.iloc[val_idx]["ensaio"].unique())

        # Zero intersecção na dobra
        leakage = fold_train_ens.intersection(fold_val_ens)
        assert len(leakage) == 0, f"Vazamento no Fold {fold_idx}: {leakage}"

        # Ensaios validados são disjuntos
        assert len(validated_ensaios.intersection(fold_val_ens)) == 0
        validated_ensaios.update(fold_val_ens)

    # Todos os 13 ensaios de treino foram validados exatamente uma vez
    assert validated_ensaios == set(train_df["ensaio"].unique())
    assert len(validated_ensaios) == 13


def test_feature_target_scaler_properties(dense_df: pd.DataFrame) -> None:
    """Valida o escalonamento Z-score ajustado exclusivamente no treino."""
    partitioner = DataPartitioner(test_ensaios=[7, 8, 14])
    train_df, test_df = partitioner.split_dataframe(dense_df)

    X_train, y_train, _ = partitioner.extract_xy(train_df)
    X_test, y_test, _ = partitioner.extract_xy(test_df)

    scaler = FeatureTargetScaler()
    scaler.fit(X_train, y_train)

    X_train_s = scaler.transform_X(X_train)
    y_train_s = scaler.transform_y(y_train)

    # Médias de treino devem ser ~0
    np.testing.assert_allclose(X_train_s.mean(axis=0), 0.0, atol=1e-7)
    # Temperatura (coluna 0) é constante a 40 °C na bancada -> std é 0.0
    # As demais 3 features (CA0, eta, t) têm variação -> std é 1.0
    np.testing.assert_allclose(X_train_s[:, 0].std(), 0.0, atol=1e-7)
    np.testing.assert_allclose(X_train_s[:, 1:].std(axis=0), 1.0, atol=1e-7)
    np.testing.assert_allclose(float(y_train_s.mean()), 0.0, atol=1e-7)
    np.testing.assert_allclose(float(y_train_s.std()), 1.0, atol=1e-7)

    # Inversão exata
    X_rec = scaler.inverse_transform_X(X_train_s)
    y_rec = scaler.inverse_transform_y(y_train_s)
    np.testing.assert_allclose(X_rec, X_train, atol=1e-6)
    np.testing.assert_allclose(y_rec, y_train, atol=1e-6)

    # Teste escalonado sem erro
    X_test_s = scaler.transform_X(X_test)
    y_test_s = scaler.transform_y(y_test)
    assert X_test_s.shape == X_test.shape
    assert y_test_s.shape == y_test.shape


def test_scaler_serialization(dense_df: pd.DataFrame) -> None:
    """Valida que salvar e carregar o scaler restaura exatamente o comportamento."""
    partitioner = DataPartitioner(test_ensaios=[7, 8, 14])
    train_df, _ = partitioner.split_dataframe(dense_df)
    X_train, y_train, _ = partitioner.extract_xy(train_df)

    scaler = FeatureTargetScaler().fit(X_train, y_train)
    X_s = scaler.transform_X(X_train)
    y_s = scaler.transform_y(y_train)

    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        scaler.save(tmp_path)
        loaded = FeatureTargetScaler.load(tmp_path)

        X_s_loaded = loaded.transform_X(X_train)
        y_s_loaded = loaded.transform_y(y_train)

        np.testing.assert_array_equal(X_s, X_s_loaded)
        np.testing.assert_array_equal(y_s, y_s_loaded)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_unfitted_scaler_errors() -> None:
    """Valida que chamar transform ou save antes do fit lança RuntimeError."""
    scaler = FeatureTargetScaler()
    dummy = np.array([[1.0, 2.0, 3.0, 4.0]])

    with pytest.raises(RuntimeError):
        scaler.transform_X(dummy)

    with pytest.raises(RuntimeError):
        scaler.transform_y(np.array([1.0]))

    with pytest.raises(RuntimeError):
        scaler.save("dummy.joblib")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
