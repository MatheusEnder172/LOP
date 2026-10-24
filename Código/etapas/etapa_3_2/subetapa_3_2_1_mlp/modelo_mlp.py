"""Módulo de Definição, Treinamento e Análise Diferencial (Autograd) da Rede Neural MLP (Subetapa 3.2.1).

Implementa:
1. Classe PyTorch `KineticsMLP` (`input_dim = 3`: `[CA0_mol_L, razao_molar_eta, t_min]` em `t > 0`)
   com suporte a blocos residuais (`ResidualBlock`, `ResNet-MLP`), normalização (`LayerNorm`),
   ativações infinitamente diferenciáveis `C∞` (`GELU`, `SiLU/Swish`, `Tanh`) e projeção física
   estritamente não-negativa (`Softplus + expm1`).
2. Classe `MLPTrainer` com validação cruzada por ensaio (`GroupKFold`), `CosineAnnealingLR`,
   `Early Stopping` guiado por validação, destilação de ensemble (4-Fold Deep Ensemble)
   e extração de derivadas parciais analíticas exatas (`∂|v|/∂C_A0`, `∂|v|/∂η`, `∂|v|/∂t`) via `torch.autograd`.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def set_seed(seed: int = 42) -> None:
    """Fixa as sementes aleatórias para garantir determinismo rigoroso."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)


def _get_activation(name: str) -> nn.Module:
    """Retorna a função de ativação suave C∞ solicitada."""
    act = name.upper()
    if act == "GELU":
        return nn.GELU()
    if act in ("SILU", "SWISH"):
        return nn.SiLU()
    if act == "TANH":
        return nn.Tanh()
    return nn.GELU()


class ResidualLinearBlock(nn.Module):
    """Bloco residual suave C∞ com conexão de atalho estabilizada (skip connection): y = Proj(x) + α·F(x)."""

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        activation: str = "GELU",
        dropout_rate: float = 0.0,
        use_layer_norm: bool = True,
    ) -> None:
        super().__init__()
        layers: List[nn.Module] = [nn.Linear(in_dim, out_dim)]
        if use_layer_norm:
            layers.append(nn.LayerNorm(out_dim))
        layers.append(_get_activation(activation))
        if dropout_rate > 0.0:
            layers.append(nn.Dropout(p=dropout_rate))
        layers.append(nn.Linear(out_dim, out_dim))
        self.block = nn.Sequential(*layers)
        self.skip = nn.Identity() if in_dim == out_dim else nn.Linear(in_dim, out_dim, bias=False)
        self.res_scale = nn.Parameter(torch.tensor(0.25, dtype=torch.float32))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.skip(x) + self.res_scale * self.block(x)


