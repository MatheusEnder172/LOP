"""
Painel 4x4 (um quadro por ensaio): white-box original (Bortot Coelho, 2017) x novo (LOP).
=========================================================================================

Original: RRB em massa (sem ÷ D³) + alpha = 5500 µm/min.
Novo:     RRB corrigida (f_n ∝ f_m / D³) + alpha = 0.

Cada quadro mostra X_Zn(t) de 0 a 15 min, os pontos experimentais, as duas curvas
e o teto estequiométrico min(1, η). RMSE em t > 0 no título (R² por ensaio não é
informativo: são 7 pontos quase constantes).

Saídas (Código/outputs/etapa_1_3/):
- fig_03_whitebox_original_vs_novo_4x4.png / .pdf  (300 DPI)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.physics.granulometry import RosinRammlerBennet, RosinRammlerMassaAntiga
from src.physics.kinetics import LeachingKinetics
from src.physics.pbm_batch import BatchPBMSolver

COR_FAB = "#D95F02"
COR_NOVO = "#1F5FA8"
COR_EXP = "#222222"


def main() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 10,
        "axes.grid": True, "grid.alpha": 0.35, "grid.linestyle": "--",
        "axes.spines.top": False, "axes.spines.right": False,
        "savefig.dpi": 300, "savefig.bbox": "tight",
    })
    base_dir = project_root.parent
    df_exp = pd.read_csv(base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv")
    out = base_dir / "Código" / "outputs" / "etapa_1_3"

    solver_novo = BatchPBMSolver(
        granulometry=RosinRammlerBennet(use_number_density_d3=True),
        kinetics=LeachingKinetics(alpha_nominal=0.0), n_mesh_points=5000)
    solver_fab = BatchPBMSolver(
        granulometry=RosinRammlerMassaAntiga(),
        kinetics=LeachingKinetics(alpha_nominal=5500.0), n_mesh_points=5000)

    t_fino = np.linspace(0.0, 15.0, 400)
    fig, axes = plt.subplots(4, 4, figsize=(17, 14), sharex=True, sharey=True)

    for ax, ens in zip(axes.flatten(), sorted(df_exp["ensaio"].unique())):
        d = df_exp[(df_exp["ensaio"] == ens) & (df_exp["t_min"] > 0)].sort_values("t_min")
        ca0 = float(d["CA0_mol_L"].iloc[0]); eta = float(d["razao_molar_eta"].iloc[0])
        t = d["t_min"].values; x = d["XZn"].values

        xf_pts = np.asarray(solver_fab.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"])
        xn_pts = np.asarray(solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"])
        rmse_f = np.sqrt(mean_squared_error(x, xf_pts)) * 100
        rmse_n = np.sqrt(mean_squared_error(x, xn_pts)) * 100
        xf = np.asarray(solver_fab.simulate(ca0=ca0, eta=eta, t_eval=t_fino)["XZn"])
        xn = np.asarray(solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_fino)["XZn"])

        ax.axhline(min(1.0, eta), color="gray", lw=1.0, ls=":")
        ax.plot(t_fino, xf, color=COR_FAB, lw=2.0, ls="--")
        ax.plot(t_fino, xn, color=COR_NOVO, lw=2.2)
        ax.plot(t, x, "o", color=COR_EXP, ms=5.5, mec="white", mew=0.6, zorder=5)

        melhor = COR_NOVO if rmse_n < rmse_f else COR_FAB
        ax.set_title(f"Ensaio {int(ens):02d} — C_A0 = {ca0:.2f} M, η = {eta:g}", fontweight="bold", fontsize=9.8)
        ax.text(0.97, 0.06, f"RMSE: {rmse_f:.1f}% → {rmse_n:.1f}%", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=9.2, color=melhor, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=melhor, lw=0.9))
        ax.set_xlim(-0.3, 15.5); ax.set_ylim(-0.02, 1.1)

    handles = [
        plt.Line2D([], [], marker="o", color=COR_EXP, ls="none", ms=7, label="Experimental"),
        plt.Line2D([], [], color=COR_FAB, ls="--", lw=2.2, label="Fabrício (RRB em massa, α = 5500 µm/min)"),
        plt.Line2D([], [], color=COR_NOVO, lw=2.4, label="Novo (RRB ÷ D³, α = 0)"),
        plt.Line2D([], [], color="gray", ls=":", lw=1.2, label="Teto estequiométrico min(1, η)"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, fontsize=11,
               bbox_to_anchor=(0.5, 0.965))
    fig.suptitle("White-box original (Bortot Coelho, 2017) × novo (RRB corrigida, sem α) — ensaio a ensaio",
                 fontweight="bold", fontsize=14.5, y=0.995)
    fig.supxlabel("Tempo de reação, t (min)", fontweight="bold", fontsize=12, y=0.02)
    fig.supylabel("Conversão de zinco, X_Zn (−)", fontweight="bold", fontsize=12, x=0.01)
    fig.text(0.5, 0.0, "Em cada quadro: RMSE (pontos percentuais de X_Zn, t > 0) do original → novo; "
             "em azul quando o novo erra menos, em laranja quando erra mais.",
             ha="center", fontsize=9.5, style="italic")
    fig.tight_layout(rect=(0.015, 0.03, 1, 0.945))
    fig.savefig(out / "fig_03_whitebox_original_vs_novo_4x4.png", dpi=300)
    fig.savefig(out / "fig_03_whitebox_original_vs_novo_4x4.pdf")
    plt.close(fig)
    print("OK:", out / "fig_03_whitebox_original_vs_novo_4x4.png")


if __name__ == "__main__":
    main()
