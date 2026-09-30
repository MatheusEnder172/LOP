"""
Módulo de Caracterização Granulométrica de Sistemas Particulados.
Implementa a função de distribuição e densidade de Rosin-Rammler-Bennet (RRB).

Referências:
- Bortot Coelho, F. E. (2017). Dissertação de Mestrado, PPGEM/UFMG, Seções 3.5.1 e 5.1.2.
- LeBlanc, S. E.; Fogler, H. S. (1987). AIChE Journal, 33(1), 54-63.
- Randolph, A. D.; Larson, M. A. (1988). Theory of Particulate Processes.
"""

from typing import Dict, Tuple, Union
import numpy as np
from scipy.special import gamma


class RosinRammlerBennet:
    """Modelo de Distribuição Granulométrica Rosin-Rammler-Bennet (RRB).

    Descreve a função cumulativa passante F(D) e a função densidade f0(D)
    para populações polidispersas de partículas minerais.

    Atributos:
        d63_2 (float): Diâmetro característico no qual 63,2% da massa passa (µm).
        m (float): Módulo de dispersão ou uniformidade (adimensional).
    """

    def __init__(self, d63_2: float = 41.65, m: float = 1.022) -> None:
        """Inicializa a distribuição RRB com os parâmetros calibrados.

        Args:
            d63_2: Diâmetro característico D_63,2 em micrometros (µm). Padrão: 41,65 µm.
            m: Parâmetro adimensional de dispersão/uniformidade. Padrão: 1,022.
        """
        if d63_2 <= 0.0:
            raise ValueError(f"d63_2 deve ser positivo, recebido: {d63_2}")
        if m <= 0.0:
            raise ValueError(f"m deve ser positivo, recebido: {m}")

        self.d63_2 = float(d63_2)
        self.m = float(m)

    def cumulative_passing(self, d: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Calcula a fração mássica acumulada passante F(D).

        F(D) = 1 - exp(-(D / D_63,2)^m)

        Args:
            d: Diâmetro de partícula ou vetor de diâmetros (µm).

        Returns:
            Fração mássica acumulada passante (0 a 1).
        """
        d_arr = np.asarray(d, dtype=np.float64)
        # Garantir não-negatividade de diâmetros
        d_pos = np.maximum(d_arr, 0.0)
        f_val = 1.0 - np.exp(-((d_pos / self.d63_2) ** self.m))

        if np.isscalar(d):
            return float(f_val)
        return f_val

    def probability_density(self, d: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Calcula a função densidade de probabilidade mássica f0(D) = dF/dD.

        f0(D) = (m / D_63,2) * (D / D_63,2)^(m - 1) * exp(-(D / D_63,2)^m)

        Args:
            d: Diâmetro de partícula ou vetor de diâmetros (µm).

        Returns:
            Densidade de frequência inicial em base mássica (µm^-1).
        """
        d_arr = np.asarray(d, dtype=np.float64)
        # Evitar divisão por zero ou log de zero em D = 0
        d_pos = np.maximum(d_arr, 1e-12)

        term1 = (self.m / self.d63_2) * ((d_pos / self.d63_2) ** (self.m - 1.0))
        term2 = np.exp(-((d_pos / self.d63_2) ** self.m))
        f0_val = term1 * term2

        # Para D <= 0, densidade é nula
        if isinstance(f0_val, np.ndarray):
            f0_val[d_arr <= 0.0] = 0.0
            return f0_val
        return float(f0_val) if d_arr > 0.0 else 0.0

    def analytical_moment(self, k: int) -> float:
        """Calcula analiticamente o k-ésimo momento da distribuição RRB.

        M_k = E[D^k] = integral_0^inf D^k * f0(D) dD = (D_63,2)^k * Gamma(1 + k/m)

        Args:
            k: Ordem do momento desejado (ex: 1 para média, 3 para volume).

        Returns:
            Valor analítico do momento M_k (µm^k).
        """
        if k < 0:
            raise ValueError(f"Ordem do momento k deve ser >= 0, recebido: {k}")
        return float((self.d63_2 ** k) * gamma(1.0 + (k / self.m)))

    def mean_diameter(self) -> float:
        """Calcula o diâmetro médio da distribuição (momento de 1ª ordem).

        mu = D_63,2 * Gamma(1 + 1/m)
        """
        return self.analytical_moment(1)

    def variance(self) -> float:
        """Calcula a variância sigma² da distribuição.

        sigma² = M_2 - (M_1)²
        """
        m1 = self.analytical_moment(1)
        m2 = self.analytical_moment(2)
        return float(m2 - (m1 ** 2))

    def coefficient_of_variation(self) -> float:
        """Calcula o coeficiente de variação CV = sigma / mu."""
        var = self.variance()
        mu = self.mean_diameter()
        return float(np.sqrt(var) / mu)

    def generate_mesh(
        self,
        d_min: float = 0.01,
        d_max: float = 297.0,
        n_points: int = 1500
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """Gera a malha de diâmetros discretizados e avalia a densidade e o momento M3(0).

        Args:
            d_min: Diâmetro mínimo da malha (µm). Padrão: 0.01 µm.
            d_max: Diâmetro máximo da malha (µm). Padrão: 297.0 µm.
            n_points: Número de nós na discretização linear. Padrão: 1500.

        Returns:
            Tupla (d_mesh, f0_mesh, m3_numerical):
                - d_mesh: Vetor linear de diâmetros (µm).
                - f0_mesh: Vetor de densidades f0(D) (µm^-1).
                - m3_numerical: Terceiro momento volumétrico integrado numericamente pela regra dos trapézios.
        """
        d_mesh = np.linspace(d_min, d_max, n_points)
        f0_mesh = self.probability_density(d_mesh)
        # Integração numérica de M3 = integral(D^3 * f0(D) dD)
        m3_numerical = float(np.trapezoid(f0_mesh * (d_mesh ** 3), d_mesh))

        return d_mesh, f0_mesh, m3_numerical

    def evaluate_fit(
        self, diametros: np.ndarray, fracao_exp: np.ndarray
    ) -> Dict[str, float]:
        """Avalia a concordância estatística entre os dados experimentais e o modelo.

        Args:
            diametros: Vetor de diâmetros medidos experimentalmente (µm).
            fracao_exp: Vetor de fração acumulada passante experimental (0 a 1).

        Returns:
            Dicionário com métricas R², RMSE e MAE.
        """
        d_arr = np.asarray(diametros, dtype=np.float64)
        y_real = np.asarray(fracao_exp, dtype=np.float64)
        y_pred = self.cumulative_passing(d_arr)

        residuos = y_real - y_pred
        ss_res = np.sum(residuos ** 2)
        ss_tot = np.sum((y_real - np.mean(y_real)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot)
        rmse = np.sqrt(np.mean(residuos ** 2))
        mae = np.mean(np.abs(residuos))

        return {
            "R2": float(r2),
            "RMSE": float(rmse),
            "MAE": float(mae),
            "SS_res": float(ss_res),
        }
