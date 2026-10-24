"""Módulo de Modelagem Híbrida do Projeto LOP (UFMG).

Contém orquestradores e acopladores entre modelos orientados por dados (DDM / Machine Learning)
e modelos mecanicistas baseados em primeiros princípios (FPM / Balanço Populacional PBM).
"""

from .serial_hybrid import SerialHybridModel

__all__ = ["SerialHybridModel"]
