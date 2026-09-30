"""
Módulo do Resolvedor do Balanço Populacional (PBM) em Reatores Batelada.
Implementa a solução analítico-numérica pelo Método das Características para
populações polidispersas de partículas sob retração com taxa homogênea v(t).

Referências:
- Herbst, J. A. (1979). Rate Processes of Extractive Metallurgy. Plenum Press.
- Bortot Coelho, F. E. (2017). Dissertação de Mestrado, PPGEM/UFMG, Capítulos 3 e 5.
- Randolph, A. D.; Larson, M. A. (1988). Theory of Particulate Processes.
- LeBlanc, S. E.; Fogler, H. S. (1987). AIChE Journal, 33(1), 54-63.
"""

from typing import Any, Callable, Dict, Optional, Union
import numpy as np
from scipy.integrate import solve_ivp, trapezoid
from scipy.interpolate import PchipInterpolator

from .granulometry import RosinRammlerBennet
from .kinetics import LeachingKinetics


class BatchPBMSolver:
    """Resolvedor do Balanço Populacional em Batelada via Método das Características.

    Resolve a dinâmica de retração de partículas sólidas esféricas em sistema batelada
    acoplada ao consumo estequiométrico de reagente lixiviante (Herbst, 1979).

    A taxa de retração interfacial v(t) = dD/dt é independente do diâmetro D
    (regime de reação química superficial pura), permitindo transformar a EDP
    hiperbólica do PBM em uma EDO ordinária de deslocamento diametral acumulado:
        d(delta)/dt = |v(t)| = -v(t) >= 0, com delta(0) = 0.

    Atributos:
        granulometry (RosinRammlerBennet): Objeto contendo os parâmetros e métodos da distribuição RRB.
        kinetics (LeachingKinetics): Objeto contendo o equacionamento cinético e balanço de Herbst.
        d_mesh (np.ndarray): Vetor de diâmetros discretizados da distribuição inicial (µm).
        f0_mesh (np.ndarray): Vetor da função densidade volumétrica inicial f0(D) (µm⁻¹).
        m3_0 (float): Terceiro momento volumétrico inicial total M3(0) (µm³).
        d_max (float): Diâmetro máximo do domínio de partículas (µm).
    """

    def __init__(
        self,
        granulometry: Optional[RosinRammlerBennet] = None,
        kinetics: Optional[LeachingKinetics] = None,
        n_mesh_points: int = 1500,
        n_delta_points: int = 500,
        d_min: float = 0.01,
        d_max: float = 297.0,
    ) -> None:
        """Inicializa o resolvedor PBM com módulos físico-químicos e malha de cálculo.

        Args:
            granulometry: Instância de RosinRammlerBennet (padrão: parâmetros nominais de Bortot Coelho).
            kinetics: Instância de LeachingKinetics (padrão: parâmetros nominais de Bortot Coelho).
            n_mesh_points: Número de nós da malha de diâmetro para integração numérica (padrão: 1500).
            n_delta_points: Número de pontos para interpolação monótona delta -> X_Zn (padrão: 500).
            d_min: Diâmetro mínimo da malha (µm). Padrão: 0,01 µm.
            d_max: Diâmetro máximo da malha (µm), correspondente à peneira Tyler #50 (padrão: 297,0 µm).
        """
        self.granulometry = granulometry or RosinRammlerBennet()
        self.kinetics = kinetics or LeachingKinetics()
        self.d_max = float(d_max)
        self.d_min = float(d_min)

        # Geração da malha inicial de diâmetros e terceiro momento inicial M3(0)
        self.d_mesh, self.f0_mesh, self.m3_0 = self.granulometry.generate_mesh(
            d_min=self.d_min, d_max=self.d_max, n_points=n_mesh_points
        )

        # Pré-computação da curva monótona delta -> X_Zn para eficiência e estabilidade numérica
        self._build_conversion_interpolator(n_delta_points)

    def _build_conversion_interpolator(self, n_points: int) -> None:
        """Pré-computa o mapeamento delta -> X_Zn e constrói interpolador monótono PCHIP."""
        delta_grid = np.linspace(0.0, self.d_max, n_points)
        x_grid = np.zeros(n_points, dtype=np.float64)

        for i, d_val in enumerate(delta_grid):
            x_grid[i] = self._compute_conversion_raw(d_val)

        # Garantir monotonicidade estrita e limites físicos [0, 1]
        x_grid = np.clip(x_grid, 0.0, 1.0)
        self.delta_grid = delta_grid
        self.x_grid = x_grid
        self._interpolator = PchipInterpolator(delta_grid, x_grid)

    def _compute_conversion_raw(self, delta: float) -> float:
        """Calcula analítica/numericamente a conversão X_Zn a partir de um valor escalar de delta."""
        if delta <= 0.0:
            return 0.0
        if delta >= self.d_max:
            return 1.0

        mask = self.d_mesh >= delta
        if not np.any(mask):
            return 1.0

        d_sub = self.d_mesh[mask]
        f_sub = self.f0_mesh[mask]
        integrand = ((d_sub - delta) ** 3) * f_sub
        m3_delta = float(trapezoid(integrand, d_sub))
        conv = 1.0 - (m3_delta / self.m3_0)
        return float(np.clip(conv, 0.0, 1.0))

    def compute_conversion_from_delta(
        self, delta: Union[float, np.ndarray]
    ) -> Union[float, np.ndarray]:
        """Calcula a conversão mássica de zinco X_Zn para um dado deslocamento diametral acumulado delta.

        Args:
            delta: Deslocamento acumulado delta(t) em micrometros (µm).

        Returns:
            Fração mássica convertida de zinco X_Zn (0 a 1).
        """
        delta_arr = np.asarray(delta, dtype=np.float64)
        delta_clipped = np.clip(delta_arr, 0.0, self.d_max)
        x_val = self._interpolator(delta_clipped)

        if np.isscalar(delta):
            return float(x_val)
        return x_val

    def simulate(
        self,
        ca0: float,
        eta: float,
        t_eval: np.ndarray,
        alpha: Optional[float] = None,
        method: str = "RK45",
        rtol: float = 1e-6,
        atol: float = 1e-8,
    ) -> Dict[str, Any]:
        """Simula a dinâmica de dissolução batelada no tempo sob taxa de retração fenomenológica.

        Args:
            ca0: Concentração inicial de ácido livre (mol/L).
            eta: Razão molar estequiométrica H2SO4/ZnO (adimensional).
            t_eval: Vetor de tempos para avaliação das variáveis (min).
            alpha: Parâmetro empírico de amortecimento cinético (µm/min). Se None, usa alpha_nominal.
            method: Algoritmo de integração temporal do solve_ivp (padrão: "RK45").
            rtol: Tolerância relativa do solver EDO.
            atol: Tolerância absoluta do solver EDO.

        Returns:
            Dicionário com séries temporais:
                - "t": tempos de avaliação (min)
                - "delta": retração acumulada (µm)
                - "XZn": conversão mássica de zinco (-)
                - "CAf": concentração de ácido livre residual (mol/L)
                - "v": taxa de retração diametral dD/dt (µm/min)
                - "success": status de convergência do integrador
                - "message": mensagem de status
        """
        if ca0 <= 0.0:
            raise ValueError(f"CA0 deve ser positivo, recebido: {ca0}")
        if eta <= 0.0:
            raise ValueError(f"eta deve ser positivo, recebido: {eta}")

        alpha_eff = self.kinetics.alpha_nominal if alpha is None else float(alpha)
        t_arr = np.asarray(t_eval, dtype=np.float64)
        t_span = (float(t_arr[0]), float(t_arr[-1]))

        def ode_system(t: float, y: np.ndarray) -> list:
            delta_curr = max(0.0, float(y[0]))
            x_curr = float(self.compute_conversion_from_delta(delta_curr))
            caf_curr = self.kinetics.acid_concentration(ca0, x_curr, eta)
            v_curr = self.kinetics.shrinkage_rate(ca0, caf_curr, alpha_eff)
            # Como v <= 0 (retração), d(delta)/dt = |v| = -v >= 0
            return [-v_curr]

        sol = solve_ivp(
            fun=ode_system,
            t_span=t_span,
            y0=[0.0],
            t_eval=t_arr,
            method=method,
            rtol=rtol,
            atol=atol,
        )

        delta_sol = np.maximum(sol.y[0], 0.0)
        x_sol = np.array([self.compute_conversion_from_delta(d) for d in delta_sol])
        x_sol = np.clip(x_sol, 0.0, 1.0)
        caf_sol = np.array([self.kinetics.acid_concentration(ca0, x, eta) for x in x_sol])
        v_sol = np.array([self.kinetics.shrinkage_rate(ca0, c, alpha_eff) for c in caf_sol])

        return {
            "t": sol.t,
            "delta": delta_sol,
            "XZn": x_sol,
            "CAf": caf_sol,
            "v": v_sol,
            "success": sol.success,
            "message": sol.message,
        }

    def simulate_with_v_profile(
        self,
        t_eval: np.ndarray,
        v_profile: np.ndarray,
    ) -> Dict[str, Any]:
        """Simula a conversão X_Zn a partir de um perfil arbitrário de velocidades v(t).

        Método preparado para acoplamento híbrido (Fase 4/5), onde uma rede neural
        ou modelo de Machine Learning fornece a velocidade de retração v(t).

        Args:
            t_eval: Vetor de tempos (min).
            v_profile: Vetor de taxas de retração v(t) (µm/min), com v <= 0.

        Returns:
            Dicionário contendo "t", "delta", "XZn" e "v".
        """
        t_arr = np.asarray(t_eval, dtype=np.float64)
        v_arr = np.asarray(v_profile, dtype=np.float64)

        if len(t_arr) != len(v_arr):
            raise ValueError("t_eval e v_profile devem possuir o mesmo tamanho.")

        # Taxa de encolhimento não-negativa |v| = -v
        abs_v = np.abs(np.minimum(v_arr, 0.0))

        # Integração cumulativa trapezoidal para obter delta(t)
        delta_profile = np.zeros_like(t_arr)
        for i in range(1, len(t_arr)):
            delta_profile[i] = delta_profile[i - 1] + 0.5 * (abs_v[i] + abs_v[i - 1]) * (
                t_arr[i] - t_arr[i - 1]
            )

        x_profile = np.array([self.compute_conversion_from_delta(d) for d in delta_profile])
        x_profile = np.clip(x_profile, 0.0, 1.0)

        return {
            "t": t_arr,
            "delta": delta_profile,
            "XZn": x_profile,
            "v": v_arr,
        }
