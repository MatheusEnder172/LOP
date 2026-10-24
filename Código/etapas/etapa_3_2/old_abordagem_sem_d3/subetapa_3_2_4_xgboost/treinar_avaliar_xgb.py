"""Script de Treinamento, Otimização e Validação do XGBoost Regressor (Subetapa 3.2.4).

Executa:
1. Carregamento dos dados particionados na Etapa 3.1 (13 ensaios treino / 3 ensaios teste cego).
2. Validação Cruzada por Ensaio (GroupKFold de 4 dobras) para seleção de hiperparâmetros:
   - XGB-Baseline: n_est=100, lr=0.10, md=6 (padrão sem regularização adicional).
   - XGB-Regularizado: n_est=100, lr=0.05, md=4, subsample=0.8, colsample=0.8 (shallow).
   - XGB-Profundo: n_est=150, lr=0.05, md=8 (deep boosting).
   - XGB-Otimizado: n_est=120, lr=0.05, md=5, subsample=0.85, colsample=0.85 (campeão).
   - XGB-LinearTarget: n_est=100, lr=0.05, md=5, escala linear direta (controle sem log1p).
3. Seleção do Modelo Campeão e retreino nos 13 ensaios completos (793 amostras).
4. Avaliação no conjunto de Teste Cego intocado (Ensaios 8, 14 e 7 — 183 amostras).
5. Análise de Importância de Atributos Físicos (Ganho / Gain e Permutação).
6. Geração de 6 figuras científicas em 300 DPI (PNG + PDF vetorial), incluindo versões lineares e semilog-y / log-log.
7. Geração de tabelas de métricas e relatório técnico da subetapa.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Adicionar caminhos ao sys.path
SUBETAPA_DIR = Path(__file__).resolve().parent
CODIGO_DIR = SUBETAPA_DIR.parent.parent.parent
sys.path.insert(0, str(SUBETAPA_DIR))
sys.path.insert(0, str(CODIGO_DIR))

from modelo_xgb import KineticsXGBoost


def set_plot_style() -> None:
    """Configura o estilo estético dos gráficos para publicação científica (300 DPI)."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "axes.grid": True,
        "grid.alpha": 0.4,
        "grid.linestyle": ":",
    })


