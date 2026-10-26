"""Treinador da MLP v2 (Subetapa 3.2.6): parada antecipada interna, perda ponderada e monotonia.

Reaproveita integralmente a rede `KineticsMLP` e o `MLPTrainer` da Subetapa 3.2.1 (que
continuam intactos, preservando a reprodutibilidade da v1) e acrescenta:

1. Parada antecipada guiada por ensaios internos (separados do treino da dobra), de modo que
   os ensaios de validação da dobra sejam usados só para dar a nota (Cawley; Talbot, 2010).
2. Pesos por amostra na perda em escala log1p (D1, Fase C).
3. Penalidade de monotonia temporal da taxa, mean(ReLU(∂ŷ_log/∂t)²), avaliada por autograd em
   pontos de colocação sorteados no domínio operacional (D2, Fase C; Raissi et al., 2019).
4. `KineticsMLPEnsemble`, que promedia a taxa de vários membros (Fase E).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn

SUBETAPA_DIR = Path(__file__).resolve().parent
MLP_V1_DIR = SUBETAPA_DIR.parent / "subetapa_3_2_1_mlp"
if str(MLP_V1_DIR) not in sys.path:
    sys.path.insert(0, str(MLP_V1_DIR))

from modelo_mlp import KineticsMLP, MLPTrainer, set_seed  # noqa: E402

# Domínio operacional dos 16 ensaios de bancada (C_A0 em mol/L, η adimensional, t em min)
DOMINIO_FISICO = np.array([[0.10, 1.50], [0.50, 3.10], [0.25, 15.0]])
# Malha temporal densa dos alvos (Etapa 2.1), usada para padronizar ln t
MALHA_T = np.arange(0.25, 15.0 + 1e-9, 0.25)


class KineticsMLPLogT(nn.Module):
    """KineticsMLP que recebe ln t no lugar de t (Fase B2).

    A entrada continua sendo o vetor padronizado [C_A0, η, t] do `scaler_X` (mesma interface do
    `SerialHybridModel`); internamente t é desfeito da padronização, levado a ln t e padronizado
    de novo com a média e o desvio de ln t na malha densa. Como ν cai várias ordens de grandeza
    nos primeiros minutos, ln t espalha melhor os instantes iniciais, onde ν é grande e define δ.
    A transformação é diferenciável, então a penalidade de monotonia em t continua válida.
    """

    def __init__(self, base: KineticsMLP, mu_t: float, sigma_t: float) -> None:
        super().__init__()
        self.base = base
        ln_t = np.log(MALHA_T)
        self.register_buffer("afim", torch.tensor([mu_t, sigma_t, ln_t.mean(), ln_t.std()], dtype=torch.float32))

    def _transformar(self, x: torch.Tensor) -> torch.Tensor:
        mu, sig, m, s = self.afim
        t = torch.clamp(x[:, 2:3] * sig + mu, min=1e-3)
        return torch.cat([x[:, :2], (torch.log(t) - m) / s], dim=1)

    def forward_log(self, x: torch.Tensor) -> torch.Tensor:
        return self.base.forward_log(self._transformar(x))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.expm1(self.forward_log(x))


class MLPTrainerV2(MLPTrainer):
    """Treinador com parada interna, pesos por amostra e penalidade de monotonia.

    Args:
        mono_lambda: Peso λ da penalidade de monotonia (0 desliga o termo D2).
        n_colocacao: Número de pontos de colocação sorteados por época para a penalidade.
        scaler_X: StandardScaler das entradas (necessário quando mono_lambda > 0).
        max_epochs: Número máximo de épocas.
        eta_min: Taxa de aprendizado final do CosineAnnealingLR.
        Demais argumentos: iguais aos de `MLPTrainer`.
    """

    def __init__(
        self,
        hidden_dims: List[int],
        mono_lambda: float = 0.0,
        n_colocacao: int = 256,
        scaler_X: Optional[object] = None,
        max_epochs: int = 350,
        eta_min: float = 1e-5,
        inicializacao: str = "padrao",
        entrada_log_t: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(hidden_dims=hidden_dims, **kwargs)
        self.mono_lambda = float(mono_lambda)
        self.n_colocacao = int(n_colocacao)
        self.scaler_X = scaler_X
        self.max_epochs = int(max_epochs)
        self.eta_min = float(eta_min)
        self.inicializacao = inicializacao
        self.entrada_log_t = bool(entrada_log_t)
        if (self.mono_lambda > 0.0 or self.entrada_log_t) and scaler_X is None:
            raise ValueError("scaler_X é obrigatório com mono_lambda > 0 ou entrada_log_t.")

    def build_model(self, seed_offset: int = 0) -> nn.Module:
        """Rede da v1, com inicialização de Glorot opcional e entrada em ln t opcional.

        "xavier": pesos das camadas lineares com a inicialização de Glorot e Bengio (2010), com o
        ganho recomendado para Tanh, e vieses nulos; "padrao": inicialização padrão do PyTorch.
        """
        model = super().build_model(seed_offset=seed_offset)
        if self.inicializacao == "xavier":
            ganho = nn.init.calculate_gain("tanh") if self.activation.upper() == "TANH" else 1.0
            for mod in model.modules():
                if isinstance(mod, nn.Linear):
                    nn.init.xavier_uniform_(mod.weight, gain=ganho)
                    nn.init.zeros_(mod.bias) if mod.bias is not None else None
        if self.entrada_log_t:
            model = KineticsMLPLogT(model, float(self.scaler_X.mean_[2]), float(self.scaler_X.scale_[2]))
        return model

    def _pontos_colocacao(self, gen: torch.Generator) -> torch.Tensor:
        """Sorteia pontos uniformes no domínio físico e os leva para a escala Z-score."""
        u = torch.rand(self.n_colocacao, 3, generator=gen, dtype=torch.float64).numpy()
        x_fis = DOMINIO_FISICO[:, 0] + u * (DOMINIO_FISICO[:, 1] - DOMINIO_FISICO[:, 0])
        x_s = self.scaler_X.transform(x_fis)
        return torch.tensor(x_s, dtype=torch.float32, requires_grad=True)

    @staticmethod
    def penalidade_monotonia(model: KineticsMLP, x_col: torch.Tensor) -> torch.Tensor:
        """mean(ReLU(∂ŷ_log/∂t_s)²): penaliza trechos em que a taxa cresce com o tempo.

        Como ln(1+ν) é monotônica em ν, o sinal de ∂ŷ_log/∂t é o mesmo de ∂ν/∂t; usar a
        escala log e o tempo padronizado deixa o termo adimensional.
        """
        y_log = model.forward_log(x_col)
        grad = torch.autograd.grad(y_log.sum(), x_col, create_graph=True)[0][:, 2]
        return torch.mean(torch.relu(grad) ** 2)

    def _perda_dados(
        self, model: KineticsMLP, x: torch.Tensor, y_log: torch.Tensor, w: torch.Tensor
    ) -> torch.Tensor:
        return torch.mean(w * (model.forward_log(x) - y_log) ** 2)

    def fit_parada_interna(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_es: np.ndarray,
        y_es: np.ndarray,
        w_train: Optional[np.ndarray] = None,
        w_es: Optional[np.ndarray] = None,
        seed_offset: int = 0,
    ) -> Tuple[KineticsMLP, Dict[str, List[float]]]:
        """Treina com parada antecipada guiada pelos ensaios internos (X_es, y_es).

        O critério de parada é a mesma perda de dados do treino (MSE ponderado em log1p),
        calculada nos ensaios internos, sem o termo de monotonia.
        """
        set_seed(self.seed + seed_offset)
        model = self.build_model(seed_offset=seed_offset)
        gen = torch.Generator().manual_seed(self.seed + seed_offset)

        w_train = np.ones(len(y_train)) if w_train is None else np.asarray(w_train, dtype=float)
        w_es = np.ones(len(y_es)) if w_es is None else np.asarray(w_es, dtype=float)

        ds = torch.utils.data.TensorDataset(
            torch.tensor(X_train, dtype=torch.float32),
            torch.tensor(np.log1p(y_train), dtype=torch.float32).view(-1, 1),
            torch.tensor(w_train, dtype=torch.float32).view(-1, 1),
        )
        loader = torch.utils.data.DataLoader(ds, batch_size=self.batch_size, shuffle=True, generator=gen)
        x_es = torch.tensor(X_es, dtype=torch.float32)
        y_es_log = torch.tensor(np.log1p(y_es), dtype=torch.float32).view(-1, 1)
        w_es_t = torch.tensor(w_es, dtype=torch.float32).view(-1, 1)

        opt = torch.optim.AdamW(model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=self.max_epochs, eta_min=self.eta_min)

        hist: Dict[str, List[float]] = {"train_loss": [], "es_loss": [], "mono_loss": [], "best_epoch": []}
        best_loss, best_state, best_ep, espera = float("inf"), None, self.max_epochs, 0

        for epoch in range(1, self.max_epochs + 1):
            model.train()
            soma, soma_mono, n = 0.0, 0.0, 0
            for xb, yb, wb in loader:
                opt.zero_grad()
                loss = self._perda_dados(model, xb, yb, wb)
                if self.mono_lambda > 0.0:
                    pen = self.penalidade_monotonia(model, self._pontos_colocacao(gen))
                    loss = loss + self.mono_lambda * pen
                    soma_mono += float(pen.item()) * len(xb)
                loss.backward()
                opt.step()
                soma += float(loss.item()) * len(xb)
                n += len(xb)
            hist["train_loss"].append(soma / n)
            hist["mono_loss"].append(soma_mono / n)

            model.eval()
            with torch.no_grad():
                es_loss = float(self._perda_dados(model, x_es, y_es_log, w_es_t).item())
            hist["es_loss"].append(es_loss)

            if es_loss < best_loss:
                best_loss, best_ep, espera = es_loss, epoch, 0
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            else:
                espera += 1
                if espera >= self.patience:
                    break
            sched.step()

        hist["best_epoch"] = [best_ep]
        if best_state is not None:
            model.load_state_dict(best_state)
        model.eval()
        return model, hist

    def fit_epocas_fixas(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        w_train: Optional[np.ndarray] = None,
        seed_offset: int = 0,
    ) -> Tuple[KineticsMLP, Dict[str, List[float]]]:
        """Treina por exatamente `max_epochs` épocas usando todos os ensaios recebidos.

        Alternativa à parada interna: nenhum ensaio é reservado para parar o treino, e o número
        de épocas passa a ser um hiperparâmetro escolhido pela validação cruzada (Goodfellow et al.,
        2016, seção 7.8). Os lotes são montados por indexação direta (mais rápido que o DataLoader).
        """
        set_seed(self.seed + seed_offset)
        model = self.build_model(seed_offset=seed_offset)
        gen = torch.Generator().manual_seed(self.seed + seed_offset)

        x = torch.tensor(X_train, dtype=torch.float32)
        y_log = torch.tensor(np.log1p(y_train), dtype=torch.float32).view(-1, 1)
        w = torch.ones_like(y_log) if w_train is None else torch.tensor(w_train, dtype=torch.float32).view(-1, 1)
        n = len(x)

        opt = torch.optim.AdamW(model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=self.max_epochs, eta_min=self.eta_min)
        hist: Dict[str, List[float]] = {"train_loss": [], "mono_loss": [], "best_epoch": [self.max_epochs]}

        model.train()
        for _ in range(self.max_epochs):
            perm = torch.randperm(n, generator=gen)
            soma, soma_mono = 0.0, 0.0
            for i in range(0, n, self.batch_size):
                idx = perm[i:i + self.batch_size]
                opt.zero_grad()
                loss = self._perda_dados(model, x[idx], y_log[idx], w[idx])
                if self.mono_lambda > 0.0:
                    pen = self.penalidade_monotonia(model, self._pontos_colocacao(gen))
                    loss = loss + self.mono_lambda * pen
                    soma_mono += float(pen.item()) * len(idx)
                loss.backward()
                opt.step()
                soma += float(loss.item()) * len(idx)
            hist["train_loss"].append(soma / n)
            hist["mono_loss"].append(soma_mono / n)
            sched.step()

        model.eval()
        return model, hist


class KineticsMLPEnsemble(nn.Module):
    """Média de vários `KineticsMLP` (Deep Ensemble; Lakshminarayanan et al., 2017).

    A média é feita na taxa física ν (µm/min). O nome da classe contém "MLP" para que o
    `SerialHybridModel` a reconheça como modelo do tipo "mlp" sem nenhuma alteração.
    """

    def __init__(self, membros: Sequence[KineticsMLP]) -> None:
        super().__init__()
        self.membros = nn.ModuleList(membros)

    def forward_membros(self, x: torch.Tensor) -> torch.Tensor:
        """Taxas de todos os membros, com formato (n_membros, N, 1)."""
        return torch.stack([m(x) for m in self.membros], dim=0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.forward_membros(x).mean(dim=0)

    def forward_log(self, x: torch.Tensor) -> torch.Tensor:
        return torch.log1p(self.forward(x))
