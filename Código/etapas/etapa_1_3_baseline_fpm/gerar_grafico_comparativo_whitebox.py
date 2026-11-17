"""
Gráfico-resumo: white-box original (Bortot Coelho, 2017) x white-box novo (LOP).
================================================================================

Original: RRB em massa (sem ÷ D³) + parâmetro de amortecimento alpha = 5500 µm/min.
Novo:     RRB corrigida (f_n ∝ f_m / D³) + alpha = 0.

Recalcula as duas simulações com o código atual (BatchPBMSolver) nos 16 ensaios
e métricas em t > 0 (112 pontos), como em simular_baseline_fpm.py.

Saídas (Código/outputs/etapa_1_3/):
- fig_03_resumo_whitebox_original_vs_novo.png / .pdf  (300 DPI)
- tabela_resumo_whitebox_original_vs_novo.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.physics.granulometry import RosinRammlerBennet, RosinRammlerMassaAntiga
from src.physics.kinetics import LeachingKinetics
from src.physics.pbm_batch import BatchPBMSolver

COR_FAB = "#D95F02"   # laranja
COR_NOVO = "#1F5FA8"  # azul
COR_EXP = "#222222"


def main() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10.5, "axes.titlesize": 11.5,
        "axes.labelsize": 10.5, "legend.fontsize": 9.5, "axes.grid": True,
        "grid.alpha": 0.35, "grid.linestyle": "--",
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

    linhas, y, p_fab, p_novo = [], [], [], []
    for ens in sorted(df_exp["ensaio"].unique()):
        d = df_exp[(df_exp["ensaio"] == ens) & (df_exp["t_min"] > 0)].sort_values("t_min")
        ca0 = float(d["CA0_mol_L"].iloc[0]); eta = float(d["razao_molar_eta"].iloc[0])
        t = d["t_min"].values; x = d["XZn"].values
        xf = np.asarray(solver_fab.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"])
        xn = np.asarray(solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"])
        y += list(x); p_fab += list(xf); p_novo += list(xn)
        linhas.append({
            "ensaio": int(ens), "eta": eta, "CA0_mol_L": ca0,
            "RMSE_fabricio": float(np.sqrt(mean_squared_error(x, xf))),
            "RMSE_novo": float(np.sqrt(mean_squared_error(x, xn))),
            "X_exp_15min": float(x[-1]), "X_fab_15min": float(xf[-1]), "X_novo_15min": float(xn[-1]),
        })
    df = pd.DataFrame(linhas)
    df["erro_patamar_fabricio"] = df["X_fab_15min"] - df["X_exp_15min"]
    df["erro_patamar_novo"] = df["X_novo_15min"] - df["X_exp_15min"]
    df.round(4).to_csv(out / "tabela_resumo_whitebox_original_vs_novo.csv", index=False)

    y, p_fab, p_novo = map(np.array, (y, p_fab, p_novo))
    met = {}
    for nome, p in (("fab", p_fab), ("novo", p_novo)):
        met[nome] = dict(r2=r2_score(y, p), rmse=np.sqrt(mean_squared_error(y, p)),
                         mae=mean_absolute_error(y, p))
    print(met)

    fig, ax = plt.subplots(2, 2, figsize=(13.5, 10))
    a, b, c, d_ = ax.flatten()

    # (a) paridade
    a.plot([0, 1.05], [0, 1.05], color="gray", lw=1.2, ls=":")
    a.scatter(y, p_fab, s=34, color=COR_FAB, alpha=0.75, edgecolor="white", lw=0.5,
              label=f"Fabrício (α = 5500): RMSE {met['fab']['rmse']*100:.1f}%")
    a.scatter(y, p_novo, s=34, color=COR_NOVO, alpha=0.75, edgecolor="white", lw=0.5,
              marker="s", label=f"Novo (RRB ÷ D³, α = 0): RMSE {met['novo']['rmse']*100:.1f}%")
    a.set_xlabel("X_Zn experimental"); a.set_ylabel("X_Zn do modelo")
    a.set_xlim(0.3, 1.05); a.set_ylim(0.3, 1.05); a.set_aspect("equal")
    a.set_title("(a) Paridade — 112 pontos (t > 0)", fontweight="bold")
    a.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=8.8)

    xs = np.arange(len(df)); w = 0.38
    rot = [f"{int(e)}\n{h:g}" for e, h in zip(df["ensaio"], df["eta"])]

    # (b) RMSE por ensaio
    b.bar(xs - w/2, df["RMSE_fabricio"] * 100, w, color=COR_FAB, label="Fabrício (α = 5500)")
    b.bar(xs + w/2, df["RMSE_novo"] * 100, w, color=COR_NOVO, label="Novo (RRB ÷ D³, α = 0)")
    b.set_xticks(xs); b.set_xticklabels(rot, fontsize=9)
    b.set_ylabel("RMSE (pontos percentuais de X_Zn)"); b.set_xlabel("Ensaio (linha de cima) e razão molar η (linha de baixo)")
    b.set_title("(b) Erro por ensaio", fontweight="bold"); b.legend(frameon=False)

    # (c) erro de patamar (t = 15 min)
    c.axhline(0, color="black", lw=0.9)
    c.bar(xs - w/2, df["erro_patamar_fabricio"] * 100, w, color=COR_FAB, label="Fabrício (α = 5500)")
    c.bar(xs + w/2, df["erro_patamar_novo"] * 100, w, color=COR_NOVO, label="Novo (RRB ÷ D³, α = 0)")
    c.set_xticks(xs); c.set_xticklabels(rot, fontsize=9)
    c.set_ylabel("X_Zn(15 min) modelo − experimental (p.p.)"); c.set_xlabel("Ensaio (linha de cima) e razão molar η (linha de baixo)")
    c.set_title("(c) Erro no patamar (t = 15 min)", fontweight="bold")
    c.set_ylim(-14, 20); c.legend(frameon=False, loc="upper left")

    # (d) métricas globais
    nomes = ["RMSE", "MAE"]
    vf = [met["fab"]["rmse"] * 100, met["fab"]["mae"] * 100]
    vn = [met["novo"]["rmse"] * 100, met["novo"]["mae"] * 100]
    xx = np.arange(2)
    bf = d_.bar(xx - w/2, vf, w, color=COR_FAB, label="Fabrício (α = 5500)")
    bn = d_.bar(xx + w/2, vn, w, color=COR_NOVO, label="Novo (RRB ÷ D³, α = 0)")
    for bars in (bf, bn):
        for r in bars:
            d_.text(r.get_x() + r.get_width()/2, r.get_height() + 0.15, f"{r.get_height():.2f}",
                    ha="center", fontsize=9.5)
    d_.set_xticks(xx); d_.set_xticklabels(nomes); d_.set_ylabel("%  (pontos percentuais de X_Zn)")
    red = (1 - met["novo"]["rmse"] / met["fab"]["rmse"]) * 100
    d_.set_title(f"(d) Global: RMSE {red:.0f}% menor; R² {met['fab']['r2']:.2f} → {met['novo']['r2']:.2f}",
                 fontweight="bold")
    d_.set_ylim(0, max(vf) * 1.25); d_.legend(frameon=False)

    fig.suptitle("White-box original (Bortot Coelho, 2017) × white-box novo (RRB corrigida, sem α)\n"
                 "16 ensaios de bancada, 112 pontos em t > 0", fontweight="bold", fontsize=13.5, y=1.0)
    fig.tight_layout()
    fig.savefig(out / "fig_03_resumo_whitebox_original_vs_novo.png", dpi=300)
    fig.savefig(out / "fig_03_resumo_whitebox_original_vs_novo.pdf")
    plt.close(fig)
    print("OK:", out / "fig_03_resumo_whitebox_original_vs_novo.png")


if __name__ == "__main__":
    main()
