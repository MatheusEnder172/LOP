"""Módulo do Modelo XGBoost Regressor para Predição da Taxa de Lixiviação.

Este módulo implementa a classe `KineticsXGBoost`, um encapsulador orientado a objetos
baseado em `xgboost.XGBRegressor` para a predição contínua da taxa de retração interfacial
|v(t)| = dD/dt a partir dos descritores operacionais [T, CA0, eta, t].

Fundamentos Físicos e Numéricos:
    1. Gradient Boosted Decision Trees (GBDT):
       Combina sequencialmente árvores de decisão rasas, onde cada nova árvore é ajustada
       para corrigir os resíduos (gradientes de primeira e segunda ordem) da soma acumulada.
    2. Regularização Avançada (L1/L2 e Shrinkage):
       Taxa de aprendizado (learning_rate / eta) amortecida combinada com regularização L1
       (reg_alpha) e L2 (reg_lambda) nas folhas, prevenindo memorização de ruído.
    3. Transformação do Alvo (log1p) e Não-Negatividade Física:
       Como a taxa varia por mais de quatro ordens de magnitude (de ~0,01 a > 1200 µm/min),
       o XGBoost opera no espaço y_log = ln(1 + |v|), com reversão física
       v = exp(y_log) - 1 >= 0 e truncamento inferior estrito (|v| >= 0).
    4. Interpretabilidade Físico-Química:
       Cálculo nativo de importância de atributos por Ganho (Gain), Frequência (Weight)
       e Cobertura (Cover), complementado por permutação no teste cego.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import joblib
import numpy as np
import xgboost as xgb
from sklearn.inspection import permutation_importance


class KineticsXGBoost:
    """Regressão por Gradient Boosting (XGBoost) para Cinética de Dissolução de Zinco.

    Encapsula o XGBRegressor do XGBoost com suporte integrado à transformação
    logarítmica do alvo (log1p), restrições físicas de não-negatividade,
    cálculo de métricas de importância de atributos e serialização padronizada (.json / .joblib).

    Attributes:
        target_transform: Estratégia de transformação do alvo ('log1p' ou 'linear').
        model: Instância subjacente de `xgb.XGBRegressor`.
        feature_names: Lista com os nomes das variáveis preditoras.
        is_fitted: Booleano indicando se o modelo foi ajustado.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.08,
        max_depth: int = 5,
        subsample: float = 0.85,
        colsample_bytree: float = 0.85,
        reg_alpha: float = 0.1,
        reg_lambda: float = 1.0,
        min_child_weight: float = 2.0,
        random_state: int = 42,
        n_jobs: int = -1,
        target_transform: Literal["log1p", "linear"] = "log1p",
        feature_names: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Inicializa o regressor KineticsXGBoost.

        Args:
            n_estimators: Número de rodadas de boosting (árvores sequenciais).
            learning_rate: Fator de amortecimento dos passos de gradiente (shrinkage / eta).
            max_depth: Profundidade máxima de cada árvore base.
            subsample: Fração de subamostragem aleatória das linhas para cada árvore.
            colsample_bytree: Fração de subamostragem aleatória das colunas (features) por árvore.
            reg_alpha: Termo de regularização L1 nos pesos das folhas (Lasso).
            reg_lambda: Termo de regularização L2 nos pesos das folhas (Ridge).
            min_child_weight: Soma mínima de pesos hessianos necessária em um nó folha.
            random_state: Semente do gerador de números pseudo-aleatórios.
            n_jobs: Número de threads paralelas (-1 para todos os núcleos).
            target_transform: 'log1p' para ln(1 + y) ou 'linear' para escala direta.
            feature_names: Nomes dos atributos de entrada (opcional).
            **kwargs: Parâmetros adicionais repassados ao XGBRegressor (ex: objective, eval_metric).
        """
        self.target_transform = target_transform
        self.feature_names = feature_names or [
            "temperatura_C",
            "CA0_mol_L",
            "razao_molar_eta",
            "t_min",
        ]
        self.model_params: Dict[str, Any] = {
            "n_estimators": int(n_estimators),
            "learning_rate": float(learning_rate),
            "max_depth": int(max_depth),
            "subsample": float(subsample),
            "colsample_bytree": float(colsample_bytree),
            "reg_alpha": float(reg_alpha),
            "reg_lambda": float(reg_lambda),
            "min_child_weight": float(min_child_weight),
            "random_state": int(random_state),
            "n_jobs": int(n_jobs),
            "objective": kwargs.get("objective", "reg:squarederror"),
            "eval_metric": kwargs.get("eval_metric", "rmse"),
        }
        # Adicionar quaisquer outros kwargs
        for k, v in kwargs.items():
            if k not in self.model_params:
                self.model_params[k] = v

        self.model = xgb.XGBRegressor(**self.model_params)
        self.is_fitted: bool = False

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        eval_set: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
        verbose: bool = False,
    ) -> "KineticsXGBoost":
        """Ajusta o modelo de gradient boosting aos dados de treinamento.

        Args:
            X: Matriz de features de shape (N, D).
            y: Vetor de alvos em escala física (|v| >= 0) de shape (N,).
            eval_set: Lista de tuplas (X_val, y_val) para monitoramento (opcional).
            verbose: Se True, imprime o histórico de perda a cada iteração.

        Returns:
            A própria instância ajustada.
        """
        X_arr = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64).ravel()

        if self.target_transform == "log1p":
            y_train = np.log1p(np.maximum(0.0, y_arr))
        else:
            y_train = np.maximum(0.0, y_arr)

        eval_set_proc = None
        if eval_set is not None:
            eval_set_proc = []
            for X_val, y_val in eval_set:
                X_v = np.asarray(X_val, dtype=np.float64)
                y_v = np.asarray(y_val, dtype=np.float64).ravel()
                if self.target_transform == "log1p":
                    y_v_proc = np.log1p(np.maximum(0.0, y_v))
                else:
                    y_v_proc = np.maximum(0.0, y_v)
                eval_set_proc.append((X_v, y_v_proc))

        self.model.fit(
            X_arr,
            y_train,
            eval_set=eval_set_proc,
            verbose=verbose,
        )
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
        if self.target_transform == "log1p":
            return np.maximum(0.0, self.model.predict(X_arr))
        else:
            pred_phys = self.predict(X_arr)
            return np.log1p(np.maximum(0.0, pred_phys))

    @property
    def feature_importances_(self) -> np.ndarray:
        """Retorna a importância relativa dos atributos baseada no Ganho (Gain).

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
        """Salva o modelo ajustado e metadados no disco em formatos .json e/ou .joblib.

        Args:
            filepath: Caminho do arquivo de destino (.json ou .joblib).
            config_filepath: Caminho do arquivo .json de metadados (opcional).
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix == ".json":
            self.model.save_model(str(path))
        else:
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
                "model_type": "KineticsXGBoost",
                "target_transform": self.target_transform,
                "feature_names": self.feature_names,
                "hyperparameters": {
                    k: (v if not isinstance(v, (np.integer, np.floating)) else float(v) if isinstance(v, np.floating) else int(v))
                    for k, v in self.model_params.items()
                },
                "n_estimators": self.model_params["n_estimators"],
                "is_fitted": self.is_fitted,
            }
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Union[str, Path], config_filepath: Optional[Union[str, Path]] = None) -> "KineticsXGBoost":
        """Carrega um modelo previamente salvo.

        Args:
            filepath: Caminho do arquivo .json ou .joblib.
            config_filepath: Caminho do arquivo de configuração .json (necessário se filepath for .json).

        Returns:
            Instância carregada e pronta para inferência.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de modelo não encontrado: {path}")

        if path.suffix == ".json":
            # Se for formato nativo do XGBoost
            if config_filepath and Path(config_filepath).exists():
                with open(config_filepath, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                target_transform = cfg.get("target_transform", "log1p")
                feature_names = cfg.get("feature_names")
                params = cfg.get("hyperparameters", {})
            else:
                target_transform = "log1p"
                feature_names = None
                params = {}

            instance = cls(target_transform=target_transform, feature_names=feature_names, **params)
            instance.model.load_model(str(path))
            instance.is_fitted = True
            return instance
        else:
            payload = joblib.load(path)
            instance = cls(
                target_transform=payload.get("target_transform", "log1p"),
                feature_names=payload.get("feature_names"),
                **payload.get("model_params", {}),
            )
            instance.model = payload["model"]
            instance.is_fitted = payload.get("is_fitted", True)
            return instance
