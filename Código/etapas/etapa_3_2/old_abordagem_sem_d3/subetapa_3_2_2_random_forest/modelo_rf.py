"""Módulo do Modelo Random Forest Regressor para Predição da Taxa de Lixiviação.

Este módulo implementa a classe `KineticsRandomForest`, um encapsulador orientado a objetos
baseado em `sklearn.ensemble.RandomForestRegressor` para a predição da taxa de retração
interfacial |v(t)| = dD/dt a partir dos descritores operacionais [T, CA0, eta, t].

Principais Características Físicas e Numéricas:
    1. Transformação de Escala do Target (log1p): Como a taxa de retração varia de ~0,01 µm/min
       a > 1200 µm/min (mais de 4 ordens de magnitude), o modelo pode ser treinado no espaço
       y_log = ln(1 + |v|), garantindo sensibilidade adequada na fase lenta.
    2. Projeção de Não-Negatividade Física Estrita: As predições em escala física são
       garantidas como estritamente não-negativas (|v| >= 0) via projeção física,
       cumprindo as leis de conservação de massa e termodinâmica.
    3. Interpretabilidade: Extração direta de importâncias de atributos (MDI e permutação).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance


class KineticsRandomForest:
    """Regressão por Floresta Aleatória para Cinética de Dissolução de Zinco.

    Encapsula o RandomForestRegressor do scikit-learn com suporte integrado
    à transformação logarítmica do alvo (log1p), restrições físicas de não-negatividade,
    cálculo de importância de atributos e serialização padronizada.

    Attributes:
        target_transform: Estratégia de transformação do alvo ('log1p' ou 'linear').
        model: Instância subjacente de `RandomForestRegressor`.
        feature_names: Lista com os nomes das variáveis preditoras.
        is_fitted: Booleano indicando se o modelo foi ajustado.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: Union[str, float, int] = 1.0,
        bootstrap: bool = True,
        random_state: int = 42,
        n_jobs: int = -1,
        target_transform: Literal["log1p", "linear"] = "log1p",
        feature_names: Optional[List[str]] = None,
    ) -> None:
        """Inicializa o regressor KineticsRandomForest.

        Args:
            n_estimators: Número de árvores na floresta.
            max_depth: Profundidade máxima das árvores. Se None, nós se expandem até folhas puras.
            min_samples_split: Número mínimo de amostras necessárias para dividir um nó interno.
            min_samples_leaf: Número mínimo de amostras necessárias para ser um nó folha.
            max_features: Número de atributos a considerar ao buscar a melhor divisão.
            bootstrap: Se amostras bootstrap são usadas para construir árvores.
            random_state: Semente do gerador de números pseudo-aleatórios.
            n_jobs: Número de jobs em paralelo (-1 para todos os núcleos).
            target_transform: 'log1p' para ln(1 + y) ou 'linear' para escala direta.
            feature_names: Nomes dos atributos de entrada (opcional).
        """
        self.target_transform = target_transform
        self.feature_names = feature_names or [
            "temperatura_C",
            "CA0_mol_L",
            "razao_molar_eta",
            "t_min",
        ]
        self.model_params: Dict[str, Any] = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "min_samples_leaf": min_samples_leaf,
            "max_features": max_features,
            "bootstrap": bootstrap,
            "random_state": random_state,
            "n_jobs": n_jobs,
        }
        self.model = RandomForestRegressor(**self.model_params)
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "KineticsRandomForest":
        """Ajusta o modelo de floresta aleatória aos dados de treinamento.

        Args:
            X: Matriz de features de shape (N, D).
            y: Vetor de alvos em escala física (|v| >= 0) de shape (N,).

        Returns:
            A própria instância ajustada.
        """
        X_arr = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64).ravel()

        if self.target_transform == "log1p":
            # Target não-negativo comprimido em log1p: ln(1 + y) >= 0
            y_train = np.log1p(np.maximum(0.0, y_arr))
        else:
            y_train = np.maximum(0.0, y_arr)

        self.model.fit(X_arr, y_train)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prediz a taxa de retração interfacial |v(t)| em escala física (µm/min).

        Garante estritamente que a predição física nunca seja negativa (|v| >= 0).

        Args:
            X: Matriz de features de shape (N, D).

        Returns:
            Vetor 1D com as taxas preditas em escala física (µm/min), com |v| >= 0.
        """
        if not self.is_fitted:
            raise RuntimeError("O modelo precisa ser ajustado com fit() antes de predict().")

        X_arr = np.asarray(X, dtype=np.float64)
        raw_pred = self.model.predict(X_arr)

        if self.target_transform == "log1p":
            # Reversão física: exp(pred_log) - 1
            pred_physical = np.expm1(np.maximum(0.0, raw_pred))
        else:
            pred_physical = raw_pred

        # Restrição física inegociável: taxa de retração interfacial estritamente não-negativa
        return np.maximum(0.0, pred_physical)

    def predict_log(self, X: np.ndarray) -> np.ndarray:
        """Prediz a taxa no espaço logarítmico comprimido y_log = ln(1 + |v|).

        Args:
            X: Matriz de features de shape (N, D).

        Returns:
            Vetor 1D no espaço log1p, com y_log >= 0.
        """
        if not self.is_fitted:
            raise RuntimeError("O modelo precisa ser ajustado com fit() antes de predict_log().")

        X_arr = np.asarray(X, dtype=np.float64)
        if self.target_transform == "log1p":
            return np.maximum(0.0, self.model.predict(X_arr))
        else:
            pred_phys = self.predict(X_arr)
            return np.log1p(np.maximum(0.0, pred_phys))

    @property
    def feature_importances_(self) -> np.ndarray:
        """Retorna a importância relativa dos atributos baseada na redução de impureza (MDI).

        Returns:
            Vetor 1D de shape (D,) com as importâncias relativas normalizadas (soma = 1.0).
        """
        if not self.is_fitted:
            raise RuntimeError("O modelo precisa ser ajustado para obter importâncias de atributos.")
        return self.model.feature_importances_

    def compute_permutation_importance(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        n_repeats: int = 10,
        random_state: int = 42,
    ) -> Dict[str, np.ndarray]:
        """Calcula a importância de permutação dos atributos no conjunto de teste.

        Args:
            X_test: Matriz de features de teste.
            y_test: Alvos reais de teste em escala física.
            n_repeats: Número de repetições da permutação.
            random_state: Semente aleatória.

        Returns:
            Dicionário com 'importances_mean' e 'importances_std'.
        """
        if not self.is_fitted:
            raise RuntimeError("O modelo precisa ser ajustado antes de calcular importância.")

        X_arr = np.asarray(X_test, dtype=np.float64)
        y_arr = np.asarray(y_test, dtype=np.float64).ravel()

        # Scorer customizado baseado em R² físico
        def physical_r2_scorer(estimator: Any, X_eval: np.ndarray, y_eval: np.ndarray) -> float:
            pred_log = estimator.predict(X_eval)
            if self.target_transform == "log1p":
                pred = np.maximum(0.0, np.expm1(np.maximum(0.0, pred_log)))
            else:
                pred = np.maximum(0.0, pred_log)
            ss_res = np.sum((y_eval - pred) ** 2)
            ss_tot = np.sum((y_eval - np.mean(y_eval)) ** 2)
            return float(1.0 - (ss_res / (ss_tot + 1e-12)))

        result = permutation_importance(
            self.model,
            X_arr,
            y_arr,
            scoring=physical_r2_scorer,
            n_repeats=n_repeats,
            random_state=random_state,
            n_jobs=-1,
        )

        return {
            "importances_mean": result.importances_mean,
            "importances_std": result.importances_std,
        }

    def save(self, filepath: Union[str, Path], config_filepath: Optional[Union[str, Path]] = None) -> None:
        """Salva o modelo ajustado e metadados no disco.

        Args:
            filepath: Caminho do arquivo .joblib.
            config_filepath: Caminho do arquivo .json de metadados (opcional).
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model": self.model,
            "model_params": self.model_params,
            "target_transform": self.target_transform,
            "feature_names": self.feature_names,
            "is_fitted": self.is_fitted,
        }
        joblib.dump(payload, path)

        if config_filepath:
            cfg_path = Path(config_filepath)
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            config_dict = {
                "model_type": "KineticsRandomForest",
                "target_transform": self.target_transform,
                "feature_names": self.feature_names,
                "hyperparameters": {
                    k: (v if not isinstance(v, np.integer) else int(v))
                    for k, v in self.model_params.items()
                },
                "n_estimators": self.model.n_estimators,
                "is_fitted": self.is_fitted,
            }
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "KineticsRandomForest":
        """Carrega um modelo previamente persistido em arquivo .joblib.

        Args:
            filepath: Caminho do arquivo .joblib salvo.

        Returns:
            Instância carregada e pronta para inferência.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de modelo não encontrado: {path}")

        payload = joblib.load(path)
        instance = cls(
            target_transform=payload.get("target_transform", "log1p"),
            feature_names=payload.get("feature_names"),
            **payload.get("model_params", {}),
        )
        instance.model = payload["model"]
        instance.is_fitted = payload.get("is_fitted", True)
        return instance
