"""
Módulo de Fenômenos de Transporte e Cinética Química Heterogênea (FPM).
Contém classes e funções para modelagem de processos particulados e cinética de lixiviação.
"""

from .granulometry import RosinRammlerBennet
from .kinetics import LeachingKinetics
from .pbm_batch import BatchPBMSolver

__all__ = ["RosinRammlerBennet", "LeachingKinetics", "BatchPBMSolver"]
