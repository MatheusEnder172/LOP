"""Protocolo comum de validação da Subetapa 3.2.6 (usado em todas as fases A–E).

Regras do protocolo:
1. O teste cego (ensaios 7, 8 e 14) não entra em nenhuma fase de seleção; é usado uma única vez,
   na Fase E (evita vazamento de informação na seleção; Kapoor; Narayanan, 2023).
2. As 4 dobras por ensaio (GroupKFold) da Etapa 3.1 são mantidas (Roberts et al., 2017).
3. Em cada dobra, 2 ensaios do próprio treino (sorteio fixo por dobra e semente, sem os vértices
   do planejamento) servem só para a parada antecipada; os ensaios de validação da dobra dão a nota
   (remove o viés otimista de selecionar e avaliar no mesmo conjunto; Cawley; Talbot, 2010).
4. Cada configuração é treinada com várias sementes.
5. Métrica principal: RMSE de X_Zn nos pontos experimentais t > 0 dos ensaios de validação,
   obtido passando a taxa prevista pelo PBM (`SerialHybridModel`), agrupado nas 4 dobras
   (91 pontos) e promediado entre as sementes.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parents[2]
BASE_DIR = CODIGO_DIR.parent
for p in (SUBETAPA_DIR, CODIGO_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from modelo_mlp_v2 import KineticsMLP, MLPTrainer, MLPTrainerV2  # noqa: E402
from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

SPLITS_DIR = BASE_DIR / "Base de dados" / "processed" / "splits"
RAW_DIR = BASE_DIR / "Base de dados" / "raw"
OUTPUTS_DIR = CODIGO_DIR / "outputs" / "etapa_3_2" / "subetapa_3_2_6_mlp_otimizacao"

FEATURES = ["CA0_mol_L", "razao_molar_eta", "t_min"]
TARGET = "abs_v_alvo_um_min"
ENSAIOS_TESTE = [7, 8, 14]
# Vértices do planejamento (C_A0, η) = (0,1; 0,5), (0,1; 3,1), (1,5; 0,5), (1,5; 3,1):
# nunca são retirados do treino para a parada interna, para não forçar extrapolação.
VERTICES = [1, 2, 5, 16]
SEMENTES_PADRAO = (42, 43, 44)

# Configuração da MLP-B v1 (Subetapa 3.2.1), ponto de partida da Fase A
CONFIG_V1: Dict[str, Any] = {
    "hidden_dims": [64, 32],
    "activation": "GELU",
    "use_layer_norm": True,
    "dropout_rate": 0.0,
    "lr": 3e-3,
    "weight_decay": 1e-4,
    "batch_size": 32,
    "patience": 60,
    "max_epochs": 350,
    "mono_lambda": 0.0,
}


@dataclass
class Dados:
    """Conjunto de dados e objetos compartilhados pelas fases."""

    train_df: pd.DataFrame
    test_df: pd.DataFrame
    folds: List[Dict[str, Any]]
    scaler_X: Any
    exp_df: pd.DataFrame  # pontos experimentais t > 0 dos 16 ensaios
    meta: pd.DataFrame  # C_A0 e η de cada ensaio
    solver: BatchPBMSolver
    X_train_s: np.ndarray = field(init=False)
    y_train: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.X_train_s = self.scaler_X.transform(self.train_df[FEATURES].values)
        self.y_train = self.train_df[TARGET].values

    def mascara(self, ensaios: Sequence[int]) -> np.ndarray:
        return self.train_df["ensaio"].isin(list(ensaios)).values


def carregar_dados() -> Dados:
    """Lê as partições da Etapa 3.1, os pontos experimentais e monta o solver PBM uma vez."""
    train_df = pd.read_csv(SPLITS_DIR / "train_dense.csv")
    test_df = pd.read_csv(SPLITS_DIR / "test_dense.csv")
    with open(SPLITS_DIR / "cv_folds_info.json", "r", encoding="utf-8") as f:
        folds = json.load(f)
    scaler_X = joblib.load(SPLITS_DIR / "scalers.joblib")["scaler_X"]
    serie = pd.read_csv(RAW_DIR / "cinetica_batelada_A1_4.csv")
    exp_df = serie[serie["t_min"] > 0.0].sort_values(["ensaio", "t_min"]).reset_index(drop=True)
    meta = pd.read_csv(RAW_DIR / "bancada_batelada_A1_1.csv")[["ensaio", "CA0_mol_L", "razao_molar_eta"]]
    assert not set(ENSAIOS_TESTE) & set(train_df["ensaio"]), "Ensaio de teste presente no treino."
    return Dados(train_df, test_df, folds, scaler_X, exp_df, meta, BatchPBMSolver())


def ensaios_parada_interna(ensaios_treino: Sequence[int], fold: int, seed: int, n: int = 2) -> List[int]:
    """Sorteio fixo (por dobra e semente) dos ensaios internos de parada antecipada."""
    candidatos = sorted(e for e in ensaios_treino if e not in VERTICES)
    rng = np.random.default_rng(1000 * seed + fold)
    return sorted(int(e) for e in rng.choice(candidatos, size=n, replace=False))


def simular_X(model: torch.nn.Module, dados: Dados, ensaios: Sequence[int], t_eval: Optional[np.ndarray] = None) -> pd.DataFrame:
    """Passa a taxa prevista pelo PBM e devolve X_Zn nos tempos experimentais (ou em t_eval)."""
    model.eval()
    hib = SerialHybridModel(ddm_model=model, scaler_X=dados.scaler_X, solver=dados.solver)
    linhas = []
    for e in ensaios:
        m = dados.meta[dados.meta["ensaio"] == e].iloc[0]
        exp = dados.exp_df[dados.exp_df["ensaio"] == e]
        tt = exp["t_min"].values if t_eval is None else np.asarray(t_eval, dtype=float)
        res = hib.simulate(ca0=float(m["CA0_mol_L"]), eta=float(m["razao_molar_eta"]), t_eval=tt)
        df = pd.DataFrame({"ensaio": e, "t_min": tt, "XZn_pred": res["XZn"], "abs_v_pred": res["abs_v"]})
        if t_eval is None:
            df["XZn_exp"] = exp["XZn"].values
        linhas.append(df)
    return pd.concat(linhas, ignore_index=True)


def metricas(y: np.ndarray, p: np.ndarray) -> Dict[str, float]:
    return {
        "R2": float(r2_score(y, p)),
        "RMSE": float(np.sqrt(mean_squared_error(y, p))),
        "MAE": float(mean_absolute_error(y, p)),
    }


def metricas_nu(model: KineticsMLP, X_s: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """R², R²_log, RMSE e MAE da taxa ν (mesmas definições da Subetapa 3.2.1)."""
    _, m, _ = MLPTrainer([1]).evaluate(model, X_s, y, torch.nn.MSELoss())
    return {"R2_nu": m["r2"], "R2_log_nu": m["r2_log"], "RMSE_nu": m["rmse"], "MAE_nu": m["mae"]}


def criar_trainer(config: Dict[str, Any], dados: Dados, seed: int) -> MLPTrainerV2:
    return MLPTrainerV2(
        hidden_dims=list(config["hidden_dims"]),
        activation=config["activation"],
        use_layer_norm=bool(config["use_layer_norm"]),
        dropout_rate=float(config["dropout_rate"]),
        lr=float(config["lr"]),
        weight_decay=float(config["weight_decay"]),
        batch_size=int(config["batch_size"]),
        patience=int(config["patience"]),
        max_epochs=int(config["max_epochs"]),
        mono_lambda=float(config.get("mono_lambda", 0.0)),
        scaler_X=dados.scaler_X,
        input_dim=3,
        use_residual=bool(config.get("use_residual", False)),
        inicializacao=config.get("inicializacao", "padrao"),
        entrada_log_t=bool(config.get("entrada_log_t", False)),
        seed=seed,
    )


@dataclass
class ResultadoCV:
    """Resultado de uma configuração no protocolo comum."""

    objetivo: float  # média entre sementes do RMSE agrupado de X_Zn (91 pontos)
    objetivo_std: float
    por_dobra: pd.DataFrame  # uma linha por (semente, dobra)
    por_semente: pd.DataFrame  # métricas agrupadas por semente
    oof: pd.DataFrame  # predições fora da dobra de X_Zn (pontos experimentais)
    modelos: Dict[tuple, KineticsMLP]  # (semente, dobra) -> modelo


def rodar_cv(
    config: Dict[str, Any],
    dados: Dados,
    sementes: Sequence[int] = SEMENTES_PADRAO,
    pesos: Optional[np.ndarray] = None,
    ao_fim_da_dobra: Optional[Callable[[int, float], None]] = None,
    treinar: Optional[Callable[..., tuple]] = None,
) -> ResultadoCV:
    """Executa o protocolo comum para uma configuração.

    Args:
        config: Hiperparâmetros (chaves de CONFIG_V1).
        pesos: Pesos por registro de `train_df` (D1); None = pesos unitários.
        ao_fim_da_dobra: Callback (índice da dobra, RMSE agrupado parcial) para poda do Optuna.
        treinar: Função alternativa de treino (Fase D); recebe (config, dados, seed, idx_tr, idx_es)
            e devolve (modelo, histórico).
    """
    linhas, oof, modelos = [], [], {}
    w_all = np.ones(len(dados.y_train)) if pesos is None else pesos

    for k, fold in enumerate(dados.folds):
        val = list(fold["val_ensaios"])
        treino_dobra = sorted(set(dados.train_df["ensaio"]) - set(val))
        for s in sementes:
            fixas = config.get("modo_parada", "interna") == "epocas_fixas"
            es = [] if fixas else ensaios_parada_interna(treino_dobra, fold["fold"], s)
            tr = [e for e in treino_dobra if e not in es]
            m_tr, m_es, m_va = dados.mascara(tr), dados.mascara(es), dados.mascara(val)
            assert not (m_tr & m_va).any() and not (m_es & m_va).any() and not (m_tr & m_es).any()

            if treinar is None and fixas:
                trainer = criar_trainer(config, dados, s)
                model, hist = trainer.fit_epocas_fixas(
                    dados.X_train_s[m_tr], dados.y_train[m_tr], w_train=w_all[m_tr],
                    seed_offset=7 * fold["fold"],
                )
            elif treinar is None:
                trainer = criar_trainer(config, dados, s)
                model, hist = trainer.fit_parada_interna(
                    dados.X_train_s[m_tr], dados.y_train[m_tr],
                    dados.X_train_s[m_es], dados.y_train[m_es],
                    w_train=w_all[m_tr], w_es=w_all[m_es], seed_offset=7 * fold["fold"],
                )
            else:
                model, hist = treinar(config, dados, s, tr, es)

            px = simular_X(model, dados, val)
            px["semente"], px["fold"] = s, fold["fold"]
            oof.append(px)
            modelos[(s, fold["fold"])] = model
            linhas.append({
                "semente": s, "fold": fold["fold"], "val_ensaios": str(val), "parada_ensaios": str(es),
                "melhor_epoca": hist["best_epoch"][0], "epocas_rodadas": len(hist["train_loss"]),
                **{f"{c}_X": v for c, v in metricas(px["XZn_exp"].values, px["XZn_pred"].values).items()},
                **metricas_nu(model, dados.X_train_s[m_va], dados.y_train[m_va]),
            })

        if ao_fim_da_dobra is not None:
            parcial = pd.concat(oof, ignore_index=True)
            rmse_parcial = float(np.mean([
                np.sqrt(np.mean((g["XZn_exp"] - g["XZn_pred"]) ** 2)) for _, g in parcial.groupby("semente")
            ]))
            ao_fim_da_dobra(k, rmse_parcial)

    oof_df = pd.concat(oof, ignore_index=True)
    por_semente = pd.DataFrame([
        {"semente": s, **{f"{c}_X": v for c, v in metricas(g["XZn_exp"].values, g["XZn_pred"].values).items()}}
        for s, g in oof_df.groupby("semente")
    ])
    return ResultadoCV(
        objetivo=float(por_semente["RMSE_X"].mean()),
        objetivo_std=float(por_semente["RMSE_X"].std(ddof=1)) if len(por_semente) > 1 else 0.0,
        por_dobra=pd.DataFrame(linhas),
        por_semente=por_semente,
        oof=oof_df,
        modelos=modelos,
    )


def X_dos_alvos(dados: Dados, ensaios: Sequence[int]) -> pd.DataFrame:
    """X_Zn reconstruído a partir dos próprios alvos ν do problema inverso (teto do híbrido)."""
    linhas = []
    for e in ensaios:
        sub = dados.train_df[dados.train_df["ensaio"] == e].sort_values("t_min")
        if sub.empty:
            sub = dados.test_df[dados.test_df["ensaio"] == e].sort_values("t_min")
        eta = float(sub["razao_molar_eta"].iloc[0])
        res = dados.solver.simulate_with_v_profile(sub["t_min"].values, -sub[TARGET].values)
        t_int = np.concatenate([[0.0], sub["t_min"].values])
        x_int = np.clip(np.maximum.accumulate(np.concatenate([[0.0], res["XZn"]])), 0.0, min(1.0, eta))
        exp = dados.exp_df[dados.exp_df["ensaio"] == e]
        linhas.append(pd.DataFrame({
            "ensaio": e, "t_min": exp["t_min"].values, "XZn_exp": exp["XZn"].values,
            "XZn_pred": np.interp(exp["t_min"].values, t_int, x_int),
        }))
    return pd.concat(linhas, ignore_index=True)