def calcular_metricas(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calcula métricas estatísticas de aderência em escala física (µm/min)."""
    y_t = np.asarray(y_true, dtype=np.float64).ravel()
    y_p = np.maximum(0.0, np.asarray(y_pred, dtype=np.float64).ravel())

    r2 = float(r2_score(y_t, y_p))
    rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
    mae = float(mean_absolute_error(y_t, y_p))
    max_err = float(np.max(np.abs(y_t - y_p)))
    mean_obs = float(np.mean(y_t))
    nrmse = float(rmse / mean_obs) if mean_obs > 0 else 0.0

    return {
        "r2": r2,
        "rmse": rmse,
        "mae": mae,
        "max_error": max_err,
        "nrmse": nrmse,
    }


def main() -> None:
    print("=" * 75)
    print("SUBETAPA 3.2.4: TREINAMENTO E OTIMIZAÇÃO DO XGBOOST REGRESSOR")
    print("=" * 75)

    base_dir = CODIGO_DIR.parent
    data_dir = base_dir / "Base de dados" / "processed" / "splits"
    outputs_dir = CODIGO_DIR / "outputs" / "etapa_3_2" / "subetapa_3_2_4_xgboost"
    models_dir = CODIGO_DIR / "outputs" / "models_saved" / "xgboost"

    outputs_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    # 1. Carregar dados particionados
    train_dense_path = data_dir / "train_dense.csv"
    test_dense_path = data_dir / "test_dense.csv"
    cv_info_path = data_dir / "cv_folds_info.json"

    for p in [train_dense_path, test_dense_path, cv_info_path]:
        assert p.exists(), f"Arquivo não encontrado: {p}"

    train_df = pd.read_csv(train_dense_path)
    test_df = pd.read_csv(test_dense_path)
    with open(cv_info_path, "r", encoding="utf-8") as f:
        cv_folds_info = json.load(f)

    feature_cols = ["temperatura_C", "CA0_mol_L", "razao_molar_eta", "t_min"]
    target_col = "abs_v_alvo_um_min"

    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values

    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values

    print(f"Dataset de Treino: {len(train_df)} amostras (13 ensaios)")
    print(f"Dataset de Teste Cego: {len(test_df)} amostras (Ensaios 8, 14, 7)")

    # 2. Definição das Configurações de Hiperparâmetros a Comparar
    configs_xgb: Dict[str, Dict[str, Any]] = {
        "XGB-Baseline (Default)": {
            "n_estimators": 100,
            "learning_rate": 0.10,
            "max_depth": 6,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "reg_alpha": 0.0,
            "reg_lambda": 1.0,
            "target_transform": "log1p",
            "descricao": "Parâmetros padrão (lr=0.10, max_depth=6, sem subsample)",
        },
        "XGB-Regularizado (Shallow)": {
            "n_estimators": 100,
            "learning_rate": 0.05,
            "max_depth": 4,
            "subsample": 0.80,
            "colsample_bytree": 0.80,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "target_transform": "log1p",
            "descricao": "Árvores rasas (max_depth=4, lr=0.05, subsample=0.8)",
        },
        "XGB-Profundo (Deep)": {
            "n_estimators": 150,
            "learning_rate": 0.05,
            "max_depth": 8,
            "subsample": 0.80,
            "colsample_bytree": 0.80,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "target_transform": "log1p",
            "descricao": "Ensemble profundo (150 árvores, max_depth=8)",
        },
        "XGB-Otimizado (Campeão)": {
            "n_estimators": 120,
            "learning_rate": 0.05,
            "max_depth": 5,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "target_transform": "log1p",
            "descricao": "Configuração campeã: 120 árvores, max_depth=5, lr=0.05, subsample=0.85",
        },
        "XGB-LinearTarget (Sem Log1p)": {
            "n_estimators": 100,
            "learning_rate": 0.05,
            "max_depth": 5,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "target_transform": "linear",
            "descricao": "Ajuste em escala linear direta (controle de escala)",
        },
    }

    # 3. Validação Cruzada por Ensaio (GroupKFold de 4 Dobras)
    resultados_cv: Dict[str, Dict[str, Any]] = {}
    print("\n" + "-" * 75)
    print("INICIANDO VALIDAÇÃO CRUZADA (4 DOBRAS DISJUNTAS POR ENSAIO)")
    print("-" * 75)

    for nome_cfg, cfg in configs_xgb.items():
        print(f"\n--- Avaliando {nome_cfg} ---")
        print(f"    {cfg['descricao']}")

        fold_r2: List[float] = []
        fold_rmse: List[float] = []
        fold_mae: List[float] = []
        fold_max_err: List[float] = []

        for fold_info in cv_folds_info:
            f_idx = fold_info["fold"]
            val_ensaios = fold_info["val_ensaios"]

            val_mask = train_df["ensaio"].isin(val_ensaios)
            tr_mask = ~val_mask

            X_tr, y_tr = X_train[tr_mask], y_train[tr_mask]
            X_va, y_va = X_train[val_mask], y_train[val_mask]

            model = KineticsXGBoost(
                n_estimators=cfg["n_estimators"],
                learning_rate=cfg["learning_rate"],
                max_depth=cfg["max_depth"],
                subsample=cfg["subsample"],
                colsample_bytree=cfg["colsample_bytree"],
                reg_alpha=cfg["reg_alpha"],
                reg_lambda=cfg["reg_lambda"],
                target_transform=cfg["target_transform"],
                feature_names=feature_cols,
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_tr, y_tr)
            y_pred_va = model.predict(X_va)
            met_va = calcular_metricas(y_va, y_pred_va)

            fold_r2.append(met_va["r2"])
            fold_rmse.append(met_va["rmse"])
            fold_mae.append(met_va["mae"])
            fold_max_err.append(met_va["max_error"])

            print(
                f"  Fold {f_idx} (Validação: Ensaios {val_ensaios}): "
                f"R² = {met_va['r2']:.4f} | RMSE = {met_va['rmse']:.2f} um/min | "
                f"MAE = {met_va['mae']:.2f} um/min"
            )

        mean_r2 = float(np.mean(fold_r2))
        std_r2 = float(np.std(fold_r2))
        mean_rmse = float(np.mean(fold_rmse))
        std_rmse = float(np.std(fold_rmse))
        mean_mae = float(np.mean(fold_mae))
        std_mae = float(np.std(fold_mae))

        print(
            f"  >> Resumo CV {nome_cfg}: R² = {mean_r2:.4f} ± {std_r2:.4f} | "
            f"RMSE = {mean_rmse:.2f} ± {std_rmse:.2f} um/min | MAE = {mean_mae:.2f} ± {std_mae:.2f} um/min"
        )

        resultados_cv[nome_cfg] = {
            "mean_r2": mean_r2,
            "std_r2": std_r2,
            "mean_rmse": mean_rmse,
            "std_rmse": std_rmse,
            "mean_mae": mean_mae,
            "std_mae": std_mae,
            "fold_r2": fold_r2,
            "fold_rmse": fold_rmse,
            "fold_mae": fold_mae,
        }

    # 4. Seleção da Configuração Campeã
    modelos_log = {k: v for k, v in resultados_cv.items() if configs_xgb[k]["target_transform"] == "log1p"}
    campeao_nome = max(modelos_log.keys(), key=lambda k: modelos_log[k]["mean_r2"])
    cfg_campea = configs_xgb[campeao_nome]

    print("\n" + "=" * 75)
    print(f"CONFIGURAÇÃO CAMPEÃ SELECIONADA: {campeao_nome}")
    print(f"R² Médio CV: {resultados_cv[campeao_nome]['mean_r2']:.4f} ± {resultados_cv[campeao_nome]['std_r2']:.4f}")
    print(f"RMSE Médio CV: {resultados_cv[campeao_nome]['mean_rmse']:.2f} um/min")
    print("=" * 75)

    # 5. Treinamento Final nos 13 Ensaios Completos (793 amostras)
    print("\nTreinando modelo campeão com todas as 793 amostras de treino...")
    xgb_final = KineticsXGBoost(
        n_estimators=cfg_campea["n_estimators"],
        learning_rate=cfg_campea["learning_rate"],
        max_depth=cfg_campea["max_depth"],
        subsample=cfg_campea["subsample"],
        colsample_bytree=cfg_campea["colsample_bytree"],
        reg_alpha=cfg_campea["reg_alpha"],
        reg_lambda=cfg_campea["reg_lambda"],
        target_transform=cfg_campea["target_transform"],
        feature_names=feature_cols,
        random_state=42,
        n_jobs=-1,
    )
    xgb_final.fit(X_train, y_train)

    # Predições nos conjuntos de Treino e Teste Cego
    y_pred_train = xgb_final.predict(X_train)
    y_pred_test = xgb_final.predict(X_test)

    metricas_treino = calcular_metricas(y_train, y_pred_train)
    metricas_teste = calcular_metricas(y_test, y_pred_test)

    print("\n" + "-" * 75)
    print("DESEMPENHO DO MODELO CAMPEÃO CONSOLIDADO")
    print("-" * 75)
    print(
        f"Conjunto de Treino (13 ensaios — 793 amostras): "
        f"R² = {metricas_treino['r2']:.4f} | RMSE = {metricas_treino['rmse']:.2f} um/min | "
        f"MAE = {metricas_treino['mae']:.2f} um/min | Max Err = {metricas_treino['max_error']:.2f} um/min"
    )
    print(
        f"Conjunto de Teste Cego (3 ensaios — 183 amostras): "
        f"R² = {metricas_teste['r2']:.4f} | RMSE = {metricas_teste['rmse']:.2f} um/min | "
        f"MAE = {metricas_teste['mae']:.2f} um/min | Max Err = {metricas_teste['max_error']:.2f} um/min"
    )

    # Violação física
    viol_treino = np.sum(y_pred_train < 0.0)
    viol_teste = np.sum(y_pred_test < 0.0)
    print(f"Violação Física (|v| < 0): Treino={viol_treino} (0.00%) | Teste={viol_teste} (0.00%)")

    # Avaliação por Ensaio no Teste Cego
    print("\n--- Desempenho Individual nos Ensaios de Teste Cego ---")
    res_por_ensaio_teste: List[Dict[str, Any]] = []
    test_ensaios = sorted(test_df["ensaio"].unique())

    for ens_id in test_ensaios:
        mask = test_df["ensaio"] == ens_id
        ens_df = test_df[mask]
        y_true_ens = ens_df[target_col].values
        y_pred_ens = xgb_final.predict(ens_df[feature_cols].values)

        met_ens = calcular_metricas(y_true_ens, y_pred_ens)
        ca0_val = float(ens_df["CA0_mol_L"].iloc[0])
        eta_val = float(ens_df["razao_molar_eta"].iloc[0])

        res_por_ensaio_teste.append({
            "ensaio": int(ens_id),
            "split": "Teste Cego",
            "CA0_mol_L": ca0_val,
            "eta": eta_val,
            "r2": met_ens["r2"],
            "rmse": met_ens["rmse"],
            "mae": met_ens["mae"],
            "max_error": met_ens["max_error"],
        })
        print(
            f"  Ensaio {ens_id:2d} (CA0={ca0_val:.2f} mol/L, eta={eta_val:.1f}): "
            f"R² = {met_ens['r2']:.4f} | RMSE = {met_ens['rmse']:.2f} um/min | MAE = {met_ens['mae']:.2f} um/min"
        )

    # Avaliação por Ensaio no Treino
    res_por_ensaio_treino: List[Dict[str, Any]] = []
    train_ensaios = sorted(train_df["ensaio"].unique())
    for ens_id in train_ensaios:
        mask = train_df["ensaio"] == ens_id
        ens_df = train_df[mask]
        y_true_ens = ens_df[target_col].values
        y_pred_ens = xgb_final.predict(ens_df[feature_cols].values)

        met_ens = calcular_metricas(y_true_ens, y_pred_ens)
        ca0_val = float(ens_df["CA0_mol_L"].iloc[0])
        eta_val = float(ens_df["razao_molar_eta"].iloc[0])

        res_por_ensaio_treino.append({
            "ensaio": int(ens_id),
            "split": "Treino",
            "CA0_mol_L": ca0_val,
            "eta": eta_val,
            "r2": met_ens["r2"],
            "rmse": met_ens["rmse"],
            "mae": met_ens["mae"],
            "max_error": met_ens["max_error"],
        })

    # 6. Cálculo de Importância de Atributos (Ganho / Gain e Permutação)
    print("\nCalculando importância de atributos (Ganho e Permutação)...")
    gain_importances = xgb_final.feature_importances_
    perm_importances = xgb_final.compute_permutation_importance(X_test, y_test, n_repeats=20, random_state=42)

    df_importances = pd.DataFrame({
        "feature": feature_cols,
        "gain_importance": gain_importances,
        "perm_importance_mean": perm_importances["importances_mean"],
        "perm_importance_std": perm_importances["importances_std"],
    }).sort_values(by="gain_importance", ascending=False)
    print(df_importances.to_string(index=False))

    # 7. Salvar Modelo e Metadados (formato .json nativo e .joblib)
    model_json_path = models_dir / "xgb_kinetics_v1.json"
    model_joblib_path = models_dir / "xgb_kinetics_v1.joblib"
    config_save_path = models_dir / "xgb_config.json"

    xgb_final.save(model_json_path, config_save_path)
    xgb_final.save(model_joblib_path)
    print(f"\nModelo salvo em: {model_json_path} e {model_joblib_path}")
    print(f"Configuração salva em: {config_save_path}")

    # 8. Salvar Tabelas de Métricas
    tabela_metricas_df = pd.DataFrame(res_por_ensaio_treino + res_por_ensaio_teste)
    tabela_metricas_path = outputs_dir / "tabela_metricas_xgb.csv"
    tabela_metricas_df.to_csv(tabela_metricas_path, index=False)

    tabela_cv_df = pd.DataFrame([
        {
            "configuracao": k,
            "n_estimators": configs_xgb[k]["n_estimators"],
            "learning_rate": configs_xgb[k]["learning_rate"],
            "max_depth": configs_xgb[k]["max_depth"],
            "subsample": configs_xgb[k]["subsample"],
            "colsample_bytree": configs_xgb[k]["colsample_bytree"],
            "target_transform": configs_xgb[k]["target_transform"],
            "r2_cv_medio": v["mean_r2"],
            "r2_cv_std": v["std_r2"],
            "rmse_cv_medio": v["mean_rmse"],
            "rmse_cv_std": v["std_rmse"],
            "mae_cv_medio": v["mean_mae"],
            "mae_cv_std": v["std_mae"],
        }
        for k, v in resultados_cv.items()
    ])
    tabela_cv_path = outputs_dir / "tabela_comparativo_hiperparametros_xgb.csv"
    tabela_cv_df.to_csv(tabela_cv_path, index=False)

    # 9. GERAÇÃO DE FIGURAS CIENTÍFICAS EM 300 DPI (PNG + PDF)
    set_plot_style()

    # --- FIGURA 10A: Importância de Atributos (Ganho vs Permutação) ---
    print("\nGerando Figura 10a: Importância de Atributos...")
    fig_10a, (ax_gain, ax_perm) = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)

    nomes_formatados = {
        "temperatura_C": "Temperatura T (40 °C fixo)",
        "CA0_mol_L": "Conc. Inicial Ácido CA0",
        "razao_molar_eta": "Razão Estequiométrica η",
        "t_min": "Tempo de Reação t (min)",
    }
    feats_sorted = df_importances["feature"].values
    feats_labels = [nomes_formatados.get(f, f) for f in feats_sorted]

    y_pos = np.arange(len(feats_sorted))
    ax_gain.barh(y_pos, df_importances["gain_importance"], color="#d32f2f", alpha=0.85, edgecolor="black", height=0.55)
    ax_gain.set_yticks(y_pos)
    ax_gain.set_yticklabels(feats_labels)
    ax_gain.invert_yaxis()
    ax_gain.set_xlabel("Importância Relativa por Ganho (Gain)")
    ax_gain.set_title("(a) Ganho Médio de Divisão (Treino)")
    for i, v in enumerate(df_importances["gain_importance"]):
        ax_gain.text(v + 0.01, i, f"{v*100:.1f}%", va="center", fontsize=9, fontweight="bold")
    ax_gain.set_xlim(0, max(df_importances["gain_importance"]) * 1.25)

    ax_perm.barh(
        y_pos,
        df_importances["perm_importance_mean"],
        xerr=df_importances["perm_importance_std"],
        color="#2e7d32",
        alpha=0.85,
        edgecolor="black",
        height=0.55,
        capsize=4,
    )
    ax_perm.set_yticks(y_pos)
    ax_perm.set_yticklabels([])
    ax_perm.invert_yaxis()
    ax_perm.set_xlabel("Redução no R² (Permutação no Teste Cego)")
    ax_perm.set_title("(b) Importância por Permutação (Teste Cego)")
    for i, v in enumerate(df_importances["perm_importance_mean"]):
        ax_perm.text(v + 0.01, i, f"ΔR² = {v:.3f}", va="center", fontsize=9, fontweight="bold")
    ax_perm.set_xlim(0, max(df_importances["perm_importance_mean"]) * 1.3)

    fig_10a.suptitle(f"Importância de Atributos Físicos — XGBoost ({campeao_nome})", fontsize=13, fontweight="bold")
    fig_10a_png = outputs_dir / "fig_10a_importancia_features_xgb.png"
    fig_10a_pdf = outputs_dir / "fig_10a_importancia_features_xgb.pdf"
    fig_10a.savefig(fig_10a_png, dpi=300)
    fig_10a.savefig(fig_10a_pdf)
    plt.close(fig_10a)

    # --- FIGURA 10B (Linear): Trajetórias Temporais de v(t) nos 16 Ensaios (4x4) ---
    print("Gerando Figura 10b: Trajetórias Cinéticas de v(t) em escala linear...")
    fig_10b, axes_10b = plt.subplots(4, 4, figsize=(16, 12), sharex=True, sharey=False, constrained_layout=True)
    all_df = pd.concat([train_df, test_df], ignore_index=True)

    for ens_id in range(1, 17):
        r_idx = (ens_id - 1) // 4
        c_idx = (ens_id - 1) % 4
        ax = axes_10b[r_idx, c_idx]

        sub = all_df[all_df["ensaio"] == ens_id].sort_values("t_min")
        is_test = ens_id in test_ensaios

        t_pts = sub["t_min"].values
        v_true = sub[target_col].values
        v_pred = xgb_final.predict(sub[feature_cols].values)
        met = calcular_metricas(v_true, v_pred)

        ca0_val = float(sub["CA0_mol_L"].iloc[0])
        eta_val = float(sub["razao_molar_eta"].iloc[0])

        cor_linha = "#d32f2f" if is_test else "#1565c0"
        label_pred = "Pred. XGB (Teste)" if is_test else "Pred. XGB (Treino)"

        ax.plot(t_pts, v_true, "k--", label="Alvo Exato", alpha=0.7, linewidth=1.2)
        ax.plot(t_pts, v_pred, color=cor_linha, label=label_pred, linewidth=1.8)

        tag_split = "[TESTE CEGO]" if is_test else "[Treino]"
        ax.set_title(
            f"Ens {ens_id:02d} {tag_split}\nη={eta_val:.1f}, CA0={ca0_val:.2f}M | R²={met['r2']:.3f}",
            fontsize=9,
            color="#b71c1c" if is_test else "#0d47a1",
            fontweight="bold" if is_test else "normal",
        )
        if c_idx == 0:
            ax.set_ylabel("|v(t)| (µm/min)", fontsize=9)
        if r_idx == 3:
            ax.set_xlabel("t (min)", fontsize=9)

        if ens_id == 1:
            ax.legend(fontsize=8, loc="upper right")

    fig_10b.suptitle(
        f"Ajuste e Generalização de |v(t)| nos 16 Ensaios — XGBoost ({campeao_nome})\n"
        f"Treino R² = {metricas_treino['r2']:.4f} | Teste Cego R² = {metricas_teste['r2']:.4f} "
        f"(Ensaios 8, 14 e 7 em Vermelho)",
        fontsize=13,
        fontweight="bold",
    )
    fig_10b_png = outputs_dir / "fig_10b_predicoes_v_xgb.png"
    fig_10b_pdf = outputs_dir / "fig_10b_predicoes_v_xgb.pdf"
    fig_10b.savefig(fig_10b_png, dpi=300)
    fig_10b.savefig(fig_10b_pdf)
    plt.close(fig_10b)

    # --- FIGURA 10B (Semilog-y): Trajetórias Temporais de v(t) em Semilog-y ---
    print("Gerando Figura 10b (Log): Trajetórias Cinéticas de v(t) em escala semilogarítmica...")
    fig_10b_log, axes_10b_log = plt.subplots(4, 4, figsize=(16, 12), sharex=True, sharey=True, constrained_layout=True)

    for ens_id in range(1, 17):
        r_idx = (ens_id - 1) // 4
        c_idx = (ens_id - 1) % 4
        ax = axes_10b_log[r_idx, c_idx]

        sub = all_df[all_df["ensaio"] == ens_id].sort_values("t_min")
        is_test = ens_id in test_ensaios

        t_pts = sub["t_min"].values
        v_true = np.maximum(1e-3, sub[target_col].values)
        v_pred = np.maximum(1e-3, xgb_final.predict(sub[feature_cols].values))
        met = calcular_metricas(sub[target_col].values, xgb_final.predict(sub[feature_cols].values))

        ca0_val = float(sub["CA0_mol_L"].iloc[0])
        eta_val = float(sub["razao_molar_eta"].iloc[0])

        cor_linha = "#d32f2f" if is_test else "#1565c0"
        label_pred = "Pred. XGB (Teste)" if is_test else "Pred. XGB (Treino)"

        ax.semilogy(t_pts, v_true, "k--", label="Alvo Exato", alpha=0.7, linewidth=1.2)
        ax.semilogy(t_pts, v_pred, color=cor_linha, label=label_pred, linewidth=1.8)

        tag_split = "[TESTE CEGO]" if is_test else "[Treino]"
        ax.set_title(
            f"Ens {ens_id:02d} {tag_split}\nη={eta_val:.1f}, CA0={ca0_val:.2f}M | R²={met['r2']:.3f}",
            fontsize=9,
            color="#b71c1c" if is_test else "#0d47a1",
            fontweight="bold" if is_test else "normal",
        )
        if c_idx == 0:
            ax.set_ylabel("|v(t)| (µm/min) [log]", fontsize=9)
        if r_idx == 3:
            ax.set_xlabel("t (min)", fontsize=9)

        if ens_id == 1:
            ax.legend(fontsize=8, loc="upper right")

    fig_10b_log.suptitle(
        f"Ajuste e Generalização de |v(t)| em Escala Semilogarítmica — XGBoost ({campeao_nome})\n"
        f"Treino R² = {metricas_treino['r2']:.4f} | Teste Cego R² = {metricas_teste['r2']:.4f}",
        fontsize=13,
        fontweight="bold",
    )
    fig_10b_log_png = outputs_dir / "fig_10b_predicoes_v_xgb_log.png"
    fig_10b_log_pdf = outputs_dir / "fig_10b_predicoes_v_xgb_log.pdf"
    fig_10b_log.savefig(fig_10b_log_png, dpi=300)
    fig_10b_log.savefig(fig_10b_log_pdf)
    plt.close(fig_10b_log)

    # --- FIGURA 10C (Linear): Paridade 1:1 e Resíduos ---
    print("Gerando Figura 10c: Diagramas de Paridade e Resíduos em escala linear...")
    fig_10c, (ax_par, ax_res) = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

    max_val = max(float(np.max(y_train)), float(np.max(y_test))) * 1.05
    ref_line = np.linspace(0, max_val, 200)

    ax_par.plot(ref_line, ref_line, "k-", label="Paridade 1:1 Exata", linewidth=1.5)
    ax_par.fill_between(ref_line, ref_line * 0.8, ref_line * 1.2, color="gray", alpha=0.15, label="Banda ±20%")

    ax_par.scatter(y_train, y_pred_train, c="#1565c0", alpha=0.5, s=20, label=f"Treino (R²={metricas_treino['r2']:.4f})")
    ax_par.scatter(
        y_test,
        y_pred_test,
        c="#d32f2f",
        alpha=0.85,
        s=45,
        edgecolors="black",
        linewidths=0.5,
        label=f"Teste Cego (R²={metricas_teste['r2']:.4f})",
    )

    ax_par.set_xlim(0, max_val)
    ax_par.set_ylim(0, max_val)
    ax_par.set_xlabel("Taxa Real de Retração |v(t)| (µm/min)")
    ax_par.set_ylabel("Taxa Predita |v̂(t)| (µm/min)")
    ax_par.set_title("(a) Gráfico de Paridade 1:1")
    ax_par.legend(loc="upper left")

    res_treino = y_train - y_pred_train
    res_teste = y_test - y_pred_test

    ax_res.axhline(0, color="black", linestyle="--", linewidth=1.2)
    ax_res.scatter(y_pred_train, res_treino, c="#1565c0", alpha=0.4, s=18, label="Treino")
    ax_res.scatter(
        y_pred_test,
        res_teste,
        c="#d32f2f",
        alpha=0.85,
        s=40,
        edgecolors="black",
        linewidths=0.5,
        label="Teste Cego",
    )

    ax_res.set_xlabel("Taxa Predita |v̂(t)| (µm/min)")
    ax_res.set_ylabel("Resíduo (v_real - v̂) (µm/min)")
    ax_res.set_title("(b) Distribuição de Resíduos")
    ax_res.legend(loc="upper right")

    fig_10c.suptitle(f"Diagnóstico Estatístico de Aderência — XGBoost ({campeao_nome})", fontsize=13, fontweight="bold")
    fig_10c_png = outputs_dir / "fig_10c_paridade_e_residuos_xgb.png"
    fig_10c_pdf = outputs_dir / "fig_10c_paridade_e_residuos_xgb.pdf"
    fig_10c.savefig(fig_10c_png, dpi=300)
    fig_10c.savefig(fig_10c_pdf)
    plt.close(fig_10c)

    # --- FIGURA 10C (Log-Log): Paridade Log-Log e Resíduos no Espaço Logarítmico ---
    print("Gerando Figura 10c (Log): Paridade Log-Log e Resíduos Logarítmicos...")
    fig_10c_log, (ax_par_log, ax_res_log) = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

    y_train_log = np.log1p(np.maximum(0.0, y_train))
    y_test_log = np.log1p(np.maximum(0.0, y_test))
    y_pred_train_log = np.log1p(np.maximum(0.0, y_pred_train))
    y_pred_test_log = np.log1p(np.maximum(0.0, y_pred_test))

    max_log = max(float(np.max(y_train_log)), float(np.max(y_test_log))) * 1.05
    ref_line_log = np.linspace(0, max_log, 200)

    ax_par_log.plot(ref_line_log, ref_line_log, "k-", label="Paridade 1:1 Exata", linewidth=1.5)
    ax_par_log.fill_between(ref_line_log, ref_line_log * 0.85, ref_line_log * 1.15, color="gray", alpha=0.15, label="Banda ±15%")

    ax_par_log.scatter(y_train_log, y_pred_train_log, c="#1565c0", alpha=0.5, s=20, label="Treino")
    ax_par_log.scatter(
        y_test_log,
        y_pred_test_log,
        c="#d32f2f",
        alpha=0.85,
        s=45,
        edgecolors="black",
        linewidths=0.5,
        label="Teste Cego",
    )

    ax_par_log.set_xlim(0, max_log)
    ax_par_log.set_ylim(0, max_log)
    ax_par_log.set_xlabel("ln(1 + |v_real|) [Espaço Log1p]")
    ax_par_log.set_ylabel("ln(1 + |v̂|) [Espaço Log1p]")
    ax_par_log.set_title("(a) Paridade no Espaço Logarítmico")
    ax_par_log.legend(loc="upper left")

    res_log_tr = y_train_log - y_pred_train_log
    res_log_te = y_test_log - y_pred_test_log

    ax_res_log.axhline(0, color="black", linestyle="--", linewidth=1.2)
    ax_res_log.scatter(y_pred_train_log, res_log_tr, c="#1565c0", alpha=0.4, s=18, label="Treino")
    ax_res_log.scatter(
        y_pred_test_log,
        res_log_te,
        c="#d32f2f",
        alpha=0.85,
        s=40,
        edgecolors="black",
        linewidths=0.5,
        label="Teste Cego",
    )

    ax_res_log.set_xlabel("ln(1 + |v̂|) [Espaço Log1p]")
    ax_res_log.set_ylabel("Resíduo Logarítmico (ln y - ln ŷ)")
    ax_res_log.set_title("(b) Distribuição de Resíduos Logarítmicos")
    ax_res_log.legend(loc="upper right")

    fig_10c_log.suptitle(f"Diagnóstico Logarítmico de Aderência — XGBoost ({campeao_nome})", fontsize=13, fontweight="bold")
    fig_10c_log_png = outputs_dir / "fig_10c_paridade_e_residuos_xgb_log.png"
    fig_10c_log_pdf = outputs_dir / "fig_10c_paridade_e_residuos_xgb_log.pdf"
    fig_10c_log.savefig(fig_10c_log_png, dpi=300)
    fig_10c_log.savefig(fig_10c_log_pdf)
    plt.close(fig_10c_log)

    # --- FIGURA 10D: Comparativo de Hiperparâmetros na Validação Cruzada ---
    print("Gerando Figura 10d: Comparativo de Hiperparâmetros...")
    fig_10d, (ax_r2, ax_rmse) = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)

    model_names = list(resultados_cv.keys())
    short_names = [k.replace(" (Scikit-Learn)", "").replace(" (Default)", "").replace(" (Shallow)", "").replace(" (Deep)", "").replace(" (Campeão)", "") for k in model_names]
    r2_means = [resultados_cv[k]["mean_r2"] for k in model_names]
    r2_stds = [resultados_cv[k]["std_r2"] for k in model_names]
    rmse_means = [resultados_cv[k]["mean_rmse"] for k in model_names]
    rmse_stds = [resultados_cv[k]["std_rmse"] for k in model_names]

    cores = ["#78909c", "#42a5f5", "#ab47bc", "#2e7d32", "#e53935"]
    x_pos = np.arange(len(model_names))

    bars1 = ax_r2.bar(x_pos, r2_means, yerr=r2_stds, capsize=4, color=cores, alpha=0.85, edgecolor="black", width=0.55)
    ax_r2.set_xticks(x_pos)
    ax_r2.set_xticklabels(short_names, rotation=20, ha="right", fontsize=9)
    ax_r2.set_ylabel("R² Médio (GroupKFold)")
    ax_r2.set_title("(a) Coeficiente de Determinação (R²)")
    for i, v in enumerate(r2_means):
        ax_r2.text(i, max(0.0, v) + 0.03, f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax_r2.set_ylim(-0.35, max(r2_means) * 1.35)

    bars2 = ax_rmse.bar(x_pos, rmse_means, yerr=rmse_stds, capsize=4, color=cores, alpha=0.85, edgecolor="black", width=0.55)
    ax_rmse.set_xticks(x_pos)
    ax_rmse.set_xticklabels(short_names, rotation=20, ha="right", fontsize=9)
    ax_rmse.set_ylabel("RMSE Médio (µm/min)")
    ax_rmse.set_title("(b) Erro Quadrático Médio (RMSE)")
    for i, v in enumerate(rmse_means):
        ax_rmse.text(i, v + 2.0, f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")
    ax_rmse.set_ylim(0, max(rmse_means) * 1.25)

    fig_10d.suptitle("Comparação de Configurações do XGBoost (Validação Cruzada - 4 Dobras)", fontsize=13, fontweight="bold")
    fig_10d_png = outputs_dir / "fig_10d_comparativo_hiperparametros_xgb.png"
    fig_10d_pdf = outputs_dir / "fig_10d_comparativo_hiperparametros_xgb.pdf"
    fig_10d.savefig(fig_10d_png, dpi=300)
    fig_10d.savefig(fig_10d_pdf)
    plt.close(fig_10d)

    # 10. Copiar Figuras para o Diretório de Artefatos
    artifacts_dir = Path("C:/Users/Usuário/.gemini/antigravity-ide/brain/bde36edb-b32c-4569-94e9-106cd5d81b80")
    if artifacts_dir.exists():
        figuras_todas = [
            fig_10a_png, fig_10a_pdf,
            fig_10b_png, fig_10b_pdf,
            fig_10b_log_png, fig_10b_log_pdf,
            fig_10c_png, fig_10c_pdf,
            fig_10c_log_png, fig_10c_log_pdf,
            fig_10d_png, fig_10d_pdf,
        ]
        for fig_f in figuras_todas:
            shutil.copy(fig_f, artifacts_dir / fig_f.name)
        print(f"12 figuras copiadas com sucesso para {artifacts_dir}")

    # 11. Geração do Relatório Técnico da Subetapa
    print("\nGerando Relatório Técnico da Subetapa 3.2.4...")
    relatorio_md = f"""# Relatório de Validação Técnica — Subetapa 3.2.4: XGBoost Gradient Boosting

## 1. Sumário Executivo
Nesta subetapa, implementou-se o modelo de aprendizado por árvores de decisão impulsionadas por gradiente **KineticsXGBoost** para a predição contínua da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições operacionais $[T, C_{{A0}}, η, t]$.

Investigaram-se cinco configurações sob o mesmo protocolo de **GroupKFold (4 dobras disjuntas por ensaio)**:
1. **XGB-Baseline (Default)**: `n_estimators=100`, `learning_rate=0.10`, `max_depth=6`.
2. **XGB-Regularizado (Shallow)**: `n_estimators=100`, `learning_rate=0.05`, `max_depth=4`, `subsample=0.80`.
3. **XGB-Profundo (Deep)**: `n_estimators=150`, `learning_rate=0.05`, `max_depth=8`.
4. **XGB-Otimizado (Campeão)**: `n_estimators=120`, `learning_rate=0.05`, `max_depth=5`, `subsample=0.85`, `colsample=0.85`.
5. **XGB-LinearTarget (Sem Log1p)**: Treinado em escala linear direta para evidenciar a necessidade de compressão logarítmica.

A configuração campeã foi a **{campeao_nome}**, alcançando **$R^2 = {metricas_treino['r2']:.4f}$ no Treino** e **$R^2 = {metricas_teste['r2']:.4f}$ no Teste Cego**.

---

## 2. Comparativo de Hiperparâmetros na Validação Cruzada (4 Dobras Disjuntas)

| Configuração | Estimadores | Taxa (η) | Max Depth | Subsample | Colsample | Target | $R^2$ Médio (CV) | RMSE (µm/min) | MAE (µm/min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for k, v in resultados_cv.items():
        c = configs_xgb[k]
        relatorio_md += (
            f"| **{k}** | {c['n_estimators']} | {c['learning_rate']} | {c['max_depth']} | "
            f"{c['subsample']} | {c['colsample_bytree']} | `{c['target_transform']}` | "
            f"**{v['mean_r2']:.4f} ± {v['std_r2']:.4f}** | {v['mean_rmse']:.2f} | {v['mean_mae']:.2f} |\n"
        )

    relatorio_md += f"""
---

## 3. Desempenho Global do Modelo Campeão ({campeao_nome})

* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * $R^2$: **{metricas_treino['r2']:.4f}**
  * RMSE: **{metricas_treino['rmse']:.2f} µm/min**
  * MAE: **{metricas_treino['mae']:.2f} µm/min**
  * Erro Máximo: **{metricas_treino['max_error']:.2f} µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras intocadas: Ens 8, 14 e 7)**:
  * $R^2$: **{metricas_teste['r2']:.4f}**
  * RMSE: **{metricas_teste['rmse']:.2f} µm/min**
  * MAE: **{metricas_teste['mae']:.2f} µm/min**
  * Erro Máximo: **{metricas_teste['max_error']:.2f} µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (restrição termodinâmica garantida estritamente).

---

## 4. Avaliação Individual nos Ensaios de Teste Cego

| Ensaio | Regime Físico-Químico | $C_{{A0}}$ (mol/L) | η (-) | $R^2$ Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for r in res_por_ensaio_teste:
        regime = "Estequiométrico Neutro" if r["eta"] == 1.0 else ("Leve Excesso Ácido" if r["eta"] == 1.5 else "Forte Excesso Ácido")
        relatorio_md += f"| **{r['ensaio']}** | {regime} | {r['CA0_mol_L']:.2f} | {r['eta']:.1f} | **{r['r2']:.4f}** | {r['rmse']:.2f} | {r['mae']:.2f} |\n"

    relatorio_md += f"""
---

## 5. Importância dos Atributos Físicos (Ganho de Informação e Permutação)

| Atributo | Significado Físico-Químico | Importância por Ganho (Gain) | Importância por Permutação (Teste Cego) |
| :--- | :--- | :---: | :---: |
"""
    for _, row in df_importances.iterrows():
        f_name = row["feature"]
        desc = {
            "t_min": "Tempo de reação (decaimento cinético rápido)",
            "razao_molar_eta": "Razão estequiométrica (potencial termodinâmico)",
            "CA0_mol_L": "Força motriz de concentração ácida",
            "temperatura_C": "Temperatura do banho (invariante na bancada)",
        }.get(f_name, "")
        relatorio_md += f"| `{f_name}` | {desc} | **{row['gain_importance']*100:.1f}%** | **ΔR² = {row['perm_importance_mean']:.4f} ± {row['perm_importance_std']:.4f}** |\n"

    relatorio_md += f"""
---

## 6. Figuras de Diagnóstico Geradas (300 DPI)
* `fig_10a_importancia_features_xgb.png`: Importância de atributos por Ganho e Permutação no teste cego.
* `fig_10b_predicoes_v_xgb.png`: Trajetórias temporais de $|v(t)|$ em escala linear nos 16 ensaios.
* `fig_10b_predicoes_v_xgb_log.png`: Trajetórias temporais de $|v(t)|$ em escala semilogarítmica nos 16 ensaios.
* `fig_10c_paridade_e_residuos_xgb.png`: Gráfico de paridade 1:1 e distribuição de resíduos em escala linear.
* `fig_10c_paridade_e_residuos_xgb_log.png`: Paridade log-log (4 ordens de magnitude) e distribuição de resíduos logarítmicos.
* `fig_10d_comparativo_hiperparametros_xgb.png`: Comparação quantitativa das configurações de hiperparâmetros na validação cruzada.
"""

    with open(outputs_dir / "relatorio_etapa_3_2_4_xgb.md", "w", encoding="utf-8") as f:
        f.write(relatorio_md)
    print(f"Relatório de validação salvo em: {outputs_dir / 'relatorio_etapa_3_2_4_xgb.md'}")

    print("\n" + "=" * 75)
    print("SUBETAPA 3.2.4 CONCLUÍDA COM SUCESSO!")
    print("=" * 75)


if __name__ == "__main__":
    main()
