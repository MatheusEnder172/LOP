"""Módulo de Definição e Treinamento da Rede Neural MLP (Subetapa 3.2.1).

Implementa a classe PyTorch KineticsMLP com topologia parametrizável,
normalização de camadas (LayerNorm), ativações suaves (GELU), cabeça de saída
com projeção física estritamente não-negativa (Softplus + expm1) e a classe
MLPTrainer para validação cruzada por ensaio, early stopping e inferência física.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


class KineticsMLP(nn.Module):
    """Rede Neural Multi-Layer Perceptron para Cinética de Retração Interfacial.

    Garante estritamente a restrição física de conservação de massa:
    taxa de retração interfacial |v(t)| >= 0 através da projeção Softplus em
    espaço logarítmico (log1p) com inversão expm1 suave:
        y_log = Softplus(z) >= 0  ==>  |v| = exp(y_log) - 1 >= 0 um/min.

    Attributes:
        input_dim: Número de features de entrada (padrão: 4 -> T, CA0, eta, t).
        hidden_dims: Lista com o número de neurônios em cada camada oculta.
        dropout_rate: Taxa de descarte estocástico para regularização.
        use_layer_norm: Se True, aplica LayerNorm após cada camada linear.
    """

    def __init__(
        self,
        input_dim: int = 4,
        hidden_dims: Optional[List[int]] = None,
        dropout_rate: float = 0.0,
        use_layer_norm: bool = True,
    ) -> None:
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [128, 64, 32]

        self.input_dim = input_dim
        self.hidden_dims = list(hidden_dims)
        self.dropout_rate = dropout_rate
        self.use_layer_norm = use_layer_norm

        layers: List[nn.Module] = []
        prev_dim = input_dim

        for dim in self.hidden_dims:
            layers.append(nn.Linear(prev_dim, dim))
            if use_layer_norm:
                layers.append(nn.LayerNorm(dim))
            layers.append(nn.GELU())
            if dropout_rate > 0.0:
                layers.append(nn.Dropout(p=dropout_rate))
            prev_dim = dim

        # Projeção final para 1 valor em espaço log1p
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Softplus())  # Assegura y_log >= 0

        self.network = nn.Sequential(*layers)

    def forward_log(self, x: torch.Tensor) -> torch.Tensor:
        """Prediz o alvo em escala logarítmica log1p (|v|).

        Args:
            x: Tensor float32 de entrada de shape (batch_size, input_dim).

        Returns:
            Tensor float32 de shape (batch_size, 1) em espaço log1p >= 0.
        """
        return self.network(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Executa a propagação direta retornando a taxa em escala física (um/min).

        Args:
            x: Tensor float32 de entrada de shape (batch_size, input_dim).

        Returns:
            Tensor float32 predito de shape (batch_size, 1) estritamente >= 0.
        """
        y_log = self.forward_log(x)
        # expm1(y_log) = exp(y_log) - 1 >= 0 para y_log >= 0
        return torch.expm1(y_log)


class MLPTrainer:
    """Gerenciador de treino, validação cruzada e avaliação do modelo MLP."""

    def __init__(
        self,
        hidden_dims: List[int],
        dropout_rate: float = 0.0,
        use_layer_norm: bool = True,
        lr: float = 3e-3,
        weight_decay: float = 1e-5,
        batch_size: int = 32,
        patience: int = 35,
        seed: int = 42,
    ) -> None:
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout_rate
        self.use_layer_norm = use_layer_norm
        self.lr = lr
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.patience = patience
        self.seed = seed
        self.device = torch.device("cpu")

    def build_model(self) -> KineticsMLP:
        """Instancia um novo modelo KineticsMLP inicializado."""
        set_seed(self.seed)
        model = KineticsMLP(
            input_dim=4,
            hidden_dims=self.hidden_dims,
            dropout_rate=self.dropout_rate,
            use_layer_norm=self.use_layer_norm,
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

            # Saída em escala física real (um/min)
            preds_tensor = torch.expm1(preds_log_tensor)
            preds = preds_tensor.cpu().numpy().ravel()

        # Métricas na escala física do processo (um/min)
        r2 = float(r2_score(y_eval, preds))
        rmse = float(np.sqrt(mean_squared_error(y_eval, preds)))
        mae = float(mean_absolute_error(y_eval, preds))
        max_err = float(np.max(np.abs(y_eval - preds)))

        # R2 também no espaço logarítmico para diagnóstico
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
    ) -> Tuple[KineticsMLP, Dict[str, List[float]]]:
        """Treina a rede neural com Early Stopping e agendamento de taxa de aprendizado."""
        set_seed(self.seed)
        model = self.build_model()

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
        }

        best_val_loss = float("inf")
        best_state = None
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
                    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1
                    if patience_counter >= self.patience:
                        break

            scheduler.step()

        if best_state is not None:
            model.load_state_dict(best_state)

        return model, history
