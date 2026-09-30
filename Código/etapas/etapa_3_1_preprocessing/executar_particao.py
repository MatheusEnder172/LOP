"""Script de Execução da Etapa 3.1: Partição e Pré-Processamento dos Dados.

Executa:
1. Separação 85/15: 13 ensaios para Treino (81,25%) e 3 ensaios para Teste Cego (18,75%: Ensaios 8, 14 e 7).
2. Validação da integridade e ausência de vazamento de dados (zero leakage).
3. Geração das 4 dobras de validação cruzada (GroupKFold) no conjunto de treino.
4. Ajuste do escalonador Z-score (StandardScaler) exclusivamente nos dados de treino.
5. Exportação dos datasets particionados e transformadores serializados.
6. Geração da Tabela de Partição e da Figura Científica fig_06 (300 DPI, PNG + PDF).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Importar módulos do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.ml.preprocessing import DataPartitioner, FeatureTargetScaler


def main() -> None:
    print("=" * 70)
    print("ETAPA 3.1: PARTIÇÃO DE DADOS E PRÉ-PROCESSAMENTO (85/15)")
    print("=" * 70)

    # Diretórios
    data_dir = BASE_DIR.parent / "Base de dados" / "processed"
    splits_dir = data_dir / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    outputs_dir = BASE_DIR / "outputs" / "etapa_3_1"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Carregar datasets
    dense_path = data_dir / "alvos_v_treinamento_denso.csv"
    exp_path = data_dir / "alvos_v_treinamento.csv"
    params_path = data_dir / "parametros_otimizacao_inversa.csv"

    assert dense_path.exists(), f"Arquivo não encontrado: {dense_path}"
    assert exp_path.exists(), f"Arquivo não encontrado: {exp_path}"
    assert params_path.exists(), f"Arquivo não encontrado: {params_path}"

    df_dense = pd.read_csv(dense_path)
    df_exp = pd.read_csv(exp_path)
    df_params = pd.read_csv(params_path)

    print(f"Dataset denso carregado: {len(df_dense)} registros ({len(df_dense['ensaio'].unique())} ensaios)")
    print(f"Dataset pontual carregado: {len(df_exp)} registros ({len(df_exp['ensaio'].unique())} ensaios)")

    # 2. Configurar Particionador
    test_ensaios = [7, 8, 14]
    partitioner = DataPartitioner(test_ensaios=test_ensaios)

    train_dense, test_dense = partitioner.split_dataframe(df_dense)
    train_exp, test_exp = partitioner.split_dataframe(df_exp)

    print("\n--- Separação dos Ensaios ---")
    train_ensaios = sorted(train_dense["ensaio"].unique())
    print(f"Ensaios de Treino ({len(train_ensaios)} ensaios - {len(train_dense)} amostras densas, {len(train_exp)} pontuais):")
    print(f"  {train_ensaios}")
    print(f"Ensaios de Teste Cego ({len(test_ensaios)} ensaios - {len(test_dense)} amostras densas, {len(test_exp)} pontuais):")
    print(f"  {test_ensaios}")

    # Validação de vazamento
    leakage = set(train_ensaios).intersection(set(test_ensaios))
    assert len(leakage) == 0, f"Erro crítico: Vazamento de dados detectado! {leakage}"
    print("Vazamento de dados: ZERO (conjuntos disjuntos comprovados).")

    # 3. Gerar e salvar dobras de Validação Cruzada (GroupKFold) no Treino
    X_train_d, y_train_d, groups_train_d = partitioner.extract_xy(train_dense)
    cv_folds = partitioner.get_cv_folds(train_dense, n_splits=4)

    cv_folds_info: List[Dict[str, Any]] = []
    print("\n--- Dobras de Validação Cruzada (GroupKFold, 4 folds) ---")
    for fold_idx, (tr_idx, val_idx) in enumerate(cv_folds, 1):
        tr_ens = sorted(train_dense.iloc[tr_idx]["ensaio"].unique())
        val_ens = sorted(train_dense.iloc[val_idx]["ensaio"].unique())
        print(f"Fold {fold_idx}:")
        print(f"  Treino ({len(tr_ens)} ensaios, {len(tr_idx)} amostras): {tr_ens}")
        print(f"  Validação ({len(val_ens)} ensaios, {len(val_idx)} amostras): {val_ens}")

        cv_folds_info.append(
            {
                "fold": fold_idx,
                "n_train_samples": int(len(tr_idx)),
                "n_val_samples": int(len(val_idx)),
                "train_ensaios": [int(e) for e in tr_ens],
                "val_ensaios": [int(e) for e in val_ens],
            }
        )

    with open(splits_dir / "cv_folds_info.json", "w", encoding="utf-8") as f:
        json.dump(cv_folds_info, f, indent=2, ensure_ascii=False)
    print("Informações das dobras salvas em: splits/cv_folds_info.json")

    # 4. Ajustar Scalers estritamente nos dados de treino
    scaler = FeatureTargetScaler()
    scaler.fit(X_train_d, y_train_d)
    scaler.save(splits_dir / "scalers.joblib")
    print("Scalers ajustados no treino e salvos em: splits/scalers.joblib")
    print(f"  Média das features (X_mean): {np.round(scaler.scaler_X.mean_, 4)}")
    print(f"  Desvio das features (X_scale): {np.round(scaler.scaler_X.scale_, 4)}")
    print(f"  Média do target (y_mean): {float(scaler.scaler_y.mean_[0]):.4f} um/min")
    print(f"  Desvio do target (y_scale): {float(scaler.scaler_y.scale_[0]):.4f} um/min")

    # 5. Salvar datasets particionados
    train_dense.to_csv(splits_dir / "train_dense.csv", index=False)
    test_dense.to_csv(splits_dir / "test_dense.csv", index=False)
    train_exp.to_csv(splits_dir / "train_exp.csv", index=False)
    test_exp.to_csv(splits_dir / "test_exp.csv", index=False)
    print("Splits de dados exportados com sucesso em Base de dados/processed/splits/")

    # 6. Tabela detalhada de partição por ensaio
    tabela_ensaios = []
    for _, row in df_params.iterrows():
        ens = int(row["ensaio"])
        part = "Teste Cego" if ens in test_ensaios else "Treino"
        tabela_ensaios.append(
            {
                "ensaio": ens,
                "particao": part,
                "temperatura_C": row["temperatura_C"],
                "CA0_mol_L": row["CA0_mol_L"],
                "razao_molar_eta": row["razao_molar_eta"],
                "amostras_densas": 61,
                "amostras_pontuais": 8,
                "R2_otim_inversa": row["R2"],
                "RMSE_otim_inversa": row["RMSE"],
                "v0_um_min": row["v0_um_min"],
                "v_final_um_min": row["v_final_um_min"],
                "delta_final_um": row["delta_final_um"],
            }
        )

    df_tabela = pd.DataFrame(tabela_ensaios).sort_values(["particao", "ensaio"])
    df_tabela.to_csv(outputs_dir / "tabela_particao_splits.csv", index=False)
    print(f"Tabela de partição salva em: {outputs_dir / 'tabela_particao_splits.csv'}")

    # 7. Gerar Figura Científica 300 DPI (PNG + PDF)
    gerar_figura_particao(df_params, df_dense, test_ensaios, outputs_dir)

    print("\nEtapa 3.1 concluída com sucesso!")


def gerar_figura_particao(
    df_params: pd.DataFrame,
    df_dense: pd.DataFrame,
    test_ensaios: List[int],
    outputs_dir: Path,
) -> None:
    """Gera a figura de diagnóstico da partição experimental em 300 DPI."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 9,
            "figure.titlesize": 13,
        }
    )

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.25)

    cor_treino = "#1f77b4"  # Azul escuro
    cor_teste = "#d62728"   # Vermelho destaque

    # --- PAINEL (a): Espaço Experimental Fatorial 4x4 (Convex Hull) ---
    ax_a = fig.add_subplot(gs[0, 0])

    for _, row in df_params.iterrows():
        ens = int(row["ensaio"])
        ca0 = row["CA0_mol_L"]
        eta = row["razao_molar_eta"]

        if ens in test_ensaios:
            ax_a.scatter(
                ca0,
                eta,
                color=cor_teste,
                s=200,
                marker="*",
                edgecolors="black",
                linewidth=1.2,
                zorder=5,
            )
            # Offset customizado para cada ensaio de teste evitar colisões
            offset_y = -16 if ens == 7 else (12 if ens == 14 else 12)
            offset_x = 0
            ax_a.annotate(
                f"Ens {ens} (Teste)",
                (ca0, eta),
                textcoords="offset points",
                xytext=(offset_x, offset_y),
                ha="center",
                fontsize=8.5,
                fontweight="bold",
                color=cor_teste,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.8, edgecolor="none"),
            )
        else:
            ax_a.scatter(
                ca0,
                eta,
                color=cor_treino,
                s=80,
                marker="o",
                alpha=0.85,
                edgecolors="navy",
                linewidth=1.0,
                zorder=4,
            )
            offset_y = 10 if (ca0 == 0.10 and eta == 3.1) else -14
            ax_a.annotate(
                f"Ens {ens}",
                (ca0, eta),
                textcoords="offset points",
                xytext=(0, offset_y),
                ha="center",
                fontsize=8,
                color="#333333",
            )

    # Linhas de grade e limites
    ax_a.set_xticks([0.10, 0.50, 1.00, 1.50])
    ax_a.set_yticks([0.5, 1.0, 1.5, 3.1])
    ax_a.set_xlim(-0.05, 1.65)
    ax_a.set_ylim(0.2, 3.55)
    ax_a.grid(True, linestyle="--", alpha=0.5)
    ax_a.set_xlabel(r"$C_{A0}\ (\mathrm{mol}\cdot\mathrm{L}^{-1})$ — Concentração Inicial de Ácido")
    ax_a.set_ylabel(r"$\eta\ (-)$ — Razão Molar Estequiométrica")
    ax_a.set_title("(a) Matriz Fatorial 4×4 e Preservação do Envoltório Convexo")

    # Linha tracejada indicando convex hull
    hull_x = [0.10, 1.50, 1.50, 0.10, 0.10]
    hull_y = [0.5, 0.5, 3.1, 3.1, 0.5]
    ax_a.plot(hull_x, hull_y, ":", color="gray", linewidth=1.5, label="Envoltório Convexo (Borda)", zorder=2)

    # Legenda customizada posicionada na área livre entre eta=1.5 e eta=3.1
    ax_a.scatter([], [], color=cor_treino, s=80, marker="o", label="Treino (13 ensaios — 81,25%)")
    ax_a.scatter([], [], color=cor_teste, s=180, marker="*", edgecolors="black", label="Teste Cego (3 ensaios — 18,75%)")
    ax_a.legend(loc="upper left", bbox_to_anchor=(0.28, 0.77), framealpha=0.92, fontsize=8.5)

    # --- PAINEL (b): Curvas de Taxa Interfacial |v(t)| ---
    ax_b = fig.add_subplot(gs[0, 1])

    # Plotar primeiro todos os de treino
    for ens in sorted(df_dense["ensaio"].unique()):
        if ens not in test_ensaios:
            df_sub = df_dense[df_dense["ensaio"] == ens].sort_values("t_min")
            ax_b.plot(
                df_sub["t_min"].values,
                df_sub["abs_v_alvo_um_min"].values,
                color=cor_treino,
                linewidth=1.0,
                alpha=0.40,
                linestyle="--",
                label="Treino (13 ensaios)" if ens == 1 else None,
                zorder=3,
            )

    # Plotar ensaios de teste com cores e estilos diferenciados
    estilos_teste = {
        7: ("-", 2.2, "Ens 7 (η=3,1, CA0=0,50)"),
        8: ("-.", 2.2, "Ens 8 (η=1,0, CA0=0,50)"),
        14: (":", 2.5, "Ens 14 (η=1,5, CA0=1,00)"),
    }
    for ens in test_ensaios:
        df_sub = df_dense[df_dense["ensaio"] == ens].sort_values("t_min")
        ls, lw, label_str = estilos_teste[ens]
        ax_b.plot(
            df_sub["t_min"].values,
            df_sub["abs_v_alvo_um_min"].values,
            color=cor_teste,
            linewidth=lw,
            linestyle=ls,
            label=f"Teste Cego: {label_str}",
            zorder=5,
        )

    ax_b.set_xlabel(r"$t\ (\mathrm{min})$ — Tempo de Reação")
    ax_b.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m}\cdot\mathrm{min}^{-1})$ — Taxa de Encolhimento")
    ax_b.set_title("(b) Perfis Temporais da Variável Alvo |v(t)|")
    ax_b.grid(True, linestyle="--", alpha=0.5)
    ax_b.set_xlim(-0.5, 16.0)
    ax_b.set_ylim(-15, 1300)
    ax_b.legend(loc="upper right", framealpha=0.92, fontsize=8.5)

    # --- PAINEL (c): Curvas Reconstruídas de Conversão X_Zn(t) ---
    ax_c = fig.add_subplot(gs[1, 0])

    for ens in sorted(df_dense["ensaio"].unique()):
        if ens not in test_ensaios:
            df_sub = df_dense[df_dense["ensaio"] == ens].sort_values("t_min")
            ax_c.plot(
                df_sub["t_min"].values,
                df_sub["XZn_reconstruido"].values * 100,
                color=cor_treino,
                linewidth=1.0,
                alpha=0.40,
                linestyle="--",
                label="Treino (13 ensaios)" if ens == 1 else None,
                zorder=3,
            )

    offsets_c = {7: 1.5, 14: -2.5, 8: 0.0}
    for ens in test_ensaios:
        df_sub = df_dense[df_dense["ensaio"] == ens].sort_values("t_min")
        ls, lw, label_str = estilos_teste[ens]
        t = df_sub["t_min"].values
        x = df_sub["XZn_reconstruido"].values * 100
        ax_c.plot(
            t,
            x,
            color=cor_teste,
            linewidth=lw,
            linestyle=ls,
            label=f"Teste: Ens {ens}",
            zorder=5,
        )
        ax_c.text(
            t[-1] + 0.25,
            x[-1] + offsets_c[ens],
            f"Ens {ens}",
            color=cor_teste,
            fontsize=8.5,
            fontweight="bold",
            va="center",
        )

    # Linhas de referência de patamares
    ax_c.axhline(50, color="#888888", linestyle=":", linewidth=1.0)
    ax_c.text(0.5, 52, r"$\eta=0,5$ (Patamar $\approx 50\%$)", fontsize=8, color="#555555")
    ax_c.axhline(87, color="#888888", linestyle=":", linewidth=1.0)
    ax_c.text(0.5, 89, r"$\eta=1,0$ (Patamar $\approx 87\%$)", fontsize=8, color="#555555")
    ax_c.axhline(100, color="#888888", linestyle=":", linewidth=1.0)
    ax_c.text(0.5, 102, r"$\eta=3,1$ (Dissolução Total)", fontsize=8, color="#555555")

    ax_c.set_xlabel(r"$t\ (\mathrm{min})$ — Tempo de Reação")
    ax_c.set_ylabel(r"$X_{\mathrm{Zn}}\ (\%)$ — Conversão de Zinco Reconstruída")
    ax_c.set_title("(c) Dinâmica de Conversão por Regime Químico")
    ax_c.grid(True, linestyle="--", alpha=0.5)
    ax_c.set_xlim(-0.5, 17.5)
    ax_c.set_ylim(-2, 108)
    ax_c.legend(loc="lower right", framealpha=0.92, fontsize=8.5)

    # --- PAINEL (d): Distribuição do Target |v| no Treino vs Teste Cego ---
    ax_d = fig.add_subplot(gs[1, 1])

    train_mask = ~df_dense["ensaio"].isin(test_ensaios)
    v_train = df_dense[train_mask]["abs_v_alvo_um_min"].values
    v_test = df_dense[~train_mask]["abs_v_alvo_um_min"].values

    bp = ax_d.boxplot(
        [v_train, v_test],
        positions=[1, 2],
        widths=0.45,
        patch_artist=True,
        showmeans=True,
        meanline=True,
    )

    bp["boxes"][0].set(facecolor=cor_treino, alpha=0.7, edgecolor="navy")
    bp["boxes"][1].set(facecolor=cor_teste, alpha=0.7, edgecolor="darkred")
    bp["medians"][0].set(color="black", linewidth=1.5)
    bp["medians"][1].set(color="black", linewidth=1.5)
    bp["means"][0].set(color="darkblue", linestyle="--", linewidth=1.5)
    bp["means"][1].set(color="darkred", linestyle="--", linewidth=1.5)

    ax_d.set_xticks([1, 2])
    ax_d.set_xticklabels(
        [f"Treino\n(13 ensaios | N = {len(v_train)})", f"Teste Cego\n(3 ensaios | N = {len(v_test)})"]
    )
    ax_d.set_ylabel(r"$|v|\ (\mu\mathrm{m}\cdot\mathrm{min}^{-1})$")
    ax_d.set_title(r"(d) Distribuição e Suporte Estatístico do Target $|v|$")
    ax_d.grid(True, linestyle="--", alpha=0.5)

    # Anotações estatísticas
    stats_text = (
        f"Treino: Média = {v_train.mean():.1f}, Mediana = {np.median(v_train):.1f}, Máx = {v_train.max():.1f} μm/min\n"
        f"Teste:  Média = {v_test.mean():.1f}, Mediana = {np.median(v_test):.1f}, Máx = {v_test.max():.1f} μm/min"
    )
    ax_d.text(
        0.05,
        0.88,
        stats_text,
        transform=ax_d.transAxes,
        fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9, edgecolor="#cccccc"),
    )

    # Salvar em 300 DPI
    png_path = outputs_dir / "fig_06_particao_espaco_experimental.png"
    pdf_path = outputs_dir / "fig_06_particao_espaco_experimental.pdf"

    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Figura salva em 300 DPI:\n  {png_path}\n  {pdf_path}")


if __name__ == "__main__":
    main()
