"""PBM diferenciável em PyTorch para o treino ponta a ponta do híbrido serial (Fase D, Subetapa 3.2.6).

Replica, em `torch`, o caminho numérico do `SerialHybridModel.simulate` nos instantes experimentais:

1. a taxa ν(t) = max(0, rede) é lida na malha canônica de 0,25 a 15 min (60 nós, Δt = 0,25 min);
2. δ(t₁) = ν(t₁)·t₁ (condição inicial δ(0) = 0) e, depois, trapézio acumulado;
3. X_raw = Hermite cúbica por partes com os nós e as inclinações da PCHIP do `BatchPBMSolver`
   (δ truncado em [0, d_max]);
4. X(0) = 0, máximo acumulado e teto estequiométrico X ≤ min(1, η);
5. leitura nos instantes experimentais (0,5; 1; 2; 3; 4; 5 e 15 min, que coincidem com nós da malha).

Todo o cálculo é feito em float64. Os gradientes passam por ν → δ → X (Psichogios; Ungar, 1992;
Thompson; Kramer, 1994). O teste `test_fases_c_d.py` confere a equivalência com o `SerialHybridModel`
(diferença menor que 1e-6).
"""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import torch

from src.physics.pbm_batch import BatchPBMSolver

T_MALHA = np.linspace(0.25, 15.0, 60, dtype=np.float64)
T_OBS = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0], dtype=np.float64)


class PBMTorch:
    """Acoplamento ν → δ → X_Zn diferenciável (equivalente ao `SerialHybridModel` em t_obs).

    Args:
        solver: `BatchPBMSolver` cuja curva PCHIP δ → X é copiada (nós e coeficientes).
        t_malha: Malha canônica de tempos (min), crescente, com t₁ > 0.
        t_obs: Instantes de leitura (min); precisam ser nós da malha.
    """

    def __init__(self, solver: BatchPBMSolver, t_malha: np.ndarray = T_MALHA, t_obs: np.ndarray = T_OBS) -> None:
        self.t_malha = np.asarray(t_malha, dtype=np.float64)
        self.t_obs = np.asarray(t_obs, dtype=np.float64)
        idx = [int(np.argmin(np.abs(self.t_malha - t))) for t in self.t_obs]
        if not np.allclose(self.t_malha[idx], self.t_obs, atol=1e-9):
            raise ValueError("Os instantes de leitura precisam ser nós da malha canônica.")
        self.idx_obs = torch.tensor(idx, dtype=torch.long)
        self.dt = torch.tensor(np.diff(self.t_malha), dtype=torch.float64)
        self.t1 = float(self.t_malha[0])
        pchip = solver._interpolator
        self.nos = torch.tensor(pchip.x, dtype=torch.float64)
        self.coef = torch.tensor(pchip.c, dtype=torch.float64)  # (4, n-1): c0·dx³ + c1·dx² + c2·dx + c3
        self.d_max = float(solver.d_max)

    def delta(self, nu: torch.Tensor) -> torch.Tensor:
        """δ(t) na malha, a partir de ν com formato (..., n_malha) (µm/min → µm)."""
        d1 = nu[..., :1] * self.t1
        inc = 0.5 * (nu[..., 1:] + nu[..., :-1]) * self.dt
        return torch.cat([d1, d1 + torch.cumsum(inc, dim=-1)], dim=-1)

    def conversao_bruta(self, delta: torch.Tensor) -> torch.Tensor:
        """X(δ) pela PCHIP do solver (diferenciável por partes)."""
        d = torch.clamp(delta, 0.0, self.d_max)
        i = torch.clamp(torch.bucketize(d, self.nos, right=True) - 1, 0, len(self.nos) - 2)
        dx = d - self.nos[i]
        c = self.coef[:, i]
        return ((c[0] * dx + c[1]) * dx + c[2]) * dx + c[3]

    def forward(self, nu: torch.Tensor, eta: torch.Tensor) -> torch.Tensor:
        """X_Zn nos instantes de `t_obs`.

        Args:
            nu: Taxas ν ≥ 0 (µm/min), formato (B, n_malha).
            eta: Razão molar η de cada ensaio, formato (B,).

        Returns:
            Tensor (B, n_obs) com X_Zn, respeitando X(0) = 0, monotonia e X ≤ min(1, η).
        """
        nu = nu.to(torch.float64)
        x_raw = self.conversao_bruta(self.delta(nu))
        x_full = torch.cat([torch.zeros_like(x_raw[..., :1]), x_raw], dim=-1)
        x_mono = torch.cummax(x_full, dim=-1).values
        teto = torch.clamp(eta.to(torch.float64), max=1.0).unsqueeze(-1)
        x = torch.minimum(torch.clamp(x_mono, min=0.0), teto)
        return x[..., self.idx_obs + 1]

    __call__ = forward


def montar_lote(
    scaler_X, meta: "pd.DataFrame", ensaios: Sequence[int], t_malha: np.ndarray = T_MALHA
) -> tuple:
    """Entradas padronizadas (E, n_malha, 3) e η (E,) dos ensaios, para a rede e o PBM."""
    linhas, etas = [], []
    for e in ensaios:
        m = meta[meta["ensaio"] == e].iloc[0]
        bruto = np.column_stack([np.full(len(t_malha), m["CA0_mol_L"]), np.full(len(t_malha), m["razao_molar_eta"]), t_malha])
        linhas.append(scaler_X.transform(bruto))
        etas.append(float(m["razao_molar_eta"]))
    return torch.tensor(np.stack(linhas), dtype=torch.float32), torch.tensor(etas, dtype=torch.float64)


def nu_da_rede(model: torch.nn.Module, x_lote: torch.Tensor) -> torch.Tensor:
    """ν = max(0, rede) para um lote (E, n_malha, 3); mesma regra do `SerialHybridModel.predict_rate`."""
    e, n, f = x_lote.shape
    return torch.clamp(model(x_lote.reshape(e * n, f)).reshape(e, n), min=0.0)
