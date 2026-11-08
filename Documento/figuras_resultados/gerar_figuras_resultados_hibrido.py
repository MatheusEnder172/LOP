"""Figuras da seção de Resultados do modelo híbrido serial (relatório final LOP).

Gera, em 300 DPI (.png) e vetorial (.pdf):
- fig_res_01_reconstrucao_problema_inverso: X_Zn reconstruído pelo problema inverso x experimental (16 ensaios)
- fig_res_02_taxas_alvo: taxas de retração estimadas no problema inverso (escala log)

As demais figuras dos Resultados vêm das saídas da Subetapa 3.2.6 (Código/outputs/etapa_3_2/...).

Uso: python gerar_figuras_resultados_hibrido.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG_DIR = Path(__file__).resolve().parent
BASE_DIR = FIG_DIR.parents[1] / "Base de dados"
SPLITS = BASE_DIR / "processed" / "splits"
RAW = BASE_DIR / "raw"

CORES = {0.1: "#1F3A5F", 0.5: "#2E6DA4", 1.0: "#2A9D8F", 1.5: "#D9822B"}
MARCAS = {0.1: "o", 0.5: "s", 1.0: "^", 1.5: "D"}

plt.rcParams.update({
    "font.family": "Arial", "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 11.5,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 9, "mathtext.fontset": "dejavusans",
    "savefig.dpi": 300,
})


def save(fig: plt.Figure, name: str) -> None:
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _dados():
    dense = pd.concat([pd.read_csv(SPLITS / "train_dense.csv"), pd.read_csv(SPLITS / "test_dense.csv")])
    exp = pd.read_csv(RAW / "cinetica_batelada_A1_4.csv")
    return dense.sort_values(["ensaio", "t_min"]), exp[exp["t_min"] > 0]


def _fmt(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


def fig_reconstrucao() -> None:
    dense, exp = _dados()
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.6), sharex=True, sharey=True)
    for ax, (eta, letra) in zip(axes.ravel(), [(0.5, "a"), (1.0, "b"), (1.5, "c"), (3.1, "d")]):
        for ca0, cor in CORES.items():
            d = dense[np.isclose(dense["razao_molar_eta"], eta) & np.isclose(dense["CA0_mol_L"], ca0)]
            if d.empty:
                continue
            e = int(d["ensaio"].iloc[0])
            t = np.concatenate([[0.0], d["t_min"].values])
            x = np.concatenate([[0.0], d["XZn_reconstruido"].values])
            teste = e in (7, 8, 14)
            ax.plot(t, x, color=cor, lw=1.8, ls="--" if teste else "-")
            p = exp[exp["ensaio"] == e]
            ax.scatter(p["t_min"], p["XZn"], marker=MARCAS[ca0], s=34, color=cor, edgecolor="white", lw=0.6,
                       zorder=3, label=f"Ensaio {e}: $C_{{A0}}$ = {_fmt(ca0)} mol/L" + (" (teste)" if teste else ""))
        ax.set_title(f"({letra}) $\\eta$ = {str(eta).replace('.', ',')}", loc="left")
        ax.grid(ls="--", alpha=0.5)
        ax.set_ylim(0, 1.05)
        ax.legend(loc="lower right", fontsize=8.5)
    for ax in axes[1]:
        ax.set_xlabel("Tempo (min)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Conversão de zinco, $X_{Zn}$ (–)")
    fig.tight_layout()
    save(fig, "fig_res_01_reconstrucao_problema_inverso")


def fig_taxas() -> None:
    dense, _ = _dados()
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.2), sharex=True, sharey=True)
    for ax, (eta, letra) in zip(axes.ravel(), [(0.5, "a"), (1.0, "b"), (1.5, "c"), (3.1, "d")]):
        for ca0, cor in CORES.items():
            d = dense[np.isclose(dense["razao_molar_eta"], eta) & np.isclose(dense["CA0_mol_L"], ca0)]
            if d.empty:
                continue
            e = int(d["ensaio"].iloc[0])
            ax.plot(d["t_min"], np.maximum(d["abs_v_alvo_um_min"], 1e-3), color=cor, lw=1.8,
                    ls="--" if e in (7, 8, 14) else "-", label=f"Ensaio {e}: $C_{{A0}}$ = {_fmt(ca0)} mol/L")
        ax.axhline(0.03, color="#6B7280", lw=1.0, ls=":")
        ax.set_yscale("log")
        ax.set_ylim(8e-4, 200)
        ax.set_title(f"({letra}) $\\eta$ = {str(eta).replace('.', ',')}", loc="left")
        ax.grid(ls="--", alpha=0.5, which="both")
        ax.legend(loc="upper right", fontsize=8.5)
    axes[0, 0].text(14.8, 0.036, "limite de $c$", ha="right", fontsize=8.5, color="#6B7280")
    for ax in axes[1]:
        ax.set_xlabel("Tempo (min)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Taxa de retração, $\\nu$ (µm/min)")
    fig.tight_layout()
    save(fig, "fig_res_02_taxas_alvo")


if __name__ == "__main__":
    fig_reconstrucao()
    fig_taxas()
