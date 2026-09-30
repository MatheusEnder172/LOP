"""
Módulo de Cinética Química Heterogênea e Balanço Estequiométrico.
Implementa a velocidade de retração interfacial da partícula v(D) = dD/dt
e o balanço de consumo de reagente lixiviante em reatores batelada.

Referências:
- Bortot Coelho, F. E. (2017). Dissertação de Mestrado, PPGEM/UFMG, Equações 4.1, 4.2, 4.3, 3.51 e 5.3.
- Herbst, J. A. (1979). Rate Processes of Extractive Metallurgy. Plenum Press.
- Levenspiel, O. (2000). Engenharia das Reações Químicas, 3ª ed., Blucher.
"""

from typing import Literal, Union
import numpy as np


class LeachingKinetics:
    """Equacionamento cinético e estequiométrico da lixiviação ácida de zincita (ZnO).

    Governa a retração interfacial das partículas esféricas sob controle de
    reação química superficial e calcula o decaimento da acidez livre no licor.

    Atributos:
        ks (float): Constante cinética superficial intrínseca (µm/min). Padrão: 1,8e4 µm/min.
        alpha_nominal (float): Parâmetro empírico nominal de amortecimento da taxa (µm/min). Padrão: 5,5e3 µm/min.
        rho_s (float): Densidade molar de ZnO puro no mineral (mol/L). Padrão: 69,2 mol/L.
        mm_zno (float): Massa molar da zincita ZnO (g/mol). Padrão: 81,38 g/mol.
        t_zno_operacional (float): Teor operacional de ZnO considerado no carregamento da bancada (0,8138 g_ZnO/g_sólido, equivalente a 1 mol ZnO / 100 g sólido).
        t_zno_quimico (float): Teor de ZnO quantificado por digestão amoniacal (0,761 g_ZnO/g_sólido).
    """

    def __init__(
        self,
        ks: float = 18000.0,
        alpha_nominal: float = 5500.0,
        rho_s: float = 69.2,
        mm_zno: float = 81.38,
        t_zno_operacional: float = 0.8138,
        t_zno_quimico: float = 0.761,
    ) -> None:
        """Inicializa os parâmetros cinéticos e físico-químicos do sistema de lixiviação."""
        if ks <= 0.0:
            raise ValueError(f"ks deve ser estritamente positivo, recebido: {ks}")
        if alpha_nominal < 0.0:
            raise ValueError(f"alpha_nominal deve ser >= 0, recebido: {alpha_nominal}")
        if rho_s <= 0.0:
            raise ValueError(f"rho_s deve ser positivo, recebido: {rho_s}")
        if mm_zno <= 0.0:
            raise ValueError(f"mm_zno deve ser positivo, recebido: {mm_zno}")

        self.ks = float(ks)
        self.alpha_nominal = float(alpha_nominal)
        self.rho_s = float(rho_s)
        self.mm_zno = float(mm_zno)
        self.t_zno_operacional = float(t_zno_operacional)
        self.t_zno_quimico = float(t_zno_quimico)

    def calculate_eta(
        self,
        ca0: float,
        v_liq_l: float,
        mb0_g: float,
        basis: Literal["operational", "chemical"] = "operational"
    ) -> float:
        """Calcula a razão molar estequiométrica eta (H2SO4 / ZnO).

        eta = n_A0 / n_B0 = (V * CA0) / [ (m_B0 * T_ZnO) / MM_ZnO ]

        No planejamento de bancada de Bortot Coelho (2017), usou-se a base operacional:
        100 g de calcina = 1,0 mol de ZnO (T_ZnO / MM_ZnO = 0,01 mol/g => T_ZnO = 0,8138),
        o que resulta exatamente em: eta = (100 * V * CA0) / m_B0.

        Args:
            ca0: Concentração inicial de ácido sulfúrico (mol/L).
            v_liq_l: Volume de solução aquosa lixiviante (L).
            mb0_g: Massa de concentrado ustulado alimentada ao reator (g).
            basis: "operational" (padrão de bancada) ou "chemical" (teor via digestão).

        Returns:
            Razão molar estequiométrica eta (adimensional).
        """
        if ca0 <= 0.0:
            raise ValueError(f"ca0 deve ser positivo, recebido: {ca0}")
        if v_liq_l <= 0.0:
            raise ValueError(f"v_liq_l deve ser positivo, recebido: {v_liq_l}")
        if mb0_g <= 0.0:
            raise ValueError(f"mb0_g deve ser positivo, recebido: {mb0_g}")

        t_zno = self.t_zno_operacional if basis == "operational" else self.t_zno_quimico
        n_a0 = float(v_liq_l * ca0)
        n_b0 = float((mb0_g * t_zno) / self.mm_zno)

        return float(n_a0 / n_b0)

    def acid_concentration(
        self, ca0: float, x_zn: Union[float, np.ndarray], eta: float
    ) -> Union[float, np.ndarray]:
        """Calcula a concentração instantânea de ácido sulfúrico livre Caf(t).

        Modelo de consumo estequiométrico em batelada (Herbst, 1979):
        Caf(t) = CA0 * [ 1 - (X_Zn(t) / eta) ]

        Garante fisicamente que Caf >= 0 e X_Zn está limitado a [0, 1].

        Args:
            ca0: Concentração inicial de ácido sulfúrico (mol/L).
            x_zn: Conversão fracionária da zincita (escalar ou array numpy).
            eta: Razão molar estequiométrica inicial.

        Returns:
            Concentração residual de ácido livre Caf (mol/L).
        """
        if eta <= 0.0:
            raise ValueError(f"eta deve ser positivo, recebido: {eta}")

        x_clipped = np.clip(np.asarray(x_zn, dtype=np.float64), 0.0, 1.0)
        caf_val = ca0 * (1.0 - (x_clipped / eta))
        caf_pos = np.maximum(caf_val, 0.0)

        if np.isscalar(x_zn):
            return float(caf_pos)
        return caf_pos

    def dissolution_driving_force(
        self,
        ca0: float,
        caf: Union[float, np.ndarray],
        alpha: Union[float, np.ndarray, None] = None,
    ) -> Union[float, np.ndarray]:
        """Calcula a força motriz líquida de ataque químico superficial à partícula.

        F_motriz = ks * Caf - alpha * (CA0 - Caf)

        Args:
            ca0: Concentração inicial de ácido sulfúrico (mol/L).
            caf: Concentração instantânea de ácido sulfúrico no licor (mol/L).
            alpha: Parâmetro de retardamento (µm/min). Se None, usa o nominal.

        Returns:
            Força motriz líquida (µm·mol / (L·min)), truncada em zero se for negativa.
        """
        if alpha is None:
            alpha_val = self.alpha_nominal
        else:
            alpha_val = alpha

        caf_arr = np.maximum(np.asarray(caf, dtype=np.float64), 0.0)
        ca0_arr = float(ca0)

        termo_direto = self.ks * caf_arr
        termo_amortecimento = alpha_val * (ca0_arr - caf_arr)
        f_net = termo_direto - termo_amortecimento

        # Dissolução é irreversível: força motriz líquida cessa se for negativa
        f_pos = np.maximum(f_net, 0.0)

        if np.isscalar(caf):
            return float(f_pos)
        return f_pos

    def shrinkage_rate(
        self,
        ca0: float,
        caf: Union[float, np.ndarray],
        alpha: Union[float, np.ndarray, None] = None,
    ) -> Union[float, np.ndarray]:
        """Calcula a taxa de retração diametral da partícula v(D) = dD/dt.

        v(D) = - (2 / rho_s) * [ ks * Caf - alpha * (CA0 - Caf) ]

        Sob controle de reação superficial, v(D) independe do diâmetro instantâneo D.
        Como o sólido sofre dissolução (redução de tamanho), v(D) <= 0.

        Args:
            ca0: Concentração inicial de ácido sulfúrico (mol/L).
            caf: Concentração instantânea de ácido sulfúrico no licor (mol/L).
            alpha: Parâmetro de retardamento (µm/min). Se None, usa o nominal.

        Returns:
            Velocidade de retração dD/dt (µm/min). Sempre <= 0.
        """
        f_net = self.dissolution_driving_force(ca0=ca0, caf=caf, alpha=alpha)
        v_d = -(2.0 / self.rho_s) * f_net

        if np.isscalar(caf):
            return float(v_d)
        return v_d

    def dissolution_stopping_acid(
        self, ca0: float, alpha: Union[float, None] = None
    ) -> float:
        """Calcula a concentração residual de ácido Caf* na qual a taxa de lixiviação cessa (v = 0).

        ks * Caf* - alpha * (CA0 - Caf*) = 0  =>  Caf* = CA0 * [ alpha / (ks + alpha) ]

        Args:
            ca0: Concentração inicial de ácido sulfúrico (mol/L).
            alpha: Parâmetro de retardamento. Se None, usa o nominal.

        Returns:
            Concentração limite de ácido livre Caf* (mol/L).
        """
        alpha_val = self.alpha_nominal if alpha is None else float(alpha)
        fator = alpha_val / (self.ks + alpha_val)
        return float(ca0 * fator)

    def theoretical_max_conversion(
        self, eta: float, alpha: Union[float, None] = None
    ) -> float:
        """Calcula a conversão máxima assintótica teórica X_Zn_max(eta, alpha).

        Equação 5.3 da dissertação de Bortot Coelho (2017):
        X_max = eta * [ 1 - alpha / (ks + alpha) ], restrito a [0, 1].

        Args:
            eta: Razão molar estequiométrica (H2SO4 / ZnO).
            alpha: Parâmetro de retardamento. Se None, usa o nominal.

        Returns:
            Conversão máxima teórica esperada no patamar assintótico.
        """
        alpha_val = self.alpha_nominal if alpha is None else float(alpha)
        fator = 1.0 - (alpha_val / (self.ks + alpha_val))
        x_max = float(eta * fator)
        return float(np.clip(x_max, 0.0, 1.0))
