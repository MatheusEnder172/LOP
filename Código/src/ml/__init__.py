"""Módulo de Machine Learning (DDM) para Lixiviação de Zinco.

Contém classes para pré-processamento, particionamento e escalonamento de dados,
além de interfaces para modelos de aprendizado supervisionado (MLP, RF, SVR, XGBoost).
"""

from src.ml.preprocessing import DataPartitioner, FeatureTargetScaler

__all__ = ["DataPartitioner", "FeatureTargetScaler"]
