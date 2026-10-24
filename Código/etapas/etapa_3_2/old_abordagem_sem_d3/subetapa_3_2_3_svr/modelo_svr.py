"""Módulo do Modelo Support Vector Regression (SVR) para Predição da Taxa de Lixiviação.

Este módulo implementa a classe `KineticsSVR`, um encapsulador orientado a objetos baseado
em `sklearn.svm.SVR` para a predição contínua da taxa de retração interfacial |v(t)| = dD/dt
a partir dos descritores operacionais padronizados [T, CA0, eta, t].

Fundamentos Físicos e Matemáticos:
    1. Espaço Dual e Kernel RBF:
       f(x) = sum_{i in SV} (alpha_i - alpha_i*) * exp(-gamma * ||x_i - x||^2) + b
       A formulação em espaço de Hilbert com funções de base radial (RBF) confere
       suavidade e diferenciabilidade infinita C^inf às trajetórias de dissolução.
    2. Perda epsilon-Insensível (Vapnik):
       Desvios dentro do tubo [-epsilon, +epsilon] não geram penalidade, induzindo
       esparsidade nos vetores de suporte (SVs) e robustez frente a ruídos amostrais.
    3. Transformação do Alvo (log1p) e Não-Negatividade Física:
       Como a velocidade varia por mais de quatro ordens de grandeza, o SVR opera no
       espaço y_log = ln(1 + |v|), com reversão física v = exp(y_log) - 1 >= 0.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import joblib
import numpy as np
from sklearn.svm import SVR


class KineticsSVR:
    """Regressão por Vetores de Suporte com Kernel RBF para Cinética de Dissolução.

    Encapsula o SVR do scikit-learn com padronização de atributos, suporte à
    transformação log1p do alvo, garantia de não-negatividade termodinâmica e
    métodos de diagnóstico de vetores de suporte.

    Attributes:
        C: Parâmetro de regularização (penalidade para violações fora do tubo).
        epsilon: Semilargura da zona de insensibilidade ao erro.
        gamma: Coeficiente de curvatura do kernel RBF.
        target_transform: Estratégia de transformação do alvo ('log1p' ou 'linear').
        model: Instância subjacente de `sklearn.svm.SVR`.
        scaler_X: Scaler opcional para as features (ou None se X já estiver escalado).
        feature_names: Nomes dos atributos preditores.
        is_fitted: Booleano indicando se o modelo foi ajustado.
    """

    def __init__(
        self,
        C: float = 10.0,
        epsilon: float = 0.05,
        gamma: Union[str, float] = "scale",
        kernel: str = "rbf",
        target_transform: Literal["log1p", "linear"] = "log1p",
        scaler_X: Optional[Any] = None,
        feature_names: Optional[List[str]] = None,
    ) -> None:
        """Inicializa o regressor KineticsSVR.

        Args:
            C: Regularização de margem suave. Valores maiores toleram menos erros.
            epsilon: Tolerância do tubo de erro. Desvios < epsilon têm perda zero.
            gamma: Curvatura do kernel RBF ('scale', 'auto' ou float).
            kernel: Tipo de kernel (padrão: 'rbf').
            target_transform: 'log1p' para ln(1 + y) ou 'linear' para escala direta.
            scaler_X: Scaler StandardScaler para as features (opcional).
            feature_names: Nomes dos atributos de entrada (opcional).
        """
        self.C = float(C)
        self.epsilon = float(epsilon)
        self.gamma = gamma
        self.kernel = kernel
        self.target_transform = target_transform
        self.scaler_X = scaler_X
        self.feature_names = feature_names or [
            "temperatura_C",
            "CA0_mol_L",
            "razao_molar_eta",
            "t_min",
        ]

        self.model = SVR(
            kernel=self.kernel,
            C=self.C,
            epsilon=self.epsilon,
            gamma=self.gamma,
        )
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "KineticsSVR":
        """Ajusta o modelo SVR aos dados de treinamento.

        Args:
            X: Matriz de features de shape (N, D).
            y: Vetor de alvos em escala física (|v| >= 0) de shape (N,).

        Returns:
            A própria instância ajustada.
        """
        X_arr = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64).ravel()

        if self.scaler_X is not None:
            X_proc = self.scaler_X.transform(X_arr)
        else:
            X_proc = X_arr

        if self.target_transform == "log1p":
            y_train = np.log1p(np.maximum(0.0, y_arr))
        else:
            y_train = np.maximum(0.0, y_arr)

        self.model.fit(X_proc, y_train)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prediz a taxa de retração interfacial |v(t)| em escala física (µm/min).

        Aplica a projeção de truncamento inferior para assegurar que |v| >= 0 estritamente.

        Args:
            X: Matriz de features de shape (N, D).

        Returns:
            Vetor 1D com as taxas preditas em escala física (µm/min), com |v| >= 0.
        """
        if not self.is_fitted:
            raise RuntimeError("O modelo precisa ser ajustado com fit() antes de predict().")

        X_arr = np.asarray(X, dtype=np.float64)
        if self.scaler_X is not None:
            X_proc = self.scaler_X.transform(X_arr)
        else:
            X_proc = X_arr

        raw_pred = self.model.predict(X_proc)

        if self.target_transform == "log1p":
            pred_physical = np.expm1(np.maximum(0.0, raw_pred))
        else:
            pred_physical = raw_pred

        # Restrição física inegociável: taxa estritamente não-negativa
        return np.maximum(0.0, pred_physical)

    def predict_log(self, X: np.ndarray) -> np.ndarray:
        """Prediz no espaço logarítmico comprimido y_log = ln(1 + |v|).

        Args:
            X: Matriz de features de shape (N, D).

        Returns:
            Vetor 1D no espaço log1p, com y_log >= 0.
        """
        if not self.is_fitted:
            raise RuntimeError("O modelo precisa ser ajustado com fit() antes de predict_log().")

        X_arr = np.asarray(X, dtype=np.float64)
        if self.scaler_X is not None:
            X_proc = self.scaler_X.transform(X_arr)
        else:
            X_proc = X_arr

        if self.target_transform == "log1p":
            return np.maximum(0.0, self.model.predict(X_proc))
        else:
            pred_phys = self.predict(X_arr)
            return np.log1p(np.maximum(0.0, pred_phys))

    @property
    def n_support_(self) -> int:
        """Retorna o número total de vetores de suporte (amostras críticas)."""
        if not self.is_fitted:
            raise RuntimeError("O modelo precisa ser ajustado para obter número de vetores de suporte.")
        return len(self.model.support_)

    @property
    def support_ratio_(self) -> float:
        """Retorna a fração de amostras de treino que se tornaram vetores de suporte."""
        if not self.is_fitted:
            raise RuntimeError("O modelo precisa ser ajustado para obter razão de vetores de suporte.")
        # shape_fit_[0] é o número de amostras no treino
        n_samples_fit = getattr(self.model, "shape_fit_", [1])[0]
        return float(len(self.model.support_) / n_samples_fit)

    def save(self, filepath: Union[str, Path], config_filepath: Optional[Union[str, Path]] = None) -> None:
        """Salva o modelo ajustado e metadados no disco em formato .joblib e .json.

        Args:
            filepath: Caminho do arquivo .joblib.
            config_filepath: Caminho do arquivo .json de metadados (opcional).
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "model": self.model,
            "C": self.C,
            "epsilon": self.epsilon,
            "gamma": self.gamma,
            "kernel": self.kernel,
            "target_transform": self.target_transform,
            "scaler_X": self.scaler_X,
            "feature_names": self.feature_names,
            "is_fitted": self.is_fitted,
        }
        joblib.dump(payload, path)

        if config_filepath:
            cfg_path = Path(config_filepath)
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            config_dict = {
                "model_type": "KineticsSVR",
                "kernel": self.kernel,
                "C": self.C,
                "epsilon": self.epsilon,
                "gamma": str(self.gamma),
                "target_transform": self.target_transform,
                "feature_names": self.feature_names,
                "n_support_vectors": self.n_support_ if self.is_fitted else None,
                "support_ratio": self.support_ratio_ if self.is_fitted else None,
                "is_fitted": self.is_fitted,
            }
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "KineticsSVR":
        """Carrega um modelo SVR previamente salvo.

        Args:
            filepath: Caminho do arquivo .joblib.

        Returns:
            Instância carregada e pronta para inferência.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de modelo não encontrado: {path}")

        payload = joblib.load(path)
        instance = cls(
            C=payload.get("C", 10.0),
            epsilon=payload.get("epsilon", 0.05),
            gamma=payload.get("gamma", "scale"),
            kernel=payload.get("kernel", "rbf"),
            target_transform=payload.get("target_transform", "log1p"),
            scaler_X=payload.get("scaler_X"),
            feature_names=payload.get("feature_names"),
        )
        instance.model = payload["model"]
        instance.is_fitted = payload.get("is_fitted", True)
        return instance
