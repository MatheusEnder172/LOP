"""Script Principal de Treinamento, Evolução Arquitetural (Opção 1) e Análise Diferencial Autograd do MLP (Subetapa 3.2.1).

Executa no domínio estrito t > 0 com 3 variáveis ativas X = [CA0_mol_L, razao_molar_eta, t_min]:
1. Comparação entre 4 Arquiteturas Neurais C∞ via GroupKFold (4 dobras disjuntas):
   - MLP-A (Compacta GELU): [32, 16]
   - MLP-B (Intermediária GELU): [64, 32]
   - MLP-C (Profunda SiLU/Swish): [128, 64, 32]
   - ResNet-MLP (Residual GELU): [64, 64, 32] com conexões de atalho (skip connections)
2. Seleção da arquitetura campeã e consolidação via Destilação de Deep Ensemble (4-Fold Early Stopping),
   eliminando o sobreajuste de treinar sem validação e gerando bandas de incerteza epistêmica (±1σ).
3. Avaliação cega estrita nos 3 ensaios de teste em t > 0 (Ensaios 8, 14 e 7 — 180 amostras).
4. Extração de derivadas parciais analíticas exatas (∂|v|/∂C_A0, ∂|v|/∂η, ∂|v|/∂t) via torch.autograd.
5. Geração de 6 figuras científicas em 300 DPI (PNG + PDF):
   - fig_07a_curvas_aprendizado_mlp
   - fig_07b_predicoes_v_mlp (com banda de incerteza ±1σ do Deep Ensemble)
   - fig_07c_paridade_e_residuos_mlp
   - fig_07d_comparativo_arquiteturas_mlp
   - fig_07e_sensibilidade_autograd_mlp (NOVO — Derivadas Parciais Analíticas)
   - fig_07f_superficie_continua_3d_mlp (NOVO — Superfície de Resposta C∞)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parent.parent.parent
sys.path.insert(0, str(SUBETAPA_DIR))
sys.path.insert(0, str(CODIGO_DIR))

from modelo_mlp import KineticsMLP, MLPTrainer


def main() -> None:
    print("=" * 80)
    print("SUBETAPA 3.2.1: EXPLORAÇÃO PROFUNDA DO MLP (OPÇÃO 1 + AUTOGRAD, t > 0, 3 INPUTS)")
    print("=" * 80)

    base_dir = CODIGO_DIR.parent
    data_dir = base_dir / "Base de dados" / "processed" / "splits"
    outputs_dir = CODIGO_DIR / "outputs" / "etapa_3_2" / "subetapa_3_2_1_mlp"
    models_dir = CODIGO_DIR / "outputs" / "models_saved" / "mlp"

    outputs_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    train_dense_path = data_dir / "train_dense.csv"
    test_dense_path = data_dir / "test_dense.csv"
    cv_info_path = data_dir / "cv_folds_info.json"
    scalers_path = data_dir / "scalers.joblib"

    for p in [train_dense_path, test_dense_path, cv_info_path, scalers_path]:
        assert p.exists(), f"Arquivo não encontrado: {p}"

    train_df = pd.read_csv(train_dense_path)
    test_df = pd.read_csv(test_dense_path)
    with open(cv_info_path, "r", encoding="utf-8") as f:
        cv_folds_info = json.load(f)

    scalers = joblib.load(scalers_path)
    scaler_X = scalers["scaler_X"]

    # Estritamente 3 variáveis ativas (sem temperatura_C) e t > 0
    feature_cols = ["CA0_mol_L", "razao_molar_eta", "t_min"]
    target_col = "abs_v_alvo_um_min"

    X_train_raw = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_train_s = scaler_X.transform(X_train_raw)

    X_test_raw = test_df[feature_cols].values
    y_test = test_df[target_col].values
    X_test_s = scaler_X.transform(X_test_raw)

    print(f"Dataset de Treino (t > 0): {len(train_df)} amostras (13 ensaios, input_dim = 3)")
    print(f"Dataset de Teste Cego (t > 0): {len(test_df)} amostras (Ensaios 8, 14, 7)")

    arquiteturas: Dict[str, Dict[str, Any]] = {
        "MLP-A (Compacta GELU)": {
            "hidden_dims": [32, 16],
            "activation": "GELU",
            "use_residual": False,
            "descricao": "2 camadas C∞ GELU (32 -> 16)",
            "lr": 3e-3,
            "weight_decay": 1e-4,
        },
        "MLP-B (Padrão GELU)": {
            "hidden_dims": [64, 32],
            "activation": "GELU",
            "use_residual": False,
            "descricao": "2 camadas C∞ GELU (64 -> 32)",
            "lr": 3e-3,
            "weight_decay": 1e-4,
        },
        "MLP-C (Profunda SiLU)": {
            "hidden_dims": [128, 64, 32],
            "activation": "SiLU",
            "use_residual": False,
            "descricao": "3 camadas C∞ SiLU/Swish (128 -> 64 -> 32)",
            "lr": 2.5e-3,
            "weight_decay": 1e-4,
        },
        "ResNet-MLP (Residual GELU)": {
            "hidden_dims": [64, 32],
            "activation": "GELU",
            "use_residual": True,
            "descricao": "2 blocos residuais C∞ GELU com skip connections estabilizadas (64 -> 32)",
            "lr": 3e-3,
            "weight_decay": 1e-4,
        },
    }

    resultados_cv: Dict[str, Dict[str, Any]] = {}
    histories_por_arq: Dict[str, List[Dict[str, List[float]]]] = {}
    fold_models_por_arq: Dict[str, List[KineticsMLP]] = {}

    criterion_eval = torch.nn.MSELoss()

    for nome_arq, config in arquiteturas.items():
        print(f"\n--- Avaliando {nome_arq} ({config['descricao']}) ---")
        trainer = MLPTrainer(
            hidden_dims=config["hidden_dims"],
            input_dim=3,
            dropout_rate=0.0,
            use_layer_norm=True,
            activation=config["activation"],
            use_residual=config["use_residual"],
            lr=config["lr"],
            weight_decay=config["weight_decay"],
            batch_size=32,
            patience=60,
            seed=42,
        )

        fold_r2: List[float] = []
        fold_r2_log: List[float] = []
        fold_rmse: List[float] = []
        fold_mae: List[float] = []
        fold_histories: List[Dict[str, List[float]]] = []
        fold_models: List[KineticsMLP] = []

        for fold_info in cv_folds_info:
            f_idx = fold_info["fold"]
            val_ensaios = fold_info["val_ensaios"]

            val_mask = train_df["ensaio"].isin(val_ensaios)
            tr_mask = ~val_mask

            X_tr, y_tr = X_train_s[tr_mask], y_train[tr_mask]
            X_va, y_va = X_train_s[val_mask], y_train[val_mask]

            model, history = trainer.fit_with_early_stopping(
                X_tr, y_tr, X_va, y_va, max_epochs=350, seed_offset=f_idx * 7
            )
            _, val_metrics, _ = trainer.evaluate(model, X_va, y_va, criterion_eval)

            fold_r2.append(val_metrics["r2"])
            fold_r2_log.append(val_metrics["r2_log"])
            fold_rmse.append(val_metrics["rmse"])
            fold_mae.append(val_metrics["mae"])
            fold_histories.append(history)
            fold_models.append(model)

            print(
                f"  Fold {f_idx} (Val: {val_ensaios}): "
                f"R² = {val_metrics['r2']:.4f} | R²_log = {val_metrics['r2_log']:.4f} | "
                f"RMSE = {val_metrics['rmse']:.2f} µm/min | MAE = {val_metrics['mae']:.2f} µm/min"
            )

        mean_r2 = float(np.mean(fold_r2))
        std_r2 = float(np.std(fold_r2))
        mean_r2_log = float(np.mean(fold_r2_log))
        mean_rmse = float(np.mean(fold_rmse))
        std_rmse = float(np.std(fold_rmse))
        mean_mae = float(np.mean(fold_mae))
        std_mae = float(np.std(fold_mae))

        print(
            f"  >> Resumo CV {nome_arq}: R² = {mean_r2:.4f} ± {std_r2:.4f} | "
            f"R²_log = {mean_r2_log:.4f} | RMSE = {mean_rmse:.2f} ± {std_rmse:.2f} µm/min"
        )

        resultados_cv[nome_arq] = {
            "r2_mean": mean_r2,
            "r2_std": std_r2,
            "r2_log_mean": mean_r2_log,
            "rmse_mean": mean_rmse,
            "rmse_std": std_rmse,
            "mae_mean": mean_mae,
            "mae_std": std_mae,
            "fold_r2": fold_r2,
            "fold_rmse": fold_rmse,
            "fold_mae": fold_mae,
        }
        histories_por_arq[nome_arq] = fold_histories
        fold_models_por_arq[nome_arq] = fold_models

    df_comp = pd.DataFrame(
        [
            {
                "arquitetura": nome,
                "n_camadas_ocultas": len(cfg["hidden_dims"]),
                "topologia": str(cfg["hidden_dims"]),
                "ativacao": cfg["activation"],
                "residual": cfg["use_residual"],
                "R2_CV_medio": resultados_cv[nome]["r2_mean"],
                "R2_CV_std": resultados_cv[nome]["r2_std"],
                "R2_log_CV_medio": resultados_cv[nome]["r2_log_mean"],
                "RMSE_CV_medio": resultados_cv[nome]["rmse_mean"],
                "RMSE_CV_std": resultados_cv[nome]["rmse_std"],
                "MAE_CV_medio": resultados_cv[nome]["mae_mean"],
                "MAE_CV_std": resultados_cv[nome]["mae_std"],
            }
            for nome, cfg in arquiteturas.items()
        ]
    )
    df_comp["Score_Combinado_CV"] = 0.50 * df_comp["R2_CV_medio"] + 0.50 * df_comp["R2_log_CV_medio"]
    df_comp = df_comp.sort_values("Score_Combinado_CV", ascending=False)

    df_comp.to_csv(outputs_dir / "tabela_comparativo_arquiteturas_mlp.csv", index=False)

    melhor_arq_nome = str(df_comp.iloc[0]["arquitetura"])
    cfg_campea = arquiteturas[melhor_arq_nome]
    fold_models_campeao = fold_models_por_arq[melhor_arq_nome]

    print("\n" + "=" * 80)
    print(f"ARQUITETURA CAMPEÃ SELECIONADA: {melhor_arq_nome}")
    print(f"Topologia: {cfg_campea['hidden_dims']} | Ativação: {cfg_campea['activation']} | Residual: {cfg_campea['use_residual']}")
    print("=" * 80)

    # Consolidação via Destilação do 4-Fold Deep Ensemble (evita memorização cega sem validação)
    trainer_final = MLPTrainer(
        hidden_dims=cfg_campea["hidden_dims"],
        input_dim=3,
        dropout_rate=0.0,
        use_layer_norm=True,
        activation=cfg_campea["activation"],
        use_residual=cfg_campea["use_residual"],
        lr=cfg_campea["lr"],
        weight_decay=cfg_campea["weight_decay"],
        batch_size=32,
        seed=42,
    )
    modelo_final, _ = trainer_final.distill_ensemble_to_single_model(
        fold_models=fold_models_campeao,
        X_train=X_train_s,
        y_train=y_train,
        epochs=260,
        alpha_ensemble=0.10,
    )

    # Avaliação do Modelo Consolidado e do Ensemble (média + incerteza ±1σ)
    _, metricas_treino, preds_treino = trainer_final.evaluate(
        modelo_final, X_train_s, y_train, criterion_eval
    )
    _, metricas_teste, preds_teste = trainer_final.evaluate(
        modelo_final, X_test_s, y_test, criterion_eval
    )
    _, std_treino_ens = trainer_final.predict_ensemble(fold_models_campeao, X_train_s)
    _, std_teste_ens = trainer_final.predict_ensemble(fold_models_campeao, X_test_s)

    print("\n--- Desempenho Global do Modelo Consolidado (t > 0, 3 Inputs) ---")
    print(
        f"Conjunto de Treino (13 ensaios, N=780):\n"
        f"  R² = {metricas_treino['r2']:.4f} | R²_log = {metricas_treino['r2_log']:.4f} | "
        f"RMSE = {metricas_treino['rmse']:.2f} µm/min | MAE = {metricas_treino['mae']:.2f} µm/min"
    )
    print(
        f"Conjunto de Teste Cego (Ensaios 8, 14 e 7, N=180):\n"
        f"  R² = {metricas_teste['r2']:.4f} | R²_log = {metricas_teste['r2_log']:.4f} | "
        f"RMSE = {metricas_teste['rmse']:.2f} µm/min | MAE = {metricas_teste['mae']:.2f} µm/min"
    )

    test_df_eval = test_df.copy()
    test_df_eval["v_pred"] = preds_teste
    test_df_eval["v_std"] = std_teste_ens
    test_df_eval["residuo"] = test_df_eval[target_col] - test_df_eval["v_pred"]

    train_df_eval = train_df.copy()
    train_df_eval["v_pred"] = preds_treino
    train_df_eval["v_std"] = std_treino_ens
    train_df_eval["residuo"] = train_df_eval[target_col] - train_df_eval["v_pred"]

    tabela_metricas_ensaios = []
    print("\n--- Métricas Individuais dos Ensaios de Teste Cego (t > 0) ---")
    for ens in [8, 14, 7]:
        sub = test_df_eval[test_df_eval["ensaio"] == ens]
        y_real = sub[target_col].values
        y_pr = sub["v_pred"].values
        r2_ens = float(r2_score(y_real, y_pr))
        rmse_ens = float(np.sqrt(mean_squared_error(y_real, y_pr)))
        mae_ens = float(mean_absolute_error(y_real, y_pr))
        ca0 = float(sub["CA0_mol_L"].iloc[0])
        eta = float(sub["razao_molar_eta"].iloc[0])
        print(
            f"  Ensaio {ens:02d} (η={eta:.1f}, C_A0={ca0:.2f} M): "
            f"R² = {r2_ens:.4f} | RMSE = {rmse_ens:.2f} µm/min | MAE = {mae_ens:.2f} µm/min"
        )
        tabela_metricas_ensaios.append(
            {
                "ensaio": ens,
                "particao": "Teste Cego",
                "CA0_mol_L": ca0,
                "razao_molar_eta": eta,
                "R2": r2_ens,
                "RMSE_um_min": rmse_ens,
                "MAE_um_min": mae_ens,
            }
        )

    for ens in sorted(train_df["ensaio"].unique()):
        sub = train_df_eval[train_df_eval["ensaio"] == ens]
        y_real = sub[target_col].values
        y_pr = sub["v_pred"].values
        tabela_metricas_ensaios.append(
            {
                "ensaio": ens,
                "particao": "Treino",
                "CA0_mol_L": float(sub["CA0_mol_L"].iloc[0]),
                "razao_molar_eta": float(sub["razao_molar_eta"].iloc[0]),
                "R2": float(r2_score(y_real, y_pr)),
                "RMSE_um_min": float(np.sqrt(mean_squared_error(y_real, y_pr))),
                "MAE_um_min": float(mean_absolute_error(y_real, y_pr)),
            }
        )

    df_ens_metricas = pd.DataFrame(tabela_metricas_ensaios)
    df_ens_metricas.to_csv(outputs_dir / "tabela_metricas_mlp.csv", index=False)

    # Salvar Checkpoint e Metadados do Modelo
    checkpoint_path = models_dir / "mlp_kinetics_v1.pt"
    config_path = models_dir / "mlp_config.json"

    torch.save(modelo_final.state_dict(), checkpoint_path)

    metadata = {
        "modelo": "KineticsMLP",
        "arquitetura": melhor_arq_nome,
        "input_dim": 3,
        "hidden_dims": cfg_campea["hidden_dims"],
        "activation": cfg_campea["activation"],
        "use_residual": cfg_campea["use_residual"],
        "output_head": "Softplus + expm1 (log1p non-negative projection)",
        "features": feature_cols,
        "target": target_col,
        "target_unit": "um/min",
        "domain": "t > 0 (t_0 = 0 hardcoded in PBM)",
        "metricas_treino": metricas_treino,
        "metricas_teste_cego": metricas_teste,
        "metricas_cv": resultados_cv[melhor_arq_nome],
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Geração das 6 Figuras Científicas (incluindo Sensibilidade Autograd e Superfície 3D C∞)
    gerar_figuras_diagnostico(
        modelo_final=modelo_final,
        scaler_X=scaler_X,
        histories_campeao=histories_por_arq[melhor_arq_nome],
        resultados_cv=resultados_cv,
        train_df_eval=train_df_eval,
        test_df_eval=test_df_eval,
        outputs_dir=outputs_dir,
    )

    gerar_relatorio_etapa(
        melhor_arq_nome,
        df_comp,
        metricas_treino,
        metricas_teste,
        tabela_metricas_ensaios,
        outputs_dir,
    )

    print("\nSubetapa 3.2.1 (MLP Protagonista — Opção 1 + Autograd) concluída com 100% de sucesso!")


def gerar_figuras_diagnostico(
    modelo_final: KineticsMLP,
    scaler_X: Any,
    histories_campeao: List[Dict[str, List[float]]],
    resultados_cv: Dict[str, Dict[str, Any]],
    train_df_eval: pd.DataFrame,
    test_df_eval: pd.DataFrame,
    outputs_dir: Path,
) -> None:
    """Gera as 6 figuras científicas em 300 DPI (PNG + PDF)."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 11.5,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "legend.fontsize": 8.8,
            "figure.titlesize": 13,
        }
    )

    cor_treino = "#1f77b4"
    cor_teste = "#d62728"
    cor_val = "#2ca02c"

    # --- FIGURA 07a: Curvas de Aprendizado nas 4 Dobras da CV ---
    fig_a, axes_a = plt.subplots(2, 2, figsize=(13, 9), sharex=True, sharey=True)
    axes_a = axes_a.ravel()

    for idx, hist in enumerate(histories_campeao):
        ax = axes_a[idx]
        epochs = range(1, len(hist["train_loss"]) + 1)
        ax.plot(epochs, hist["train_loss"], label="Perda Treino (MSE log1p)", color=cor_treino, lw=1.7)
        if hist["val_loss"]:
            ax.plot(epochs, hist["val_loss"], label="Perda Validação (Early Stopping)", color=cor_val, lw=1.7, ls="--")
        ax.set_title(f"Dobra (Fold) {idx + 1}", fontweight="bold")
        ax.set_yscale("log")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_xlabel("Épocas de Treinamento")
        ax.set_ylabel("MSE_log (-)")
        ax.legend(loc="upper right", framealpha=0.9)

    fig_a.suptitle("Evolução da Função de Perda (Loss) nas 4 Dobras do GroupKFold (Domínio t > 0, 3 Inputs)", fontweight="bold", y=0.98)
    fig_a.tight_layout()
    fig_a.savefig(outputs_dir / "fig_07a_curvas_aprendizado_mlp.png", dpi=300)
    fig_a.savefig(outputs_dir / "fig_07a_curvas_aprendizado_mlp.pdf", dpi=300)
    plt.close(fig_a)

    # --- FIGURA 07b: Trajetórias Temporais de |v(t)| nos 16 Ensaios (com Banda ±1σ) ---
    fig_b, axes_b = plt.subplots(4, 4, figsize=(16, 12.5), sharex=True)
    axes_b = axes_b.ravel()

    todos_ensaios = sorted(list(set(train_df_eval["ensaio"].unique()).union(set(test_df_eval["ensaio"].unique()))))

    for idx, ens in enumerate(todos_ensaios):
        ax = axes_b[idx]
        is_test = ens in [8, 14, 7]
        df_ens = test_df_eval[test_df_eval["ensaio"] == ens] if is_test else train_df_eval[train_df_eval["ensaio"] == ens]
        df_ens = df_ens.sort_values("t_min")

        t = df_ens["t_min"].values
        v_real = df_ens["abs_v_alvo_um_min"].values
        v_pred = df_ens["v_pred"].values
        v_std = df_ens["v_std"].values
        ca0 = df_ens["CA0_mol_L"].iloc[0]
        eta = df_ens["razao_molar_eta"].iloc[0]

        tag = "TESTE CEGO" if is_test else "Treino"
        c_line = cor_teste if is_test else cor_treino

        ax.plot(t, v_real, "k-", lw=1.8, label="Alvo Inverso (t > 0)", alpha=0.75)
        ax.plot(t, v_pred, color=c_line, lw=1.9, ls="--", label=f"MLP ({tag})")
        ax.fill_between(
            t,
            np.maximum(0.0, v_pred - 1.5 * v_std),
            v_pred + 1.5 * v_std,
            color=c_line,
            alpha=0.22,
            label="Incerteza Ensemble (±1,5σ)",
        )

        ax.set_title(f"Ensaio {ens:02d} ({tag}) — η={eta}, C_A0={ca0}", fontsize=9.2, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.45)
        if idx >= 12:
            ax.set_xlabel("t (min)")
        if idx % 4 == 0:
            ax.set_ylabel("|v(t)| (µm/min)")
        if idx in (0, 6):
            ax.legend(loc="upper right", fontsize=7.2, framealpha=0.88)

    fig_b.suptitle("Trajetórias Cinéticas |v(t)| em t > 0: Predição do MLP + Banda de Incerteza do Deep Ensemble", fontweight="bold", y=0.99)
    fig_b.tight_layout()
    fig_b.savefig(outputs_dir / "fig_07b_predicoes_v_mlp.png", dpi=300)
    fig_b.savefig(outputs_dir / "fig_07b_predicoes_v_mlp.pdf", dpi=300)
    plt.close(fig_b)

    # --- FIGURA 07c: Gráfico de Paridade e Resíduos ---
    fig_c, (ax_c1, ax_c2) = plt.subplots(1, 2, figsize=(14, 6))

    ax_c1.scatter(train_df_eval["abs_v_alvo_um_min"], train_df_eval["v_pred"], color=cor_treino, alpha=0.55, s=28, label="Treino (13 ensaios, t > 0)")
    ax_c1.scatter(test_df_eval["abs_v_alvo_um_min"], test_df_eval["v_pred"], color=cor_teste, marker="^", s=55, label="Teste Cego (Ens 8, 14, 7)", zorder=5)

    lim_max = max(float(train_df_eval["abs_v_alvo_um_min"].max()), float(test_df_eval["abs_v_alvo_um_min"].max())) * 1.08
    ax_c1.plot([0, lim_max], [0, lim_max], "k-", lw=1.5, label="Linha Ideal (1:1)")
    ax_c1.plot([0, lim_max], [0, lim_max * 1.1], "k:", lw=1.0, alpha=0.6, label="Margem de ±10%")
    ax_c1.plot([0, lim_max], [0, lim_max * 0.9], "k:", lw=1.0, alpha=0.6)

    ax_c1.set_xlim(-2, lim_max)
    ax_c1.set_ylim(-2, lim_max)
    ax_c1.set_xlabel("|v|_alvo (µm/min) — Taxa Real (t > 0)")
    ax_c1.set_ylabel("|v|_pred (µm/min) — Predição MLP")
    ax_c1.set_title("(a) Gráfico de Paridade da Taxa Interfacial em t > 0", fontweight="bold")
    ax_c1.grid(True, linestyle="--", alpha=0.5)
    ax_c1.legend(loc="upper left", framealpha=0.9)

    res_tr = train_df_eval["residuo"].values
    res_te = test_df_eval["residuo"].values

    ax_c2.hist(res_tr, bins=35, density=True, color=cor_treino, alpha=0.6, label=f"Treino (Média = {res_tr.mean():.2f} µm/min)")
    ax_c2.hist(res_te, bins=20, density=True, color=cor_teste, alpha=0.6, label=f"Teste Cego (Média = {res_te.mean():.2f} µm/min)")
    ax_c2.axvline(0, color="black", linestyle="--", lw=1.2)

    ax_c2.set_xlabel("Resíduo (|v|_alvo − |v|_pred) (µm/min)")
    ax_c2.set_ylabel("Densidade de Probabilidade")
    ax_c2.set_title("(b) Distribuição Estatística dos Resíduos em t > 0", fontweight="bold")
    ax_c2.grid(True, linestyle="--", alpha=0.5)
    ax_c2.legend(loc="upper right", framealpha=0.9)

    fig_c.suptitle("Avaliação de Concordância e Resíduos do Modelo MLP Consolidado (Domínio t > 0)", fontweight="bold", y=0.98)
    fig_c.tight_layout()
    fig_c.savefig(outputs_dir / "fig_07c_paridade_e_residuos_mlp.png", dpi=300)
    fig_c.savefig(outputs_dir / "fig_07c_paridade_e_residuos_mlp.pdf", dpi=300)
    plt.close(fig_c)

    # --- FIGURA 07d: Comparativo de Arquiteturas na Validação Cruzada ---
    fig_d, (ax_d1, ax_d2) = plt.subplots(1, 2, figsize=(13.5, 5.8))

    nomes = list(resultados_cv.keys())
    labels_curtos = ["MLP-A\n(GELU 32-16)", "MLP-B\n(GELU 64-32)", "MLP-C\n(SiLU 128-64-32)", "ResNet-MLP\n(Residual 64-64-32)"]
    r2_means = [resultados_cv[k]["r2_mean"] for k in nomes]
    r2_stds = [resultados_cv[k]["r2_std"] for k in nomes]
    rmse_means = [resultados_cv[k]["rmse_mean"] for k in nomes]
    rmse_stds = [resultados_cv[k]["rmse_std"] for k in nomes]

    x_pos = np.arange(len(nomes))
    cores_bar = ["#aec7e8", "#1f77b4", "#2ca02c", "#9467bd"]

    bars1 = ax_d1.bar(x_pos, r2_means, yerr=r2_stds, capsize=6, color=cores_bar, edgecolor="black", alpha=0.88)
    ax_d1.set_xticks(x_pos)
    ax_d1.set_xticklabels(labels_curtos, fontsize=9)
    ax_d1.set_ylabel("R² Médio na Validação Cruzada (-)")
    ax_d1.set_title("(a) Coeficiente de Determinação R² (CV 4 Folds, t > 0)", fontweight="bold")
    ax_d1.set_ylim(0.70, 1.03)
    ax_d1.grid(True, linestyle="--", alpha=0.5)
    for bar in bars1:
        yval = bar.get_height()
        ax_d1.text(bar.get_x() + bar.get_width() / 2, yval + 0.015, f"{yval:.4f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    bars2 = ax_d2.bar(x_pos, rmse_means, yerr=rmse_stds, capsize=6, color=["#ffbb78", "#ff7f0e", "#d62728", "#e377c2"], edgecolor="black", alpha=0.88)
    ax_d2.set_xticks(x_pos)
    ax_d2.set_xticklabels(labels_curtos, fontsize=9)
    ax_d2.set_ylabel("RMSE Médio (µm/min)")
    ax_d2.set_title("(b) Erro Quadrático Médio RMSE (CV 4 Folds, t > 0)", fontweight="bold")
    ax_d2.grid(True, linestyle="--", alpha=0.5)
    for bar in bars2:
        yval = bar.get_height()
        ax_d2.text(bar.get_x() + bar.get_width() / 2, yval + 0.15, f"{yval:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    fig_d.suptitle("Opção 1 — Comparação de Arquiteturas Neurais C∞ (Padrão vs. ResNet-MLP) na Validação Cruzada", fontweight="bold", y=0.99)
    fig_d.tight_layout()
    fig_d.savefig(outputs_dir / "fig_07d_comparativo_arquiteturas_mlp.png", dpi=300)
    fig_d.savefig(outputs_dir / "fig_07d_comparativo_arquiteturas_mlp.pdf", dpi=300)
    plt.close(fig_d)

    # --- FIGURA 07e (NOVO): Análise de Sensibilidade Diferencial Analítica via Autograd ---
    fig_e, axes_e = plt.subplots(2, 2, figsize=(14, 10.5))
    t_grid = np.linspace(0.25, 15.0, 120)

    # Perfis das derivadas parciais para os 3 regimes de teste cego (Ensaios 8, 14 e 7)
    perfis_teste = [
        (8, 0.22, 1.0, "#1f77b4", "Ens 08 (C_A0=0,22 M, η=1,0)"),
        (14, 1.00, 1.5, "#2ca02c", "Ens 14 (C_A0=1,00 M, η=1,5)"),
        (7, 0.50, 3.1, "#d62728", "Ens 07 (C_A0=0,50 M, η=3,1)"),
    ]

    ax_e1, ax_e2, ax_e3, ax_e4 = axes_e.ravel()

    for _, ca0_v, eta_v, cor, lbl in perfis_teste:
        X_q = np.column_stack([np.full_like(t_grid, ca0_v), np.full_like(t_grid, eta_v), t_grid])
        X_q_s = scaler_X.transform(X_q)
        sens = modelo_final.compute_sensitivities_autograd(X_q_s, scaler_X.scale_)

        ax_e1.plot(t_grid, sens["dv_dCA0"], color=cor, lw=2.2, label=lbl)
        ax_e2.plot(t_grid, sens["dv_deta"], color=cor, lw=2.2, label=lbl)
        ax_e3.plot(t_grid, sens["dv_dt"], color=cor, lw=2.2, label=lbl)

    ax_e1.axhline(0.0, color="black", ls=":", lw=1.0)
    ax_e1.set_title("(a) Sensibilidade Ácida Analítica: ∂|v| / ∂C_A0", fontweight="bold")
    ax_e1.set_xlabel("Tempo, t (min)")
    ax_e1.set_ylabel("∂|v| / ∂C_A0 (µm·L / min·mol)")
    ax_e1.grid(True, ls="--", alpha=0.5)
    ax_e1.legend(loc="upper right")

    ax_e2.axhline(0.0, color="black", ls=":", lw=1.0)
    ax_e2.set_title("(b) Sensibilidade Estequiométrica Analítica: ∂|v| / ∂η", fontweight="bold")
    ax_e2.set_xlabel("Tempo, t (min)")
    ax_e2.set_ylabel("∂|v| / ∂η (µm/min)")
    ax_e2.grid(True, ls="--", alpha=0.5)
    ax_e2.legend(loc="upper right")

    ax_e3.axhline(0.0, color="black", ls=":", lw=1.0)
    ax_e3.set_title("(c) Taxa de Desaceleração Cinética: ∂|v| / ∂t ≤ 0", fontweight="bold")
    ax_e3.set_xlabel("Tempo, t (min)")
    ax_e3.set_ylabel("∂|v| / ∂t (µm/min²)")
    ax_e3.grid(True, ls="--", alpha=0.5)
    ax_e3.legend(loc="lower right")

    # Painel (d): Importância Diferencial Média Integrada (|∂|v|/∂X_i| * σ_i) no Dataset Completo
    X_all = np.vstack([train_df_eval[["CA0_mol_L", "razao_molar_eta", "t_min"]].values, test_df_eval[["CA0_mol_L", "razao_molar_eta", "t_min"]].values])
    X_all_s = scaler_X.transform(X_all)
    sens_all = modelo_final.compute_sensitivities_autograd(X_all_s, np.ones(3))  # Gradiente adimensionalizado por σ
    imp_grad = np.array([
        np.mean(np.abs(sens_all["dv_dCA0"])),
        np.mean(np.abs(sens_all["dv_deta"])),
        np.mean(np.abs(sens_all["dv_dt"])),
    ])
    imp_grad_pct = 100.0 * imp_grad / np.sum(imp_grad)
    feat_labels = ["Concentração Ácida\n(C_A0)", "Razão Molar\n(η)", "Tempo de Reação\n(t)"]
    bars_g = ax_e4.bar(feat_labels, imp_grad_pct, color=["#1f77b4", "#2ca02c", "#ff7f0e"], edgecolor="black", width=0.52, alpha=0.88)
    for b in bars_g:
        h = b.get_height()
        ax_e4.text(b.get_x() + b.get_width() / 2, h + 1.2, f"{h:.1f}%", ha="center", va="bottom", fontweight="bold")
    ax_e4.set_ylim(0, max(imp_grad_pct) * 1.18)
    ax_e4.set_ylabel("Sensibilidade Média Normalizada (%)")
    ax_e4.set_title("(d) Importância Física via Gradiente Analítico (Autograd)", fontweight="bold")
    ax_e4.grid(True, axis="y", ls="--", alpha=0.5)

    fig_e.suptitle("Análise Diferencial Exclusiva do MLP via PyTorch Autograd: Derivadas Parciais Analíticas C∞", fontweight="bold", y=0.99)
    fig_e.tight_layout()
    fig_e.savefig(outputs_dir / "fig_07e_sensibilidade_autograd_mlp.png", dpi=300)
    fig_e.savefig(outputs_dir / "fig_07e_sensibilidade_autograd_mlp.pdf", dpi=300)
    plt.close(fig_e)

    # --- FIGURA 07f (NOVO): Superfície de Resposta Cinética Contínua C∞ ---
    fig_f = plt.figure(figsize=(14, 6.2))
    ax_f1 = fig_f.add_subplot(1, 2, 1, projection="3d")
    ax_f2 = fig_f.add_subplot(1, 2, 2)

    ca0_mesh = np.linspace(0.10, 1.50, 45)
    t_mesh = np.linspace(0.25, 10.0, 45)
    CA0_G, T_G = np.meshgrid(ca0_mesh, t_mesh)
    ETA_G = np.full_like(CA0_G, 1.5)

    X_surf = np.column_stack([CA0_G.ravel(), ETA_G.ravel(), T_G.ravel()])
    X_surf_s = scaler_X.transform(X_surf)
    with torch.no_grad():
        V_surf = modelo_final(torch.tensor(X_surf_s, dtype=torch.float32)).cpu().numpy().reshape(CA0_G.shape)

    surf = ax_f1.plot_surface(CA0_G, T_G, V_surf, cmap="viridis", edgecolor="none", alpha=0.92)
    ax_f1.set_xlabel("C_A0 (mol/L)")
    ax_f1.set_ylabel("Tempo t (min)")
    ax_f1.set_zlabel("|v(t)| (µm/min)")
    ax_f1.set_title("(a) Superfície 3D Contínua C∞ do MLP (η = 1,5)", fontweight="bold")
    ax_f1.view_init(elev=26, azim=-130)
    fig_f.colorbar(surf, ax=ax_f1, shrink=0.65, pad=0.08, label="|v| (µm/min)")

    # Mapa de contorno (C_A0 vs η em t = 0,50 min)
    eta_mesh = np.linspace(0.5, 3.1, 50)
    CA0_C, ETA_C = np.meshgrid(ca0_mesh, eta_mesh)
    T_C = np.full_like(CA0_C, 0.50)
    X_cont = np.column_stack([CA0_C.ravel(), ETA_C.ravel(), T_C.ravel()])
    X_cont_s = scaler_X.transform(X_cont)
    with torch.no_grad():
        V_cont = modelo_final(torch.tensor(X_cont_s, dtype=torch.float32)).cpu().numpy().reshape(CA0_C.shape)

    cf = ax_f2.contourf(CA0_C, ETA_C, V_cont, levels=18, cmap="plasma")
    cs = ax_f2.contour(CA0_C, ETA_C, V_cont, levels=8, colors="white", linewidths=0.8, alpha=0.7)
    ax_f2.clabel(cs, inline=True, fontsize=8, fmt="%.1f")
    fig_f.colorbar(cf, ax=ax_f2, label="|v(t = 0,50 min)| (µm/min)")
    ax_f2.set_xlabel("Concentração Inicial de Ácido, C_A0 (mol/L)")
    ax_f2.set_ylabel("Razão Molar Estequiométrica, η (-)")
    ax_f2.set_title("(b) Mapa de Contorno Cinético C∞ em t = 0,50 min", fontweight="bold")

    fig_f.suptitle("Interpolação Suave C∞ do MLP no Espaço Operacional Tridimensional [C_A0, η, t]", fontweight="bold", y=0.99)
    fig_f.tight_layout()
    fig_f.savefig(outputs_dir / "fig_07f_superficie_continua_3d_mlp.png", dpi=300)
    fig_f.savefig(outputs_dir / "fig_07f_superficie_continua_3d_mlp.pdf", dpi=300)
    plt.close(fig_f)

    print("Figuras fig_07a a fig_07f geradas em 300 DPI com sucesso!")


def gerar_relatorio_etapa(
    melhor_arq_nome: str,
    df_comp: pd.DataFrame,
    metricas_tr: Dict[str, float],
    metricas_te: Dict[str, float],
    metricas_ens: List[Dict[str, Any]],
    outputs_dir: Path,
) -> None:
    """Gera o relatório técnico de validação da subetapa 3.2.1 em Markdown usando Unicode limpo."""
    relatorio_md = f"""# Relatório de Validação Técnica — Subetapa 3.2.1: Multi-Layer Perceptron (MLP Protagonista — Opção 1 + Autograd)

## 1. Sumário Executivo
Nesta subetapa, o modelo neural **KineticsMLP** foi evoluído sob três diretrizes fundamentais:
1. **Exclusão de `t = 0` e Condição Inicial Hardcoded (`X_Zn(0) = 0, δ(0) = 0`)**: Elimina o salto impulsivo artificial na origem, permitindo que o MLP aprenda o decaimento suave em `t > 0` (`t ∈ [0,25; 15,00] min`).
2. **Vetor de Entrada 3D (`input_dim = 3`)**: Remoção da variável constante `temperatura_C` (`40,0 °C`), operando estritamente com `X = [CA0_mol_L, razao_molar_eta, t_min]`.
3. **Opção 1 + Análise Diferencial `Autograd`**: Comparação de topologias `C∞` (`GELU`, `SiLU/Swish` e blocos residuais `ResNet-MLP`), consolidação via **Destilação de Deep Ensemble (4-Fold Early Stopping)** com bandas de incerteza `±1,5σ` e extração de derivadas parciais analíticas (`∂|v|/∂C_A0`, `∂|v|/∂η`, `∂|v|/∂t`).

A arquitetura campeã **{melhor_arq_nome}** alcançou **R² = {metricas_tr['r2']:.4f} (R²_log = {metricas_tr['r2_log']:.4f}) no Treino** e **R² = {metricas_te['r2']:.4f} (R²_log = {metricas_te['r2_log']:.4f}, RMSE = {metricas_te['rmse']:.2f} µm/min, MAE = {metricas_te['mae']:.2f} µm/min) no Teste Cego**.

---

## 2. Comparação de Arquiteturas na Validação Cruzada (4 Dobras Disjuntas, t > 0)

| Arquitetura | Topologia | Ativação | Residual | R² Médio (CV) | R²_log Médio | RMSE Médio (µm/min) | MAE Médio (µm/min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for _, row in df_comp.iterrows():
        relatorio_md += (
            f"| **{row['arquitetura']}** | `{row['topologia']}` | {row['ativacao']} | {row['residual']} | "
            f"**{row['R2_CV_medio']:.4f}** ± {row['R2_CV_std']:.4f} | {row['R2_log_CV_medio']:.4f} | "
            f"{row['RMSE_CV_medio']:.2f} | {row['MAE_CV_medio']:.2f} |\n"
        )

    relatorio_md += """
---

## 3. Avaliação Individual nos Ensaios de Teste Cego (t > 0)

| Ensaio | Regime Físico-Químico | C_A0 (mol/L) | η (-) | R² Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for item in metricas_ens:
        if item["particao"] == "Teste Cego":
            regime = "Estequiométrico Neutro" if item["ensaio"] == 8 else ("Leve Excesso Ácido" if item["ensaio"] == 14 else "Forte Excesso Ácido")
            relatorio_md += (
                f"| **{item['ensaio']:02d}** | {regime} | {item['CA0_mol_L']:.2f} | {item['razao_molar_eta']:.1f} | "
                f"**{item['R2']:.4f}** | {item['RMSE_um_min']:.2f} | {item['MAE_um_min']:.2f} |\n"
            )

    with open(outputs_dir / "relatorio_etapa_3_2_1_mlp.md", "w", encoding="utf-8") as f:
        f.write(relatorio_md)


if __name__ == "__main__":
    main()
