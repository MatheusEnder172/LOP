"""
Geração do Painel 4x4 dos 16 Ensaios e Gráficos Individuais — Etapa 1.3.
========================================================================

Compara diretamente para cada um dos 16 ensaios de bancada:
1. Dados Experimentais (Bortot Coelho, 2017)
2. Baseline Antigo Histórico (RRB em massa sem ÷ D³, com α = 5500 µm/min)
3. Novo Baseline White-Box Puro Oficial (RRB ÷ D³, sem parâmetro α, α = 0 µm/min)

Gera:
- Painel consolidado 4x4: outputs/etapa_1_3/fig_03_ensaios_individuais_4x4.png e .pdf
- Gráficos individuais detalhados em: outputs/etapa_1_3/ensaios_individuais/
"""

from __future__ import annotations

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score

# Adicionar raiz do código ao path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.physics.granulometry import RosinRammlerBennet, RosinRammlerMassaAntiga
from src.physics.kinetics import LeachingKinetics
from src.physics.pbm_batch import BatchPBMSolver


def configurar_estilo() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10.0,
        "axes.titlesize": 11.0,
        "axes.labelsize": 10.5,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 8.8,
        "axes.grid": True,
        "grid.alpha": 0.40,
        "grid.linestyle": "--",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def main() -> None:
    configurar_estilo()
    base_dir = project_root.parent
    raw_data_path = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    metadata_path = base_dir / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv"
    output_dir = base_dir / "Código" / "outputs" / "etapa_1_3"
    indiv_dir = output_dir / "ensaios_individuais"
    output_dir.mkdir(parents=True, exist_ok=True)
    indiv_dir.mkdir(parents=True, exist_ok=True)

    df_exp = pd.read_csv(raw_data_path)
    df_meta = pd.read_csv(metadata_path).set_index("ensaio")

    solver_novo = BatchPBMSolver(
        granulometry=RosinRammlerBennet(use_number_density_d3=True),
        kinetics=LeachingKinetics(alpha_nominal=0.0),
        n_mesh_points=5000,
    )
    solver_antigo = BatchPBMSolver(
        granulometry=RosinRammlerMassaAntiga(),
        kinetics=LeachingKinetics(alpha_nominal=5500.0),
        n_mesh_points=5000,
    )

    ensaios_unicos = sorted(df_exp["ensaio"].unique())
    t_fine = np.linspace(0.0, 15.0, 300)

    # =========================================================================
    # 1. PAINEL CONSOLIDADO 4x4 DOS 16 ENSAIOS
    # =========================================================================
    fig_grid, axes_grid = plt.subplots(4, 4, figsize=(18, 15), sharex=True, sharey=True)
    axes_grid = axes_grid.flatten()

    for idx, ens in enumerate(ensaios_unicos):
        ax = axes_grid[idx]
        df_ens = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
        ca0 = float(df_ens["CA0_mol_L"].iloc[0])
        eta = float(df_ens["razao_molar_eta"].iloc[0])
        df_ens_pos = df_ens[df_ens["t_min"] > 0.0]
        t_exp = df_ens_pos["t_min"].values
        x_exp = df_ens_pos["XZn"].values

        # Simulações (avaliadas em t > 0 para métricas e resíduos; t_fine parte de t=0 com XZn(0)=0 hardcoded)
        res_novo_exp = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_exp)
        res_novo_fine = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_fine)

        res_ant_exp = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_exp)
        res_ant_fine = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_fine)

        r2_novo = float(r2_score(x_exp, res_novo_exp["XZn"]))
        rmse_novo = float(np.sqrt(mean_squared_error(x_exp, res_novo_exp["XZn"])))

        r2_ant = float(r2_score(x_exp, res_ant_exp["XZn"]))
        rmse_ant = float(np.sqrt(mean_squared_error(x_exp, res_ant_exp["XZn"])))

        # Plot no grid
        ax.plot(
            t_exp,
            x_exp,
            color="black",
            marker="o",
            markersize=5.8,
            linestyle="none",
            zorder=6,
            label="Dados Experimentais" if idx == 0 else "",
        )
        ax.plot(
            t_fine,
            res_ant_fine["XZn"],
            color="#1f77b4",
            linestyle="--",
            linewidth=1.8,
            zorder=4,
            label="Baseline Antigo (Massa, α=5500)" if idx == 0 else "",
        )
        ax.plot(
            t_fine,
            res_novo_fine["XZn"],
            color="#d62728",
            linestyle="-",
            linewidth=2.3,
            zorder=5,
            label="Novo Baseline Oficial (RRB ÷ D³, Sem α)" if idx == 0 else "",
        )

        ax.set_title(
            f"Ensaio {ens:02d} (C_A0={ca0:.2f} M, η={eta:.1f})\n"
            f"R²: {r2_ant:.3f} → {r2_novo:.3f} | RMSE: {rmse_ant*100:.1f}% → {rmse_novo*100:.1f}%",
            fontsize=9.2,
            fontweight="bold",
        )
        ax.set_xlim(-0.4, 15.5)
        ax.set_ylim(-0.03, 1.06)

        # =====================================================================
        # 2. GRÁFICO INDIVIDUAL DETALHADO POR ENSAIO (COM PAINEL DE RESÍDUOS)
        # =====================================================================
        meta_row = df_meta.loc[ens]
        sl = float(meta_row["razao_solido_liquido_g_L"])

        fig_ind, (ax_main, ax_res) = plt.subplots(
            2, 1, figsize=(9.5, 7.0), sharex=True, gridspec_kw={"height_ratios": [3.2, 1.2]}
        )

        ax_main.plot(t_exp, x_exp, color="black", marker="o", markersize=7.0, linestyle="none", zorder=6, label="Dados Experimentais")
        ax_main.plot(t_fine, res_ant_fine["XZn"], color="#1f77b4", linestyle="--", linewidth=2.0, label=f"Baseline Antigo (α=5500) — R² = {r2_ant:.4f}")
        ax_main.plot(t_fine, res_novo_fine["XZn"], color="#d62728", linestyle="-", linewidth=2.4, label=f"Novo Baseline (RRB ÷ D³, Sem α) — R² = {r2_novo:.4f}")
        ax_main.set_title(
            f"Ensaio {ens:02d} — C_A0 = {ca0:.2f} mol/L | η = {eta:.1f} | S/L = {sl:.1f} g/L\n"
            f"Evolução do R²: {r2_ant:.4f} → {r2_novo:.4f} (RMSE: {rmse_ant*100:.2f}% → {rmse_novo*100:.2f}%)",
            fontweight="bold",
        )
        ax_main.set_ylabel("Conversão de Zinco, X_Zn (-)", fontweight="bold")
        ax_main.set_ylim(-0.02, 1.05)
        ax_main.legend(loc="lower right", frameon=True, facecolor="white")

        # Painel inferior de resíduos
        res_ant_pts = (res_ant_exp["XZn"] - x_exp) * 100.0
        res_novo_pts = (res_novo_exp["XZn"] - x_exp) * 100.0
        ax_res.plot(t_exp, res_ant_pts, color="#1f77b4", marker="s", linestyle="--", label="Resíduo Antigo (%)")
        ax_res.plot(t_exp, res_novo_pts, color="#d62728", marker="o", linestyle="-", label="Resíduo Novo (%)")
        ax_res.axhline(0.0, color="black", linestyle="--", linewidth=1.0)
        ax_res.axhline(5.0, color="gray", linestyle=":", linewidth=0.8)
        ax_res.axhline(-5.0, color="gray", linestyle=":", linewidth=0.8)
        ax_res.set_ylabel("Resíduo (p.p.)", fontweight="bold")
        ax_res.set_xlabel("Tempo de Reação, t (min)", fontweight="bold")
        ax_res.set_xlim(-0.3, 15.3)
        ax_res.legend(loc="upper right", frameon=True, facecolor="white", fontsize=8.0)

        plt.tight_layout()
        indiv_png = indiv_dir / f"ensaio_{ens:02d}_comparativo_baseline.png"
        indiv_pdf = indiv_dir / f"ensaio_{ens:02d}_comparativo_baseline.pdf"
        fig_ind.savefig(indiv_png, dpi=300)
        fig_ind.savefig(indiv_pdf)
        plt.close(fig_ind)

    # Legenda comum do painel 4x4
    handles, labels = axes_grid[0].get_legend_handles_labels()
    fig_grid.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.945),
        ncol=3,
        fontsize=11.5,
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
    )
    fig_grid.text(0.5, 0.02, "Tempo de Reação, t (min)", ha="center", fontsize=13, fontweight="bold")
    fig_grid.text(
        0.02,
        0.5,
        "Conversão Mássica de Zinco, X_Zn (-)",
        va="center",
        rotation="vertical",
        fontsize=13,
        fontweight="bold",
    )
    fig_grid.suptitle(
        "Etapa 1.3 — Painel Ensaio a Ensaio (16 Ensaios de Bancada): Baseline Antigo vs. Novo Baseline White-Box Puro",
        fontsize=14.5,
        fontweight="bold",
        y=0.98,
    )
    plt.subplots_adjust(top=0.89, bottom=0.06, left=0.06, right=0.98, hspace=0.35, wspace=0.14)

    grid_png = output_dir / "fig_03_ensaios_individuais_4x4.png"
    grid_pdf = output_dir / "fig_03_ensaios_individuais_4x4.pdf"
    fig_grid.savefig(grid_png, dpi=300)
    fig_grid.savefig(grid_pdf)
    plt.close(fig_grid)

    print(f"[OK] Painel 4x4 consolidado salvo em: {grid_png}")
    print(f"[OK] 16 Gráficos individuais salvos em: {indiv_dir}")


if __name__ == "__main__":
    main()