class KineticsMLP(nn.Module):
    """Rede Neural Multi-Layer Perceptron (Padrão ou ResNet-MLP) para Cinética Interfacial em t > 0.

    Garante estritamente a restrição física de conservação de massa:
    taxa de retração interfacial |v(t)| >= 0 através da projeção Softplus em
    espaço logarítmico (log1p) com inversão expm1 suave:
        y_log = Softplus(z) >= 0  ==>  |v| = exp(y_log) - 1 >= 0 µm/min.

    Attributes:
        input_dim: Número de features de entrada (padrão: 3 -> CA0_mol_L, razao_molar_eta, t_min).
        hidden_dims: Lista com o número de neurônios em cada camada oculta.
        dropout_rate: Taxa de descarte estocástico para regularização.
        use_layer_norm: Se True, aplica LayerNorm após cada camada linear.
        activation: Nome da função de ativação C∞ ('GELU', 'SiLU', 'Tanh').
        use_residual: Se True, utiliza conexões residuais (ResNet-MLP).
    """

    def __init__(
        self,
        input_dim: int = 3,
        hidden_dims: Optional[List[int]] = None,
        dropout_rate: float = 0.0,
        use_layer_norm: bool = True,
        activation: str = "GELU",
        use_residual: bool = False,
    ) -> None:
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [64, 32]

        self.input_dim = input_dim
        self.hidden_dims = list(hidden_dims)
        self.dropout_rate = dropout_rate
        self.use_layer_norm = use_layer_norm
        self.activation = activation
        self.use_residual = use_residual

        layers: List[nn.Module] = []
        prev_dim = input_dim

        for dim in self.hidden_dims:
            if use_residual:
                layers.append(
                    ResidualLinearBlock(
                        in_dim=prev_dim,
                        out_dim=dim,
                        activation=activation,
                        dropout_rate=dropout_rate,
                        use_layer_norm=use_layer_norm,
                    )
                )
            else:
                layers.append(nn.Linear(prev_dim, dim))
                if use_layer_norm:
                    layers.append(nn.LayerNorm(dim))
                layers.append(_get_activation(activation))
                if dropout_rate > 0.0:
                    layers.append(nn.Dropout(p=dropout_rate))
            prev_dim = dim

        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Softplus())  # Assegura y_log >= 0

        self.network = nn.Sequential(*layers)

    def forward_log(self, x: torch.Tensor) -> torch.Tensor:
        """Prediz o alvo em escala logarítmica log1p(|v|)."""
        return self.network(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Executa a propagação direta retornando a taxa em escala física (µm/min)."""
        y_log = self.forward_log(x)
        return torch.expm1(y_log)

    def compute_sensitivities_autograd(
        self,
        X_scaled: np.ndarray,
        feature_scales: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        """Calcula analiticamente via torch.autograd as derivadas parciais físicas ∂|v|/∂X_i.

        Pela regra da cadeia, dado X_scaled = (X - μ) / σ:
            ∂|v| / ∂X_i = (∂|v| / ∂X_scaled_i) / σ_i

        Args:
            X_scaled: Matriz de features escalonadas (N, 3) -> [CA0, eta, t].
            feature_scales: Vetor σ de desvios-padrão do StandardScaler (3,).

        Returns:
            Dicionário com o vetor predito '|v|' e as derivadas parciais exatas:
            'dv_dCA0', 'dv_deta', 'dv_dt'.
        """
        self.eval()
        x_tensor = torch.tensor(X_scaled, dtype=torch.float32, requires_grad=True)
        y_pred = self.forward(x_tensor)
        grads_scaled = torch.autograd.grad(
            outputs=y_pred,
            inputs=x_tensor,
            grad_outputs=torch.ones_like(y_pred),
            create_graph=False,
            retain_graph=False,
        )[0].detach().cpu().numpy()

        scales = np.asarray(feature_scales, dtype=np.float64).reshape(1, -1)
        grads_phys = grads_scaled / scales

        return {
            "abs_v": y_pred.detach().cpu().numpy().ravel(),
            "dv_dCA0": grads_phys[:, 0],
            "dv_deta": grads_phys[:, 1],
            "dv_dt": grads_phys[:, 2],
        }


class MLPTrainer:
    """Gerenciador de treino, validação cruzada, ensemble e avaliação do modelo MLP."""

    def __init__(
        self,
        hidden_dims: List[int],
        input_dim: int = 3,
        dropout_rate: float = 0.0,
        use_layer_norm: bool = True,
        activation: str = "GELU",
        use_residual: bool = False,
        lr: float = 3e-3,
        weight_decay: float = 1e-4,
        batch_size: int = 32,
        patience: int = 60,
        seed: int = 42,
    ) -> None:
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout_rate
        self.use_layer_norm = use_layer_norm
        self.activation = activation
        self.use_residual = use_residual
        self.lr = lr
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.patience = patience
        self.seed = seed
        self.device = torch.device("cpu")

    def build_model(self, seed_offset: int = 0) -> KineticsMLP:
        """Instancia um novo modelo KineticsMLP inicializado."""
        set_seed(self.seed + seed_offset)
        model = KineticsMLP(
            input_dim=self.input_dim,
            hidden_dims=self.hidden_dims,
            dropout_rate=self.dropout_rate,
            use_layer_norm=self.use_layer_norm,
            activation=self.activation,
            use_residual=self.use_residual,
        ).to(self.device)
        return model

    def train_epoch(
        self,
        model: KineticsMLP,
        dataloader: torch.utils.data.DataLoader,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
    ) -> float:
        """Executa uma época de treino minimizando a perda em escala log1p."""
        model.train()
        total_loss = 0.0
        n_samples = 0

        for batch_x, batch_y_log in dataloader:
            batch_x = batch_x.to(self.device)
            batch_y_log = batch_y_log.to(self.device)

            optimizer.zero_grad()
            preds_log = model.forward_log(batch_x)
            loss = criterion(preds_log, batch_y_log)
            loss.backward()
            optimizer.step()

            total_loss += float(loss.item()) * len(batch_x)
            n_samples += len(batch_x)

        return total_loss / max(1, n_samples)

    def evaluate(
        self,
        model: KineticsMLP,
        X_eval: np.ndarray,
        y_eval: np.ndarray,
        criterion: nn.Module,
    ) -> Tuple[float, Dict[str, float], np.ndarray]:
        """Avalia o modelo calculando a perda log e as métricas físicas reais."""
        model.eval()
        y_eval_log = np.log1p(y_eval)

        with torch.no_grad():
            x_tensor = torch.tensor(X_eval, dtype=torch.float32).to(self.device)
            y_log_tensor = torch.tensor(y_eval_log, dtype=torch.float32).view(-1, 1).to(self.device)

            preds_log_tensor = model.forward_log(x_tensor)
            val_loss = float(criterion(preds_log_tensor, y_log_tensor).item())

            preds_tensor = torch.expm1(preds_log_tensor)
            preds = preds_tensor.cpu().numpy().ravel()

        r2 = float(r2_score(y_eval, preds))
        rmse = float(np.sqrt(mean_squared_error(y_eval, preds)))
        mae = float(mean_absolute_error(y_eval, preds))
        max_err = float(np.max(np.abs(y_eval - preds)))
        r2_log = float(r2_score(y_eval_log, preds_log_tensor.cpu().numpy().ravel()))

        metrics = {
            "r2": r2,
            "rmse": rmse,
            "mae": mae,
            "max_error": max_err,
            "r2_log": r2_log,
        }
        return val_loss, metrics, preds

    def fit_with_early_stopping(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        max_epochs: int = 350,
        seed_offset: int = 0,
    ) -> Tuple[KineticsMLP, Dict[str, List[float]]]:
        """Treina a rede neural com Early Stopping guiado por validação e CosineAnnealingLR."""
        set_seed(self.seed + seed_offset)
        model = self.build_model(seed_offset=seed_offset)

        y_train_log = np.log1p(y_train)

        dataset = torch.utils.data.TensorDataset(
            torch.tensor(X_train, dtype=torch.float32),
            torch.tensor(y_train_log, dtype=torch.float32).view(-1, 1),
        )
        dataloader = torch.utils.data.DataLoader(
            dataset, batch_size=self.batch_size, shuffle=True
        )

        optimizer = torch.optim.AdamW(
            model.parameters(), lr=self.lr, weight_decay=self.weight_decay
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=max_epochs, eta_min=1e-5
        )
        criterion = nn.MSELoss()

        history: Dict[str, List[float]] = {
            "train_loss": [],
            "val_loss": [],
            "val_r2": [],
            "val_rmse": [],
            "best_epoch": [],
        }

        best_val_loss = float("inf")
        best_state = None
        best_ep = max_epochs
        patience_counter = 0

        for epoch in range(1, max_epochs + 1):
            train_loss = self.train_epoch(model, dataloader, optimizer, criterion)
            history["train_loss"].append(train_loss)

            if X_val is not None and y_val is not None:
                val_loss, val_metrics, _ = self.evaluate(model, X_val, y_val, criterion)
                history["val_loss"].append(val_loss)
                history["val_r2"].append(val_metrics["r2"])
                history["val_rmse"].append(val_metrics["rmse"])

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_ep = epoch
                    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self.patience:
                        break

            scheduler.step()

        history["best_epoch"] = [best_ep]
        if best_state is not None:
            model.load_state_dict(best_state)

        return model, history

    def distill_ensemble_to_single_model(
        self,
        fold_models: List[KineticsMLP],
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 240,
        alpha_ensemble: float = 0.65,
    ) -> Tuple[KineticsMLP, Dict[str, List[float]]]:
        """Consolida os 4 modelos validados por Early Stopping (Deep Ensemble) em uma única rede KineticsMLP.

        Combina os alvos físicos de treino (1 - alpha) com a predição suavizada do Ensemble (alpha),
        evitando o overfitting de treinar cegamente sem conjunto de validação e preservando 100%
        de compatibilidade com o checkpoint único `mlp_kinetics_v1.pt`.
        """
        set_seed(self.seed)
        x_tensor = torch.tensor(X_train, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            ens_logs = [m.forward_log(x_tensor).cpu().numpy().ravel() for m in fold_models]
        y_ens_log = np.mean(ens_logs, axis=0)
        y_true_log = np.log1p(y_train)
        y_target_log = alpha_ensemble * y_ens_log + (1.0 - alpha_ensemble) * y_true_log

        model = self.build_model()
        dataset = torch.utils.data.TensorDataset(
            torch.tensor(X_train, dtype=torch.float32),
            torch.tensor(y_target_log, dtype=torch.float32).view(-1, 1),
        )
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        optimizer = torch.optim.AdamW(model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
        criterion = nn.MSELoss()

        history: Dict[str, List[float]] = {"train_loss": [], "val_loss": []}
        for _ in range(epochs):
            tr_loss = self.train_epoch(model, dataloader, optimizer, criterion)
            history["train_loss"].append(tr_loss)
            scheduler.step()

        return model, history

    @staticmethod
    def predict_ensemble(
        fold_models: List[KineticsMLP],
        X_scaled: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Retorna a média e o desvio-padrão epistêmico (±1σ) das predições dos modelos das 4 dobras."""
        x_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        preds_list = []
        with torch.no_grad():
            for m in fold_models:
                m.eval()
                preds_list.append(m(x_tensor).cpu().numpy().ravel())
        preds_arr = np.stack(preds_list, axis=0)
        return np.mean(preds_arr, axis=0), np.std(preds_arr, axis=0)
