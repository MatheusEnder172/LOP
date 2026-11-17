"""Comparativo dos quatro modelos nos 16 ensaios (in-domain, t > 0).
==================================================================

1. White-box do Fabrício (Bortot Coelho, 2017): RRB em massa + α = 5500 µm/min.
2. White-box novo (LOP): RRB ÷ D³, α = 0.
3. MLP pura (Subetapa 3.2.7): (C_A0, η, t) → X_Zn direto, sem PBM.
4. Híbrido serial (MLP v2, comitê de 10 em ν → PBM): modelo final do projeto.

Só lê modelos congelados (nenhum treino aqui). Teste cego = ensaios 7, 8 e 14.

Saídas em Código/outputs/etapa_4_2_avaliacao_indomain/:
- fig_13a_comparativo_4_modelos_4x4.png/.pdf
- fig_13b_comparativo_4_modelos_resumo.png/.pdf
- tabela_comparativo_4_modelos_por_ensaio.csv, tabela_comparativo_4_modelos_global.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.hybrid.serial_hybrid import SerialHybridModel
from src.physics.granulometry import RosinRammlerBennet, RosinRammlerMassaAntiga
from src.physics.kinetics import LeachingKinetics
from src.physics.pbm_batch import BatchPBMSolver

OUT = project_root / "outputs" / "etapa_4_2_avaliacao_indomain"
PURO_DIR = project_root / "outputs" / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"
RAW = project_root.parent / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
ENSAIOS_TESTE = [7, 8, 14]

MODELOS = [  # chave, rótulo, cor
    ("fab", "White-box do Fabrício (α = 5500)", "#D95F02"),
    ("novo", "White-box novo (RRB ÷ D³, α = 0)", "#1F5FA8"),
    ("puro", "MLP pura (X_Zn direto)", "#1B9E77"),
    ("hib", "Híbrido serial (MLP v2 → PBM)", "#7B2D8E"),
]


def rmse(y, p) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


def main() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.grid": True, "grid.alpha": 0.35,
        "grid.linestyle": "--", "axes.spines.top": False, "axes.spines.right": False,
        "savefig.dpi": 300, "savefig.bbox": "tight",
    })
    exp = pd.read_csv(RAW)
    exp_pos = exp[exp["t_min"] > 0].sort_values(["ensaio", "t_min"])
    puro_pts = pd.read_csv(PURO_DIR / "predicoes_pontos_experimentais.csv")
    puro_dense = pd.read_csv(PURO_DIR / "curvas_densas_mlp_puro.csv")

    sol_novo = BatchPBMSolver(granulometry=RosinRammlerBennet(use_number_density_d3=True),
                              kinetics=LeachingKinetics(alpha_nominal=0.0), n_mesh_points=5000)
    sol_fab = BatchPBMSolver(granulometry=RosinRammlerMassaAntiga(),
                             kinetics=LeachingKinetics(alpha_nominal=5500.0), n_mesh_points=5000)
    hib = SerialHybridModel(model_type="mlp_v2")

    t_fino = np.linspace(0.0, 15.0, 301)
    ensaios = sorted(exp["ensaio"].unique())
    curvas, pontos, linhas = {}, [], []

    for e in ensaios:
        d = exp_pos[exp_pos["ensaio"] == e]
        ca0, eta = float(d["CA0_mol_L"].iloc[0]), float(d["razao_molar_eta"].iloc[0])
        t, x = d["t_min"].values, d["XZn"].values
        p_fab = np.asarray(sol_fab.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"])
        p_novo = np.asarray(sol_novo.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"])
        p_hib = np.asarray(hib.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t)["XZn"])
        p_puro = puro_pts[puro_pts["ensaio"] == e].sort_values("t_min")["XZn_pred"].values
        assert len(p_puro) == len(t)
        part = "Teste cego" if e in ENSAIOS_TESTE else "Treino"
        for k, p in (("fab", p_fab), ("novo", p_novo), ("puro", p_puro), ("hib", p_hib)):
            for ti, xi, pi in zip(t, x, p):
                pontos.append({"ensaio": e, "particao": part, "modelo": k, "t_min": ti, "XZn_exp": xi, "XZn_pred": pi})
        linhas.append({"ensaio": e, "particao": part, "CA0_mol_L": ca0, "eta": eta,
                       **{f"RMSE_{k}": rmse(x, p) for k, p in (("fab", p_fab), ("novo", p_novo), ("puro", p_puro), ("hib", p_hib))}})

        hm = hib.simulate_members(T=40.0, ca0=ca0, eta=eta, t_eval=t_fino)
        curvas[e] = {
            "fab": np.asarray(sol_fab.simulate(ca0=ca0, eta=eta, t_eval=t_fino)["XZn"]),
            "novo": np.asarray(sol_novo.simulate(ca0=ca0, eta=eta, t_eval=t_fino)["XZn"]),
            "hib": np.asarray(hib.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t_fino)["XZn"]),
            "hib_lo": np.asarray(hm["XZn_min"]), "hib_hi": np.asarray(hm["XZn_max"]),
            "ca0": ca0, "eta": eta, "t": t, "x": x,
        }

    por_ens = pd.DataFrame(linhas)
    por_ens.round(5).to_csv(OUT / "tabela_comparativo_4_modelos_por_ensaio.csv", index=False)
    pts = pd.DataFrame(pontos)
    glob = []
    for nome, sel in (("Treino (13 ensaios, 91 pts)", pts["particao"] == "Treino"),
                      ("Teste cego (3 ensaios, 21 pts)", pts["particao"] == "Teste cego"),
                      ("Global (16 ensaios, 112 pts)", pts["particao"].notna())):
        linha = {"particao": nome}
        for k, _, _ in MODELOS:
            g = pts[sel & (pts["modelo"] == k)]
            linha[f"RMSE_{k}"] = rmse(g["XZn_exp"], g["XZn_pred"])
            ss = np.sum((g["XZn_exp"] - g["XZn_pred"]) ** 2); st = np.sum((g["XZn_exp"] - g["XZn_exp"].mean()) ** 2)
            linha[f"R2_{k}"] = float(1 - ss / st)
        glob.append(linha)
    tab_glob = pd.DataFrame(glob)
    tab_glob.round(5).to_csv(OUT / "tabela_comparativo_4_modelos_global.csv", index=False)
    print(tab_glob.round(4).to_string())

    # ---------------- Figura 13a: 4x4 ----------------
    fig, axes = plt.subplots(4, 4, figsize=(18, 15), sharex=True, sharey=True)
    for ax, e in zip(axes.flatten(), ensaios):
        c = curvas[e]
        r = por_ens[por_ens["ensaio"] == e].iloc[0]
        cego = e in ENSAIOS_TESTE
        ax.axhline(min(1.0, c["eta"]), color="gray", lw=1.0, ls=":")
        ax.plot(t_fino, c["fab"], color=MODELOS[0][2], lw=1.8, ls="--")
        ax.plot(t_fino, c["novo"], color=MODELOS[1][2], lw=1.8)
        ax.fill_between(t_fino, c["hib_lo"], c["hib_hi"], color=MODELOS[3][2], alpha=0.18, lw=0)
        ax.plot(t_fino, c["hib"], color=MODELOS[3][2], lw=2.4)
        pd_e = puro_dense[puro_dense["ensaio"] == e]
        ax.plot(pd_e["t_min"], pd_e["XZn_pred"], color=MODELOS[2][2], lw=2.0, ls="-.")
        ax.plot(c["t"], c["x"], "o", color="#222222", ms=5.2, mec="white", mew=0.6, zorder=6)
        ax.set_title(f"Ensaio {e:02d} — C_A0 = {c['ca0']:.2f} M, η = {c['eta']:g}" + ("  [TESTE CEGO]" if cego else ""),
                     fontweight="bold", fontsize=9.6, color="#B22222" if cego else "black")
        vals = [r["RMSE_fab"], r["RMSE_novo"], r["RMSE_puro"], r["RMSE_hib"]]
        melhor = int(np.argmin(vals))
        ax.add_patch(plt.Rectangle((0.43, 0.025), 0.55, 0.30, transform=ax.transAxes, fc="white", ec="#bbbbbb", lw=0.8, zorder=7))
        for i, ((k, nome, cor), v) in enumerate(zip(MODELOS, vals)):
            curto = ["Fabrício", "WB novo", "MLP pura", "Híbrido"][i]
            ax.text(0.455, 0.285 - 0.067 * i, f"{curto}: {v*100:.1f}%" + ("  ★" if i == melhor else ""),
                    transform=ax.transAxes, fontsize=8.6, color=cor, fontweight="bold" if i == melhor else "normal", zorder=8)
        ax.set_xlim(-0.3, 15.5); ax.set_ylim(-0.02, 1.1)

    handles = [plt.Line2D([], [], marker="o", color="#222222", ls="none", ms=7, label="Experimental"),
               plt.Line2D([], [], color=MODELOS[0][2], ls="--", lw=2.2, label=MODELOS[0][1]),
               plt.Line2D([], [], color=MODELOS[1][2], lw=2.2, label=MODELOS[1][1]),
               plt.Line2D([], [], color=MODELOS[2][2], ls="-.", lw=2.2, label=MODELOS[2][1]),
               plt.Line2D([], [], color=MODELOS[3][2], lw=2.6, label=MODELOS[3][1]),
               plt.Line2D([], [], color="gray", ls=":", lw=1.2, label="Teto min(1, η)")]
    fig.legend(handles=handles, loc="upper center", ncol=6, frameon=False, fontsize=10.5, bbox_to_anchor=(0.5, 0.968))
    g = tab_glob
    fig.suptitle("Comparativo ensaio a ensaio: white-box do Fabrício × white-box novo × MLP pura × híbrido serial",
                 fontweight="bold", fontsize=14.5, y=0.995)
    fig.supxlabel("Tempo de reação, t (min)", fontweight="bold", fontsize=12, y=0.02)
    fig.supylabel("Conversão de zinco, X_Zn (−)", fontweight="bold", fontsize=12, x=0.01)
    fig.text(0.5, 0.0, "Em cada quadro: RMSE de X_Zn nos pontos experimentais (t > 0); ★ = menor erro do ensaio. "
             "Faixa roxa = variação entre os 10 membros do comitê do híbrido (não é intervalo de confiança). "
             "A MLP pura só tem dados a partir de 0,5 min.", ha="center", fontsize=9, style="italic")
    fig.tight_layout(rect=(0.015, 0.03, 1, 0.95))
    fig.savefig(OUT / "fig_13a_comparativo_4_modelos_4x4.png", dpi=300)
    fig.savefig(OUT / "fig_13a_comparativo_4_modelos_4x4.pdf")
    plt.close(fig)

    # ---------------- Figura 13b: resumo ----------------
    fig, (a, b) = plt.subplots(1, 2, figsize=(17, 6.2), gridspec_kw={"width_ratios": [1, 1.7]})
    w = 0.2; xs = np.arange(3)
    for i, (k, nome, cor) in enumerate(MODELOS):
        vals = tab_glob[f"RMSE_{k}"].values * 100
        bars = a.bar(xs + (i - 1.5) * w, vals, w, color=cor, label=nome)
        for r_, v in zip(bars, vals):
            a.text(r_.get_x() + r_.get_width() / 2, v + 0.15, f"{v:.1f}", ha="center", fontsize=8.2)
    a.set_xticks(xs); a.set_xticklabels(["Treino\n(91 pts)", "Teste cego\n(21 pts)", "Global\n(112 pts)"])
    a.set_ylabel("RMSE de X_Zn (pontos percentuais)"); a.set_title("(a) RMSE por partição", fontweight="bold")
    a.set_ylim(0, 17.5)
    a.legend(frameon=False, fontsize=8.8, loc="upper right")

    mat = por_ens[[f"RMSE_{k}" for k, _, _ in MODELOS]].values.T * 100
    im = b.imshow(mat, aspect="auto", cmap="YlOrRd", vmin=0, vmax=15)
    b.set_xticks(range(16))
    b.set_xticklabels([f"{int(e)}{'*' if e in ENSAIOS_TESTE else ''}\nη={h:g}" for e, h in zip(por_ens["ensaio"], por_ens["eta"])], fontsize=8)
    b.set_yticks(range(4)); b.set_yticklabels(["Fabrício", "WB novo", "MLP pura", "Híbrido"])
    for i in range(4):
        for j in range(16):
            b.text(j, i, f"{mat[i, j]:.1f}", ha="center", va="center", fontsize=8,
                   color="white" if mat[i, j] > 9 else "black", fontweight="bold" if mat[i, j] == mat[:, j].min() else "normal")
    b.set_title("(b) RMSE por ensaio (pontos percentuais; negrito = menor do ensaio; * = teste cego)", fontweight="bold")
    b.grid(False)
    fig.colorbar(im, ax=b, fraction=0.025, pad=0.01, label="RMSE (p.p.)")
    fig.suptitle("Resumo do comparativo de quatro modelos (16 ensaios, 112 pontos em t > 0)", fontweight="bold", fontsize=13.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig_13b_comparativo_4_modelos_resumo.png", dpi=300)
    fig.savefig(OUT / "fig_13b_comparativo_4_modelos_resumo.pdf")
    plt.close(fig)
    print("OK")


if __name__ == "__main__":
    main()
