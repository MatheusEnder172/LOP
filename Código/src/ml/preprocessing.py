"""Módulo de Pré-Processamento e Particionamento de Dados.

Implementa a partição estrita por ensaio (evitando vazamento temporal e de ensaio),
escalonamento com StandardScaler ajustado exclusivamente no treino, geração de
dobras de validação cruzada (GroupKFold) e persistência de transformadores.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler


class DataPartitioner:
    """Gerenciador de partição de dados de lixiviação por ensaio experimental.

    Garante a integridade estatística dividindo os dados ao nível de ensaio
    (batch), evitando qualquer vazamento temporal entre instantes de tempo
    do mesmo ensaio físico.

    Attributes:
        test_ensaios: Lista de identificadores de ensaios alocados ao Teste Cego.
        feature_cols: Lista com os nomes das colunas de entrada (features).
        target_col: Nome da coluna alvo (velocidade interfacial |v|).
    """

    DEFAULT_TEST_ENSAIOS: List[int] = [7, 8, 14]
    DEFAULT_TRAIN_ENSAIOS: List[int] = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 15, 16]
    FEATURE_COLS: List[str] = ["temperatura_C", "CA0_mol_L", "razao_molar_eta", "t_min"]
    TARGET_COL: str = "abs_v_alvo_um_min"

    def __init__(
        self,
        test_ensaios: Optional[List[int]] = None,
        feature_cols: Optional[List[str]] = None,
        target_col: Optional[str] = None,
    ) -> None:
        """Inicializa o particionador de dados.

        Args:
            test_ensaios: Lista opcional de ensaios de teste. Se None, usa [7, 8, 14].
            feature_cols: Lista opcional de features. Se None, usa DEFAULT.
            target_col: Coluna alvo opcional. Se None, usa 'abs_v_alvo_um_min'.
        """
        self.test_ensaios = sorted(test_ensaios) if test_ensaios is not None else list(self.DEFAULT_TEST_ENSAIOS)
        self.feature_cols = list(feature_cols) if feature_cols is not None else list(self.FEATURE_COLS)
        self.target_col = target_col or self.TARGET_COL

    def split_dataframe(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Divide um DataFrame em conjuntos de Treino e Teste Cego por ensaio.

        Args:
            df: DataFrame contendo obrigatoriamente a coluna 'ensaio'.

        Returns:
            Tupla (train_df, test_df) com cópias independentes dos dados.

        Raises:
            ValueError: Se a coluna 'ensaio' estiver ausente ou se algum ensaio
                de teste não existir no DataFrame.
        """
        if "ensaio" not in df.columns:
            raise ValueError("O DataFrame deve conter a coluna 'ensaio'.")

        ensaios_presentes = set(df["ensaio"].unique())
        test_set = set(self.test_ensaios)

        missing_test = test_set - ensaios_presentes
        if missing_test:
            raise ValueError(f"Ensaios de teste não encontrados no dataset: {missing_test}")

        test_mask = df["ensaio"].isin(self.test_ensaios)
        train_df = df[~test_mask].copy().reset_index(drop=True)
        test_df = df[test_mask].copy().reset_index(drop=True)

        return train_df, test_df

    def extract_xy(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extrai matriz de features X, vetor target y e vetor de grupos de ensaio.

        Args:
            df: DataFrame com as colunas necessárias.

        Returns:
            Tupla (X, y, groups):
                - X: array float64 de shape (N, n_features)
                - y: array float64 de shape (N,)
                - groups: array int64 de shape (N,) identificando o ensaio de cada linha
        """
        missing_feats = [col for col in self.feature_cols if col not in df.columns]
        if missing_feats:
            raise ValueError(f"Features ausentes no DataFrame: {missing_feats}")
        if self.target_col not in df.columns:
            raise ValueError(f"Coluna target '{self.target_col}' ausente no DataFrame.")

        X = df[self.feature_cols].values.astype(np.float64)
        y = df[self.target_col].values.astype(np.float64)
        groups = df["ensaio"].values.astype(np.int64)

        return X, y, groups

    def get_cv_folds(
        self, train_df: pd.DataFrame, n_splits: int = 4
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Gera índices de treino e validação para Validação Cruzada por Ensaio.

        Usa GroupKFold para garantir que todas as amostras temporais de um mesmo
        ensaio estejam ou no conjunto de treino da dobra ou no conjunto de validação,
        nunca divididas entre ambos.

        Args:
            train_df: DataFrame de treino com a coluna 'ensaio'.
            n_splits: Número de dobras (padrão: 4, distribuindo os 13 ensaios em 3, 3, 3, 4).

        Returns:
            Lista de tuplas (train_indices, val_indices) para cada dobra.
        """
        X, y, groups = self.extract_xy(train_df)
        gkf = GroupKFold(n_splits=n_splits)

        folds = []
        for train_idx, val_idx in gkf.split(X, y, groups):
            folds.append((train_idx, val_idx))

        return folds


class FeatureTargetScaler:
    """Escalonador conjunto para matriz de features e variável target.

    Utiliza StandardScaler (Z-Score: média = 0, desvio-padrão = 1) ajustado
    exclusivamente com os dados de Treino para prevenir data leakage.

    Attributes:
        scaler_X: Instância de StandardScaler ajustada nas features.
        scaler_y: Instância de StandardScaler ajustada no target.
        is_fitted: Booleano indicando se os scalers foram ajustados.
    """

    def __init__(self) -> None:
        """Inicializa os escalonadores de features e target."""
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.is_fitted: bool = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> FeatureTargetScaler:
        """Ajusta os transformadores estatísticos aos dados de treino.

        Args:
            X_train: Matriz de features de treino (N, D).
            y_train: Vetor ou matriz target de treino (N,) ou (N, 1).

        Returns:
            A própria instância ajustada.
        """
        y_train_2d = y_train.reshape(-1, 1) if y_train.ndim == 1 else y_train

        self.scaler_X.fit(X_train)
        self.scaler_y.fit(y_train_2d)
        self.is_fitted = True
        return self

    def transform_X(self, X: np.ndarray) -> np.ndarray:
        """Aplica a normalização Z-score nas features.

        Args:
            X: Matriz de features (N, D).

        Returns:
            Matriz escalonada (N, D).
        """
        self._check_fitted()
        return self.scaler_X.transform(X)

    def inverse_transform_X(self, X_scaled: np.ndarray) -> np.ndarray:
        """Converte as features escalonadas de volta à escala física original.

        Args:
            X_scaled: Matriz normalizada (N, D).

        Returns:
            Matriz em unidades físicas de engenharia.
        """
        self._check_fitted()
        return self.scaler_X.inverse_transform(X_scaled)

    def transform_y(self, y: np.ndarray) -> np.ndarray:
        """Aplica a normalização Z-score no target.

        Args:
            y: Vetor (N,) ou matriz (N, 1).

        Returns:
            Vetor escalonado 1D (N,).
        """
        self._check_fitted()
        y_2d = y.reshape(-1, 1) if y.ndim == 1 else y
        y_scaled_2d = self.scaler_y.transform(y_2d)
        return y_scaled_2d.ravel()

    def inverse_transform_y(self, y_scaled: np.ndarray) -> np.ndarray:
        """Converte o target predito normalizado de volta à unidade física (µm/min).

        Args:
            y_scaled: Vetor (N,) ou matriz (N, 1).

        Returns:
            Vetor em escala natural (µm/min).
        """
        self._check_fitted()
        y_scaled_2d = y_scaled.reshape(-1, 1) if y_scaled.ndim == 1 else y_scaled
        y_orig_2d = self.scaler_y.inverse_transform(y_scaled_2d)
        return y_orig_2d.ravel()

    def save(self, filepath: str | Path) -> None:
        """Serializa os transformadores em arquivo .joblib.

        Args:
            filepath: Caminho de destino para salvar o arquivo de scalers.
        """
        self._check_fitted()
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "scaler_X": self.scaler_X,
                "scaler_y": self.scaler_y,
                "is_fitted": self.is_fitted,
            },
            path,
        )

    @classmethod
    def load(cls, filepath: str | Path) -> FeatureTargetScaler:
        """Carrega transformadores serializados a partir de arquivo .joblib.

        Args:
            filepath: Caminho do arquivo .joblib salvo.

        Returns:
            Instância carregada e pronta para transformação.
        """
        data = joblib.load(filepath)
        instance = cls()
        instance.scaler_X = data["scaler_X"]
        instance.scaler_y = data["scaler_y"]
        instance.is_fitted = data["is_fitted"]
        return instance

    def _check_fitted(self) -> None:
        """Verifica se os transformadores já foram ajustados."""
        if not self.is_fitted:
            raise RuntimeError(
                "O escalonador ainda não foi ajustado. Chame fit() antes de transform/save."
            )
