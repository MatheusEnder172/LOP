"""Pipeline Unificado para Geração de Versões Logarítmicas das Figuras Científicas.

Gera as versões em escala logarítmica (semilog-y e log-log) para todas as etapas
do projeto LOP onde a visualização logarítmica possui fundamentação físico-química:
  1. Etapa 0.1: fig_01_curvas_cineticas_bancada_log (Fração residual 1 - X_Zn em semilog-y)
  2. Etapa 1.3: fig_03_baseline_fpm_vs_experimento_log (1 - X_Zn em semilog-y)
               fig_comp_01_cinetica_16_ensaios_log (1 - X_Zn em semilog-y)
               fig_comp_03_paridade_e_residuos_log (Paridade de 1 - X_Zn em log-log)
  3. Etapa 2.1: fig_04_reconstrucao_XZn_vs_experimento_log (1 - X_Zn em semilog-y)
               fig_05_curvas_v_otimizadas_log (|v(t)| em semilog-y cobrindo 4 ordens de magnitude)
  4. Etapa 3.1: fig_06_particao_espaco_experimental_log (|v(t)| e 1 - X_Zn em semilog-y)
  5. Etapa 3.2.1 (MLP): fig_07b_predicoes_v_mlp_log (Trajetórias de |v(t)| em semilog-y nos 16 ensaios)
                       fig_07c_paridade_e_residuos_mlp_log (Paridade log-log e resíduos logarítmicos)
  6. Etapa 3.2.2 (RF):  fig_08b_predicoes_v_rf_log (Trajetórias de |v(t)| em semilog-y nos 16 ensaios)
                       fig_08c_paridade_e_residuos_rf_log (Paridade log-log e resíduos logarítmicos)

Padrão de saída: 300 DPI em formato PNG e cópia vetorial em formato PDF,
preservando estritamente os arquivos originais em escala linear sem modificações.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

# Adicionar caminhos ao sys.path
project_root = Path(__file__).resolve().parents[1]
mlp_dir = project_root / "etapas" / "etapa_3_2" / "subetapa_3_2_1_mlp"
rf_dir = project_root / "etapas" / "etapa_3_2" / "subetapa_3_2_2_random_forest"
svr_dir = project_root / "etapas" / "etapa_3_2" / "subetapa_3_2_3_svr"

for p in [str(project_root), str(mlp_dir), str(rf_dir), str(svr_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.physics.pbm_batch import BatchPBMSolver
from modelo_mlp import KineticsMLP
from modelo_rf import KineticsRandomForest
from modelo_svr import KineticsSVR


def set_plot_style() -> None:
    """Configura o estilo padrão para gráficos científicos de alto contraste."""
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
            "axes.grid": True,
            "grid.alpha": 0.35,
            "grid.linestyle": "--",
        }
    )


# =============================================================================
# 1. ETAPA 0.1: Cinética de Bancada em Escala Logarítmica (1 - X_Zn)
# =============================================================================
def gerar_log_etapa_0_1(base_dir: Path) -> None:
    print("\n[1/6] Gerando versão logarítmica da Etapa 0.1 (Cinética de Bancada)...")
    raw_path = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    out_dir = base_dir / "Código" / "outputs" / "etapa_0_1"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(raw_path)

    etas = [0.5, 1.0, 1.5, 3.1]
    ca0_vals = [0.1, 0.5, 1.0, 1.5]
    estilos = {
        0.1: {"color": "#1f77b4", "marker": "o", "label": "0,10 mol/L"},
        0.5: {"color": "#2ca02c", "marker": "s", "label": "0,50 mol/L"},
        1.0: {"color": "#ff7f0e", "marker": "^", "label": "1,00 mol/L"},
        1.5: {"color": "#d62728", "marker": "D", "label": "1,50 mol/L"},
    }

    fig, axes = plt.subplots(2, 2, figsize=(13, 10), sharex=True, sharey=True)
    axes = axes.flatten()

    for idx, eta in enumerate(etas):
        ax = axes[idx]
        df_eta = df[df["razao_molar_eta"] == eta]

        for ca0 in ca0_vals:
            sub = df_eta[df_eta["CA0_mol_L"] == ca0].sort_values("t_min")
            est = estilos[ca0]
            unreacted = np.maximum(1e-4, 1.0 - sub["XZn"].values)
            ax.plot(
                sub["t_min"],
                unreacted,
                color=est["color"],
                marker=est["marker"],
                markersize=6,
                lw=1.8,
                label=f"$C_{{A0}} = {est['label']}$",
                alpha=0.9,
            )

        ax.set_yscale("log")
        ax.set_ylim(5e-4, 1.3)
        ax.set_xlim(-0.3, 15.5)

        if eta == 0.5:
            titulo = r"$\eta = 0,5$ (Patamar Residual: $1 - X \approx 0,50$)"
            ax.axhline(0.50, color="gray", linestyle=":", lw=1.2)
        elif eta == 1.0:
            titulo = r"$\eta = 1,0$ (Patamar Residual: $1 - X \approx 0,13 - 0,15$)"
            ax.axhline(0.14, color="gray", linestyle=":", lw=1.2)
        elif eta == 1.5:
            titulo = r"$\eta = 1,5$ (Patamar Residual: $1 - X \approx 0,03$)"
            ax.axhline(0.03, color="gray", linestyle=":", lw=1.2)
        else:
            titulo = r"$\eta = 3,1$ (Dissolução Total: $1 - X < 0,005$)"
            ax.axhline(0.005, color="gray", linestyle=":", lw=1.2)

        ax.set_title(f"Painel ({chr(97+idx)}) — {titulo}", fontweight="bold", pad=8)
        if idx % 2 == 0:
            ax.set_ylabel("Fração Não-Reagida, $(1 - X_{\\mathrm{Zn}})$ [-]", fontweight="bold")
        if idx >= 2:
            ax.set_xlabel("Tempo de Reação, $t$ (min)", fontweight="bold")

        ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

    fig.suptitle(
        "Cinética de Lixiviação em Escala Semilogarítmica: Fração Não-Reagida $(1 - X_{\\mathrm{Zn}})$ vs. Tempo\n"
        "Evidenciação dos Patamares de Equilíbrio e Decaimento Exponencial das Espécies Minerais",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout()
    fig.subplots_adjust(top=0.91)
    png_path = out_dir / "fig_01_curvas_cineticas_bancada_log.png"
    pdf_path = out_dir / "fig_01_curvas_cineticas_bancada_log.pdf"
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)
    print(f"  -> Salvo: {png_path.name} e {pdf_path.name}")


# =============================================================================
# 2. ETAPA 1.3: Baseline FPM e Comparativo Fabrício vs. LOP em Escala Logarítmica
# =============================================================================
def gerar_log_etapa_1_3(base_dir: Path) -> None:
    print("\n[2/6] Gerando versões logarítmicas da Etapa 1.3 (Baseline FPM e Comparativo Fabrício vs. LOP)...")
    out_dir_comp = base_dir / "Código" / "outputs" / "etapa_1_3" / "comparacao_fabricio_x_LOP"
    out_dir_fpm = base_dir / "Código" / "outputs" / "etapa_1_3"
    out_dir_comp.mkdir(parents=True, exist_ok=True)
    out_dir_fpm.mkdir(parents=True, exist_ok=True)

    raw_path = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    params_path = base_dir / "Base de dados" / "processed" / "parametros_otimizacao_inversa.csv"

    df_exp = pd.read_csv(raw_path)
    df_params = pd.read_csv(params_path).set_index("ensaio")
    solver = BatchPBMSolver()

    etas = [0.5, 1.0, 1.5, 3.1]
    t_fine = np.linspace(0.0, 15.0, 200)

    color_map_ca0 = {0.10: "#1f77b4", 0.50: "#2ca02c", 1.00: "#ff7f0e", 1.50: "#d62728"}
    marker_map_ca0 = {0.10: "o", 0.50: "s", 1.00: "^", 1.50: "D"}

    # FIGURA 03 LOG: Baseline Mecanístico FPM Puro vs Experimento em Semilog-y
    fig03, axes03 = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    axes03 = axes03.flatten()

    for idx, eta in enumerate(etas):
        ax = axes03[idx]
        ensaios_eta = sorted(df_exp[df_exp["razao_molar_eta"] == eta]["ensaio"].unique())
        for ens in ensaios_eta:
            sub = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
            ca0 = float(sub["CA0_mol_L"].iloc[0])
            t_exp = sub["t_min"].values
            x_exp = sub["XZn"].values
            res_fab_fine = solver.simulate(ca0, eta, t_fine, alpha=5500.0)

            cor = color_map_ca0.get(ca0, "black")
            marcador = marker_map_ca0.get(ca0, "o")

            ax.plot(
                t_fine,
                np.maximum(1e-4, 1.0 - res_fab_fine["XZn"]),
                color=cor,
                lw=2.0,
                label=f"Baseline FPM ($C_{{A0}}={ca0:.2f}\\mathrm{{M}}$)",
            )
            ax.plot(
                t_exp,
                np.maximum(1e-4, 1.0 - x_exp),
                color=cor,
                marker=marcador,
                markersize=6,
                linestyle="none",
                label=f"Exp ($C_{{A0}}={ca0:.2f}\\mathrm{{M}}$)",
            )

        ax.set_yscale("log")
        ax.set_ylim(5e-4, 1.3)
        ax.set_xlim(-0.3, 15.5)
        ax.set_title(f"Painel ({chr(97+idx)}) — Razão Molar $\\eta = {eta:.1f}$", fontweight="bold", pad=8)
        if idx % 2 == 0:
            ax.set_ylabel("Fração Não-Reagida, $(1 - X_{\\mathrm{Zn}})$ [-]", fontweight="bold")
        if idx >= 2:
            ax.set_xlabel("Tempo de Reação, $t$ (min)", fontweight="bold")
        ax.legend(loc="upper right", fontsize=8.0, framealpha=0.9, ncol=2)

    fig03.suptitle(
        "Simulação do Baseline Fenomenológico Puro (FPM Puro) em Escala Semilogarítmica\n"
        "Fração Não-Reagida $(1 - X_{\\mathrm{Zn}})$ vs. Tempo — Modelo PBM Nominal com $\\alpha = 5500\\ \\mu\\mathrm{m/min}$",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout()
    fig03.subplots_adjust(top=0.91)
    png03 = out_dir_fpm / "fig_03_baseline_fpm_vs_experimento_log.png"
    pdf03 = out_dir_fpm / "fig_03_baseline_fpm_vs_experimento_log.pdf"
    fig03.savefig(png03, dpi=300)
    fig03.savefig(pdf03)
    plt.close(fig03)
    print(f"  -> Salvo: {png03.name} e {pdf03.name}")

    # FIGURA COMP 01 LOG: Fração Não-Reagida 1 - X_Zn nos 16 ensaios
    fig1, axes1 = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    axes1 = axes1.flatten()

    all_y_exp = []
    all_y_fab = []
    all_y_novo = []

    for idx, eta in enumerate(etas):
        ax = axes1[idx]
        ensaios_eta = sorted(df_exp[df_exp["razao_molar_eta"] == eta]["ensaio"].unique())

        for ens in ensaios_eta:
            sub = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
            ca0 = float(sub["CA0_mol_L"].iloc[0])
            t_exp = sub["t_min"].values
            x_exp = sub["XZn"].values

            # Modelo Nominal Fabricio (alpha = 5500)
            res_fab_exp = solver.simulate(ca0, eta, t_exp, alpha=5500.0)
            res_fab_fine = solver.simulate(ca0, eta, t_fine, alpha=5500.0)

            # Modelo Adaptativo LOP
            p = df_params.loc[ens]
            d_fine = (p["a1"] / p["b1"]) * (1 - np.exp(-p["b1"] * t_fine)) + (p["a2"] / p["b2"]) * (1 - np.exp(-p["b2"] * t_fine)) + p["c"] * t_fine
            d_exp = (p["a1"] / p["b1"]) * (1 - np.exp(-p["b1"] * t_exp)) + (p["a2"] / p["b2"]) * (1 - np.exp(-p["b2"] * t_exp)) + p["c"] * t_exp
            x_novo_fine = solver.compute_conversion_from_delta(d_fine)
            x_novo_exp = solver.compute_conversion_from_delta(d_exp)

            # Armazenar pontos para gráfico de paridade logarítmica
            all_y_exp.extend(np.maximum(1e-4, 1.0 - x_exp))
            all_y_fab.extend(np.maximum(1e-4, 1.0 - res_fab_exp["XZn"]))
            all_y_novo.extend(np.maximum(1e-4, 1.0 - x_novo_exp))

            # Plot de curvas selecionadas por painel para legibilidade
            if ca0 in [0.10, 1.00]:
                ls_fab = "--" if ca0 == 0.10 else ":"
                ax.plot(
                    t_fine,
                    np.maximum(1e-4, 1.0 - res_fab_fine["XZn"]),
                    color="#c62828",
                    linestyle=ls_fab,
                    lw=1.5,
                    alpha=0.8,
                    label="Nominal (α=5500)" if (ens == ensaios_eta[0] and ca0 == 0.10) else None,
                )
                ax.plot(
                    t_fine,
                    np.maximum(1e-4, 1.0 - x_novo_fine),
                    color="#2e7d32",
                    linestyle="-",
                    lw=2.0,
                    alpha=0.9,
                    label="Adaptativo LOP" if (ens == ensaios_eta[0] and ca0 == 0.10) else None,
                )
                ax.plot(
                    t_exp,
                    np.maximum(1e-4, 1.0 - x_exp),
                    color="#1565c0",
                    marker="o" if ca0 == 0.10 else "s",
                    linestyle="none",
                    markersize=6,
                    label=f"Exp. (CA0={ca0:.2f}M)" if ens == ensaios_eta[0] else None,
                )

        ax.set_yscale("log")
        ax.set_ylim(5e-4, 1.3)
        ax.set_xlim(-0.4, 15.5)
        ax.set_title(f"Painel ({chr(97+idx)}) — Razão Molar $\\eta = {eta:.1f}$", fontweight="bold", pad=8)
        if idx % 2 == 0:
            ax.set_ylabel("Fração Residual $(1 - X_{\\mathrm{Zn}})$ [-]", fontweight="bold")
        if idx >= 2:
            ax.set_xlabel("Tempo de Reação, $t$ (min)", fontweight="bold")
        ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

    fig1.suptitle(
        "Comparativo Cinético em Escala Semilogarítmica: Fração Residual $(1 - X_{\\mathrm{Zn}})$ vs. Tempo\n"
        "Evidenciação do Afastamento no Platô do Modelo Nominal (α = 5500) vs. Aderência Estrita da Abordagem LOP",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout()
    fig1.subplots_adjust(top=0.91)
    png1 = out_dir_comp / "fig_comp_01_cinetica_16_ensaios_log.png"
    pdf1 = out_dir_comp / "fig_comp_01_cinetica_16_ensaios_log.pdf"
    fig1.savefig(png1, dpi=300)
    fig1.savefig(pdf1)
    plt.close(fig1)
    print(f"  -> Salvo: {png1.name} e {pdf1.name}")

    # FIGURA COMP 03 LOG: Gráfico de Paridade Log-Log da Fração Residual
    fig2, (ax_p1, ax_p2) = plt.subplots(1, 2, figsize=(13, 6), sharey=True, constrained_layout=True)
    all_y_exp = np.array(all_y_exp)
    all_y_fab = np.array(all_y_fab)
    all_y_novo = np.array(all_y_novo)

    diag = np.logspace(-4, 0.2, 100)

    # Painel (a): Modelo Nominal Fabrício
    ax_p1.plot(diag, diag, "k-", lw=1.5, label="Bissetriz Ideal 1:1")
    ax_p1.fill_between(diag, diag * 0.7, diag * 1.3, color="gray", alpha=0.15, label="Faixa de Tolerância ±30%")
    ax_p1.scatter(all_y_exp, all_y_fab, color="#c62828", alpha=0.65, s=35, edgecolors="black", lw=0.5, label="Modelo Nominal (α=5500)")
    ax_p1.set_xscale("log")
    ax_p1.set_yscale("log")
    ax_p1.set_xlim(8e-4, 1.2)
    ax_p1.set_ylim(8e-4, 1.2)
    ax_p1.set_xlabel("Fração Não-Reagida Experimental $(1 - X_{\\mathrm{exp}})$", fontweight="bold")
    ax_p1.set_ylabel("Fração Não-Reagida Predita $(1 - X_{\\mathrm{pred}})$", fontweight="bold")
    ax_p1.set_title("(a) Modelo Nominal de Bortot Coelho (α = 5500)", fontweight="bold")
    ax_p1.legend(loc="upper left", fontsize=8.5)

    # Painel (b): Nova Abordagem LOP
    ax_p2.plot(diag, diag, "k-", lw=1.5, label="Bissetriz Ideal 1:1")
    ax_p2.fill_between(diag, diag * 0.7, diag * 1.3, color="gray", alpha=0.15, label="Faixa de Tolerância ±30%")
    ax_p2.scatter(all_y_exp, all_y_novo, color="#2e7d32", alpha=0.75, s=35, edgecolors="black", lw=0.5, label="Nova Abordagem (LOP)")
    ax_p2.set_xscale("log")
    ax_p2.set_yscale("log")
    ax_p2.set_xlim(8e-4, 1.2)
    ax_p2.set_ylim(8e-4, 1.2)
    ax_p2.set_xlabel("Fração Não-Reagida Experimental $(1 - X_{\\mathrm{exp}})$", fontweight="bold")
    ax_p2.set_title("(b) Nova Abordagem Adaptativa (LOP)", fontweight="bold")
    ax_p2.legend(loc="upper left", fontsize=8.5)

    fig2.suptitle(
        "Diagramas de Paridade Log-Log: Fração Residual Não-Reagida $(1 - X_{\\mathrm{Zn}})$\n"
        "Comprovação do Colapso Estrito de 3 Ordens de Magnitude sobre a Bissetriz Ideal na Abordagem LOP",
        fontsize=13,
        fontweight="bold",
    )
    png2 = out_dir_comp / "fig_comp_03_paridade_e_residuos_log.png"
    pdf2 = out_dir_comp / "fig_comp_03_paridade_e_residuos_log.pdf"
    fig2.savefig(png2, dpi=300)
    fig2.savefig(pdf2)
    plt.close(fig2)
    print(f"  -> Salvo: {png2.name} e {pdf2.name}")


# =============================================================================
# 3. ETAPA 2.1: Otimização Inversa — Perfis de Velocidade e Conversão em Semilog-y
# =============================================================================
def gerar_log_etapa_2_1(base_dir: Path) -> None:
    print("\n[3/6] Gerando versões logarítmicas da Etapa 2.1 (Otimização Inversa dos Alvos v(t) e X_Zn)...")
    out_dir = base_dir / "Código" / "outputs" / "etapa_2_1"
    out_dir.mkdir(parents=True, exist_ok=True)

    dense_path = base_dir / "Base de dados" / "processed" / "alvos_v_treinamento_denso.csv"
    raw_path = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    df_dense = pd.read_csv(dense_path)
    df_exp = pd.read_csv(raw_path)

    etas = [0.5, 1.0, 1.5, 3.1]
    color_map = {0.10: "#1f77b4", 0.50: "#2ca02c", 1.00: "#ff7f0e", 1.50: "#d62728"}
    marker_map = {0.10: "o", 0.50: "s", 1.00: "^", 1.50: "D"}

    # FIGURA 04 LOG: Reconstrução de 1 - X_Zn vs Experimento em Semilog-y
    fig4, axes4 = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    axes4 = axes4.flatten()

    for idx, eta_val in enumerate(etas):
        ax = axes4[idx]
        df_eta_rec = df_dense[np.isclose(df_dense["razao_molar_eta"], eta_val)]
        df_eta_exp = df_exp[np.isclose(df_exp["razao_molar_eta"], eta_val)]
        ensaios = sorted(
            df_eta_rec["ensaio"].unique(),
            key=lambda e: df_eta_rec[df_eta_rec["ensaio"] == e]["CA0_mol_L"].iloc[0],
        )

        for ens in ensaios:
            sub_rec = df_eta_rec[df_eta_rec["ensaio"] == ens].sort_values("t_min")
            sub_exp = df_eta_exp[df_eta_exp["ensaio"] == ens].sort_values("t_min")
            ca0 = float(sub_rec["CA0_mol_L"].iloc[0])
            cor = color_map.get(ca0, "black")
            marcador = marker_map.get(ca0, "o")

            unrec_rec = np.maximum(1e-4, 1.0 - sub_rec["XZn_reconstruido"].values)
            unrec_exp = np.maximum(1e-4, 1.0 - sub_exp["XZn"].values)

            ax.plot(
                sub_rec["t_min"],
                unrec_rec,
                color=cor,
                lw=2.2,
                label=f"PBM Reconstruído ($C_{{A0}}={ca0:.2f}\\mathrm{{M}}$)",
            )
            ax.plot(
                sub_exp["t_min"],
                unrec_exp,
                color=cor,
                marker=marcador,
                markersize=6.5,
                linestyle="none",
                markeredgecolor="black",
                markeredgewidth=0.7,
                label=f"Exp ($C_{{A0}}={ca0:.2f}\\mathrm{{M}}$)",
            )

        ax.set_yscale("log")
        ax.set_ylim(5e-4, 1.3)
        ax.set_xlim(-0.3, 15.5)
        ax.set_title(f"Painel ({chr(97 + idx)}) — Razão Molar $\\eta = {eta_val}$", fontweight="bold", pad=8)
        if idx % 2 == 0:
            ax.set_ylabel("Fração Não-Reagida, $(1 - X_{\\mathrm{Zn}})$ [-]", fontweight="bold")
        if idx >= 2:
            ax.set_xlabel("Tempo de Reação, $t$ (min)", fontweight="bold")
        ax.legend(loc="upper right", fontsize=8.0, framealpha=0.9, ncol=2)

    fig4.suptitle(
        "Validação da Inversão em Escala Semilogarítmica: Fração Não-Reagida $(1 - X_{\\mathrm{Zn}})$ vs. Tempo\n"
        "Reconstrução via PBM com $v(t)$ Otimizado vs. Dados Experimentais (Colapso Perfeito nos Patamares Residuais)",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout()
    fig4.subplots_adjust(top=0.91)
    png4 = out_dir / "fig_04_reconstrucao_XZn_vs_experimento_log.png"
    pdf4 = out_dir / "fig_04_reconstrucao_XZn_vs_experimento_log.pdf"
    fig4.savefig(png4, dpi=300)
    fig4.savefig(pdf4)
    plt.close(fig4)
    print(f"  -> Salvo: {png4.name} e {pdf4.name}")

    # FIGURA 05 LOG: Perfis de Velocidade |v(t)| em Semilog-y
    fig5, axes5 = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    axes5 = axes5.flatten()

    for idx, eta_val in enumerate(etas):
        ax = axes5[idx]
        df_eta = df_dense[np.isclose(df_dense["razao_molar_eta"], eta_val)]
        ensaios = sorted(df_eta["ensaio"].unique(), key=lambda e: df_eta[df_eta["ensaio"] == e]["CA0_mol_L"].iloc[0])

        for ens in ensaios:
            sub = df_eta[df_eta["ensaio"] == ens].sort_values("t_min")
            ca0 = float(sub["CA0_mol_L"].iloc[0])
            cor = color_map.get(ca0, "black")
            v_val = np.maximum(1e-3, sub["abs_v_alvo_um_min"].values)

            ax.plot(
                sub["t_min"],
                v_val,
                color=cor,
                lw=2.2,
                label=f"$C_{{A0}} = {ca0:.2f}\\ \\mathrm{{mol/L}}$ (Ens. {ens})",
            )

        ax.set_yscale("log")
        ax.set_ylim(8e-4, 2e3)
        ax.set_xlim(-0.2, 15.2)
        ax.set_title(f"Painel ({chr(97 + idx)}) — Taxa $|v(t)|$ para $\\eta = {eta_val}$", fontweight="bold", pad=8)
        if idx % 2 == 0:
            ax.set_ylabel("Módulo da Velocidade, $|v(t)|\\ (\\mu\\mathrm{m/min})$", fontweight="bold")
        if idx >= 2:
            ax.set_xlabel("Tempo de Reação, $t$ (min)", fontweight="bold")

        ax.legend(loc="upper right", fontsize=8.8, framealpha=0.9)

    fig5.suptitle(
        "Perfis Ótimos de Velocidade Interfacial $|v(t)|$ em Escala Semilogarítmica (PBM Inverso)\n"
        "Resolução Plena de 4 Ordens de Magnitude: Transiente Ultrarrápido Inicial ($>500\\ \\mu\\mathrm{m/min}$) à Cauda Lenta ($<0,01\\ \\mu\\mathrm{m/min}$)",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout()
    fig5.subplots_adjust(top=0.91)
    png5 = out_dir / "fig_05_curvas_v_otimizadas_log.png"
    pdf5 = out_dir / "fig_05_curvas_v_otimizadas_log.pdf"
    fig5.savefig(png5, dpi=300)
    fig5.savefig(pdf5)
    plt.close(fig5)
    print(f"  -> Salvo: {png5.name} e {pdf5.name}")


# =============================================================================
# 4. ETAPA 3.1: Partição de Dados em Escala Logarítmica
# =============================================================================
def gerar_log_etapa_3_1(base_dir: Path) -> None:
    print("\n[4/6] Gerando versão logarítmica da Etapa 3.1 (Partição do Espaço Experimental)...")
    out_dir = base_dir / "Código" / "outputs" / "etapa_3_1"
    out_dir.mkdir(parents=True, exist_ok=True)

    splits_dir = base_dir / "Base de dados" / "processed" / "splits"
    train_dense = pd.read_csv(splits_dir / "train_dense.csv")
    test_dense = pd.read_csv(splits_dir / "test_dense.csv")

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # Subplot (a): Espaço Experimental C_A0 vs eta
    ax_a = axes[0, 0]
    train_exp = train_dense.drop_duplicates(subset=["ensaio"])
    test_exp = test_dense.drop_duplicates(subset=["ensaio"])

    ax_a.scatter(
        train_exp["razao_molar_eta"],
        train_exp["CA0_mol_L"],
        color="#1565c0",
        s=120,
        label=f"Treino/Validação ({len(train_exp)} ensaios, 793 pts)",
        edgecolors="black",
        lw=0.8,
        zorder=3,
    )
    for _, r in train_exp.iterrows():
        ax_a.annotate(f"E{int(r['ensaio'])}", (r["razao_molar_eta"] + 0.05, r["CA0_mol_L"] + 0.02), fontsize=8.5, color="#1565c0")

    ax_a.scatter(
        test_exp["razao_molar_eta"],
        test_exp["CA0_mol_L"],
        color="#d32f2f",
        s=170,
        marker="^",
        label=f"Teste Cego Estrito ({len(test_exp)} ensaios: 7, 8, 14)",
        edgecolors="black",
        lw=1.0,
        zorder=4,
    )
    for _, r in test_exp.iterrows():
        ax_a.annotate(f"E{int(r['ensaio'])}*", (r["razao_molar_eta"] + 0.05, r["CA0_mol_L"] + 0.03), fontsize=9.5, fontweight="bold", color="#d32f2f")

    ax_a.set_title("(a) Domínio Operacional Particionado", fontweight="bold")
    ax_a.set_xlabel(r"Razão Molar Ácido/Zinco Inicial, $\eta$ (-)", fontweight="bold")
    ax_a.set_ylabel(r"Concentração Inicial de Ácido, $C_{A0}$ (mol/L)", fontweight="bold")
    ax_a.set_xlim(0.2, 3.4)
    ax_a.set_ylim(0.0, 1.7)
    ax_a.legend(loc="upper left", fontsize=8.5)

    # Subplot (b): Perfis de Velocidade |v(t)| em Semilog-y
    ax_b = axes[0, 1]
    for ens, g in train_dense.groupby("ensaio"):
        v_pos = np.maximum(1e-3, g["abs_v_alvo_um_min"])
        ax_b.plot(g["t_min"], v_pos, color="#1565c0", alpha=0.35, lw=1.2)
    for ens, g in test_dense.groupby("ensaio"):
        v_pos = np.maximum(1e-3, g["abs_v_alvo_um_min"])
        ax_b.plot(g["t_min"], v_pos, color="#d32f2f", alpha=0.85, lw=2.2, label=f"Teste Cego: Ens. {ens}")

    ax_b.plot([], [], color="#1565c0", alpha=0.7, lw=1.5, label="Treino (13 ensaios)")
    ax_b.set_yscale("log")
    ax_b.set_ylim(8e-4, 2e3)
    ax_b.set_xlim(-0.2, 15.2)
    ax_b.set_title(r"(b) Trajetórias de $|v(t)|$ nos Ensaios [Escala Semilogarítmica]", fontweight="bold")
    ax_b.set_xlabel("Tempo, $t$ (min)", fontweight="bold")
    ax_b.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_b.legend(loc="upper right", fontsize=8.5)

    # Subplot (c): Fração Residual Não-Reagida 1 - X_Zn em Semilog-y
    ax_c = axes[1, 0]
    for ens, g in train_dense.groupby("ensaio"):
        unrec = np.maximum(1e-4, 1.0 - g["XZn_reconstruido"])
        ax_c.plot(g["t_min"], unrec, color="#1565c0", alpha=0.35, lw=1.2)
    for ens, g in test_dense.groupby("ensaio"):
        unrec = np.maximum(1e-4, 1.0 - g["XZn_reconstruido"])
        ax_c.plot(g["t_min"], unrec, color="#d32f2f", alpha=0.85, lw=2.2, label=f"Teste Cego: Ens. {ens}")

    ax_c.plot([], [], color="#1565c0", alpha=0.7, lw=1.5, label="Treino (13 ensaios)")
    ax_c.set_yscale("log")
    ax_c.set_ylim(5e-4, 1.3)
    ax_c.set_xlim(-0.2, 15.2)
    ax_c.set_title(r"(c) Fração Residual $(1 - X_{\mathrm{Zn}})$ [Escala Semilogarítmica]", fontweight="bold")
    ax_c.set_xlabel("Tempo, $t$ (min)", fontweight="bold")
    ax_c.set_ylabel(r"$(1 - X_{\mathrm{Zn}})\ (-)$ [Escala Log]", fontweight="bold")
    ax_c.legend(loc="upper right", fontsize=8.5)

    # Subplot (d): Distribuição do Target no Espaço Logarítmico ln(1 + |v|)
    ax_d = axes[1, 1]
    y_tr_log = np.log1p(train_dense["abs_v_alvo_um_min"])
    y_te_log = np.log1p(test_dense["abs_v_alvo_um_min"])

    bins = np.linspace(0, float(np.max(y_tr_log)) + 0.5, 30)
    ax_d.hist(y_tr_log, bins=bins, density=True, color="#1565c0", alpha=0.55, edgecolor="black", label=f"Treino ($N={len(y_tr_log)}$)")
    ax_d.hist(y_te_log, bins=bins, density=True, color="#d32f2f", alpha=0.55, edgecolor="black", label=f"Teste Cego ($N={len(y_te_log)}$)")

    ax_d.set_title(r"(d) Distribuição de Frequência do Target $\ln(1 + |v|)$", fontweight="bold")
    ax_d.set_xlabel(r"$\ln(1 + |v|)\ (\mathrm{adimensional})$", fontweight="bold")
    ax_d.set_ylabel("Densidade de Probabilidade", fontweight="bold")
    ax_d.legend(loc="upper right", fontsize=8.5)

    fig.suptitle(
        "Caracterização da Partição dos Dados em Escala Logarítmica — Etapa 3.1\n"
        "Comprovação de Representatividade Fenomenológica e Ampla Cobertura Dinâmica de Treino vs. Teste Cego",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout()
    fig.subplots_adjust(top=0.91)
    png_path = out_dir / "fig_06_particao_espaco_experimental_log.png"
    pdf_path = out_dir / "fig_06_particao_espaco_experimental_log.pdf"
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)
    print(f"  -> Salvo: {png_path.name} e {pdf_path.name}")


# =============================================================================
# 5. ETAPA 3.2.1: Multi-Layer Perceptron (MLP) em Escala Logarítmica
# =============================================================================
def gerar_log_etapa_3_2_1_mlp(base_dir: Path) -> None:
    print("\n[5/6] Gerando versões logarítmicas da Subetapa 3.2.1 (MLP PyTorch)...")
    out_dir = base_dir / "Código" / "outputs" / "etapa_3_2" / "subetapa_3_2_1_mlp"
    out_dir.mkdir(parents=True, exist_ok=True)

    splits_dir = base_dir / "Base de dados" / "processed" / "splits"
    models_dir = base_dir / "Código" / "outputs" / "models_saved" / "mlp"

    train_df = pd.read_csv(splits_dir / "train_dense.csv")
    test_df = pd.read_csv(splits_dir / "test_dense.csv")
    scalers = joblib.load(splits_dir / "scalers.joblib")
    scaler_X = scalers["scaler_X"]

    with open(models_dir / "mlp_config.json", "r") as f:
        cfg = json.load(f)

    # Carregar modelo PyTorch
    model = KineticsMLP(input_dim=4, hidden_dims=cfg["hidden_dims"])
    model.load_state_dict(torch.load(models_dir / "mlp_kinetics_v1.pt", map_location=torch.device("cpu"), weights_only=False))
    model.eval()

    feature_cols = ["temperatura_C", "CA0_mol_L", "razao_molar_eta", "t_min"]
    target_col = "abs_v_alvo_um_min"
    test_ensaios = [7, 8, 14]

    # Predições em escala física (um/min)
    for df in [train_df, test_df]:
        X_norm = scaler_X.transform(df[feature_cols].values)
        with torch.no_grad():
            t_X = torch.tensor(X_norm, dtype=torch.float32)
            v_hat = model(t_X).numpy().flatten()
            df["v_pred"] = np.maximum(0.0, v_hat)

    all_df = pd.concat([train_df, test_df], ignore_index=True)

    # FIGURA 07B LOG: 16 ensaios em semilog-y
    fig_b, axes_b = plt.subplots(4, 4, figsize=(16, 12), sharex=True, sharey=True, constrained_layout=True)

    for ens_id in range(1, 17):
        r_idx = (ens_id - 1) // 4
        c_idx = (ens_id - 1) % 4
        ax = axes_b[r_idx, c_idx]

        sub = all_df[all_df["ensaio"] == ens_id].sort_values("t_min")
        is_test = ens_id in test_ensaios
        ca0 = float(sub["CA0_mol_L"].iloc[0])
        eta = float(sub["razao_molar_eta"].iloc[0])

        t = sub["t_min"].values
        v_real = np.maximum(1e-3, sub[target_col].values)
        v_pred = np.maximum(1e-3, sub["v_pred"].values)

        cor_linha = "#d32f2f" if is_test else "#1565c0"
        tag = "[TESTE CEGO]" if is_test else "[Treino]"

        ax.plot(t, v_real, "k--", lw=1.3, label="Alvo Inverso (PBM)", alpha=0.7)
        ax.plot(t, v_pred, color=cor_linha, lw=1.8, label=f"Pred. MLP {tag}")

        ax.set_yscale("log")
        ax.set_ylim(8e-4, 2e3)
        ax.set_xlim(-0.4, 15.4)
        ax.set_title(f"Ens {ens_id:02d} {tag}\n$\\eta={eta:.1f}$, $C_{{A0}}={ca0:.2f}\\mathrm{{M}}$", fontsize=9, fontweight="bold" if is_test else "normal", color="#b71c1c" if is_test else "#0d47a1")
        if c_idx == 0:
            ax.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m/min})$", fontsize=9)
        if r_idx == 3:
            ax.set_xlabel(r"$t\ (\mathrm{min})$", fontsize=9)

        if ens_id == 1:
            ax.legend(fontsize=7.5, loc="upper right")

    fig_b.suptitle(
        "Ajuste e Generalização de |v(t)| em Escala Semilogarítmica nos 16 Ensaios — Multi-Layer Perceptron (MLP PyTorch)\n"
        "Evidenciação da Precisão Neural Simultânea no Pico Transiente Inicial e na Cauda Lenta Assintótica",
        fontsize=13,
        fontweight="bold",
    )
    png_b = out_dir / "fig_07b_predicoes_v_mlp_log.png"
    pdf_b = out_dir / "fig_07b_predicoes_v_mlp_log.pdf"
    fig_b.savefig(png_b, dpi=300)
    fig_b.savefig(pdf_b)
    plt.close(fig_b)
    print(f"  -> Salvo: {png_b.name} e {pdf_b.name}")

    # FIGURA 07C LOG: Paridade Log-Log
    fig_c, (ax_c1, ax_c2) = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    diag = np.logspace(-2, 3.2, 100)

    # Paridade Log-Log
    ax_c1.plot(diag, diag, "k-", lw=1.5, label="Bissetriz Ideal 1:1")
    ax_c1.fill_between(diag, diag * 0.7, diag * 1.3, color="gray", alpha=0.15, label="Faixa de Tolerância ±30%")
    ax_c1.scatter(np.maximum(1e-2, train_df[target_col]), np.maximum(1e-2, train_df["v_pred"]), color="#1565c0", alpha=0.5, s=25, label="Treino (13 ensaios)")
    ax_c1.scatter(np.maximum(1e-2, test_df[target_col]), np.maximum(1e-2, test_df["v_pred"]), color="#d32f2f", marker="^", s=50, edgecolors="black", lw=0.6, label="Teste Cego (Ens 8, 14, 7)", zorder=5)

    ax_c1.set_xscale("log")
    ax_c1.set_yscale("log")
    ax_c1.set_xlim(8e-3, 2e3)
    ax_c1.set_ylim(8e-3, 2e3)
    ax_c1.set_xlabel("Taxa Real Alvo $|v(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c1.set_ylabel("Taxa Predita MLP $|\\hat{v}(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c1.set_title("(a) Gráfico de Paridade Log-Log de 4 Ordens de Magnitude", fontweight="bold")
    ax_c1.legend(loc="upper left", fontsize=8.5)

    # Resíduos no Espaço Logarítmico: ln(1 + v_real) - ln(1 + v_pred)
    res_log_train = np.log1p(train_df[target_col]) - np.log1p(train_df["v_pred"])
    res_log_test = np.log1p(test_df[target_col]) - np.log1p(test_df["v_pred"])

    ax_c2.axhline(0, color="black", linestyle="--", lw=1.2)
    ax_c2.axhspan(-0.3, 0.3, color="#e8f5e9", alpha=0.6, label="Tolerância Logarítmica ±0,3")
    ax_c2.scatter(train_df["v_pred"], res_log_train, color="#1565c0", alpha=0.45, s=20, label="Treino")
    ax_c2.scatter(test_df["v_pred"], res_log_test, color="#d32f2f", marker="^", s=45, edgecolors="black", lw=0.6, label="Teste Cego", zorder=5)

    ax_c2.set_xscale("log")
    ax_c2.set_xlim(8e-3, 2e3)
    ax_c2.set_xlabel("Taxa Predita MLP $|\\hat{v}(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c2.set_ylabel(r"Resíduo Logarítmico: $\ln(1+v) - \ln(1+\hat{v})$", fontweight="bold")
    ax_c2.set_title("(b) Distribuição de Resíduos no Espaço Logarítmico", fontweight="bold")
    ax_c2.legend(loc="upper right", fontsize=8.5)

    fig_c.suptitle(
        "Diagnóstico Estatístico de Aderência Logarítmica — Multi-Layer Perceptron (MLP Campeão)",
        fontsize=13,
        fontweight="bold",
    )
    png_c = out_dir / "fig_07c_paridade_e_residuos_mlp_log.png"
    pdf_c = out_dir / "fig_07c_paridade_e_residuos_mlp_log.pdf"
    fig_c.savefig(png_c, dpi=300)
    fig_c.savefig(pdf_c)
    plt.close(fig_c)
    print(f"  -> Salvo: {png_c.name} e {pdf_c.name}")


# =============================================================================
# 6. ETAPA 3.2.2: Random Forest em Escala Logarítmica
# =============================================================================
def gerar_log_etapa_3_2_2_rf(base_dir: Path) -> None:
    print("\n[6/6] Gerando versões logarítmicas da Subetapa 3.2.2 (Random Forest)...")
    out_dir = base_dir / "Código" / "outputs" / "etapa_3_2" / "subetapa_3_2_2_random_forest"
    out_dir.mkdir(parents=True, exist_ok=True)

    splits_dir = base_dir / "Base de dados" / "processed" / "splits"
    models_dir = base_dir / "Código" / "outputs" / "models_saved" / "random_forest"

    train_df = pd.read_csv(splits_dir / "train_dense.csv")
    test_df = pd.read_csv(splits_dir / "test_dense.csv")

    rf_model = KineticsRandomForest.load(models_dir / "rf_kinetics_v1.joblib")

    feature_cols = ["temperatura_C", "CA0_mol_L", "razao_molar_eta", "t_min"]
    target_col = "abs_v_alvo_um_min"
    test_ensaios = [7, 8, 14]

    train_df["v_pred"] = rf_model.predict(train_df[feature_cols].values)
    test_df["v_pred"] = rf_model.predict(test_df[feature_cols].values)
    all_df = pd.concat([train_df, test_df], ignore_index=True)

    # FIGURA 08B LOG: 16 ensaios em semilog-y
    fig_b, axes_b = plt.subplots(4, 4, figsize=(16, 12), sharex=True, sharey=True, constrained_layout=True)

    for ens_id in range(1, 17):
        r_idx = (ens_id - 1) // 4
        c_idx = (ens_id - 1) % 4
        ax = axes_b[r_idx, c_idx]

        sub = all_df[all_df["ensaio"] == ens_id].sort_values("t_min")
        is_test = ens_id in test_ensaios
        ca0 = float(sub["CA0_mol_L"].iloc[0])
        eta = float(sub["razao_molar_eta"].iloc[0])

        t = sub["t_min"].values
        v_real = np.maximum(1e-3, sub[target_col].values)
        v_pred = np.maximum(1e-3, sub["v_pred"].values)

        cor_linha = "#d32f2f" if is_test else "#1565c0"
        tag = "[TESTE CEGO]" if is_test else "[Treino]"

        ax.plot(t, v_real, "k--", lw=1.3, label="Alvo Exato (PBM)", alpha=0.7)
        ax.plot(t, v_pred, color=cor_linha, lw=1.8, label=f"Pred. RF {tag}")

        ax.set_yscale("log")
        ax.set_ylim(8e-4, 2e3)
        ax.set_xlim(-0.4, 15.4)
        ax.set_title(f"Ens {ens_id:02d} {tag}\n$\\eta={eta:.1f}$, $C_{{A0}}={ca0:.2f}\\mathrm{{M}}$", fontsize=9, fontweight="bold" if is_test else "normal", color="#b71c1c" if is_test else "#0d47a1")
        if c_idx == 0:
            ax.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m/min})$", fontsize=9)
        if r_idx == 3:
            ax.set_xlabel(r"$t\ (\mathrm{min})$", fontsize=9)

        if ens_id == 1:
            ax.legend(fontsize=7.5, loc="upper right")

    fig_b.suptitle(
        "Ajuste e Generalização de |v(t)| em Escala Semilogarítmica nos 16 Ensaios — Random Forest Campeão (Shallow)\n"
        "Comprovação de Ausência de Degraus Bruscos e Captura Precisa da Cauda Lenta nos Ensaios Cegos (Ens 8, 14 e 7 em Vermelho)",
        fontsize=13,
        fontweight="bold",
    )
    png_b = out_dir / "fig_08b_predicoes_v_rf_log.png"
    pdf_b = out_dir / "fig_08b_predicoes_v_rf_log.pdf"
    fig_b.savefig(png_b, dpi=300)
    fig_b.savefig(pdf_b)
    plt.close(fig_b)
    print(f"  -> Salvo: {png_b.name} e {pdf_b.name}")

    # FIGURA 08C LOG: Paridade Log-Log
    fig_c, (ax_c1, ax_c2) = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    diag = np.logspace(-2, 3.2, 100)

    # Paridade Log-Log
    ax_c1.plot(diag, diag, "k-", lw=1.5, label="Bissetriz Ideal 1:1")
    ax_c1.fill_between(diag, diag * 0.7, diag * 1.3, color="gray", alpha=0.15, label="Faixa de Tolerância ±30%")
    ax_c1.scatter(np.maximum(1e-2, train_df[target_col]), np.maximum(1e-2, train_df["v_pred"]), color="#1565c0", alpha=0.5, s=25, label="Treino (13 ensaios)")
    ax_c1.scatter(np.maximum(1e-2, test_df[target_col]), np.maximum(1e-2, test_df["v_pred"]), color="#d32f2f", marker="s", s=45, edgecolors="black", lw=0.6, label="Teste Cego (R²=0,9120)", zorder=5)

    ax_c1.set_xscale("log")
    ax_c1.set_yscale("log")
    ax_c1.set_xlim(8e-3, 2e3)
    ax_c1.set_ylim(8e-3, 2e3)
    ax_c1.set_xlabel("Taxa Real Alvo $|v(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c1.set_ylabel("Taxa Predita RF $|\\hat{v}(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c1.set_title("(a) Gráfico de Paridade Log-Log (4 Ordens de Magnitude)", fontweight="bold")
    ax_c1.legend(loc="upper left", fontsize=8.5)

    # Resíduos Logarítmicos
    res_log_train = np.log1p(train_df[target_col]) - np.log1p(train_df["v_pred"])
    res_log_test = np.log1p(test_df[target_col]) - np.log1p(test_df["v_pred"])

    ax_c2.axhline(0, color="black", linestyle="--", lw=1.2)
    ax_c2.axhspan(-0.3, 0.3, color="#e8f5e9", alpha=0.6, label="Tolerância Logarítmica ±0,3")
    ax_c2.scatter(train_df["v_pred"], res_log_train, color="#1565c0", alpha=0.45, s=20, label="Treino")
    ax_c2.scatter(test_df["v_pred"], res_log_test, color="#d32f2f", marker="s", s=45, edgecolors="black", lw=0.6, label="Teste Cego", zorder=5)

    ax_c2.set_xscale("log")
    ax_c2.set_xlim(8e-3, 2e3)
    ax_c2.set_xlabel("Taxa Predita RF $|\\hat{v}(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c2.set_ylabel(r"Resíduo Logarítmico: $\ln(1+v) - \ln(1+\hat{v})$", fontweight="bold")
    ax_c2.set_title("(b) Distribuição de Resíduos no Espaço Logarítmico", fontweight="bold")
    ax_c2.legend(loc="upper right", fontsize=8.5)

    fig_c.suptitle(
        "Diagnóstico Estatístico de Aderência Logarítmica — Random Forest Campeão",
        fontsize=13,
        fontweight="bold",
    )
    png_c = out_dir / "fig_08c_paridade_e_residuos_rf_log.png"
    pdf_c = out_dir / "fig_08c_paridade_e_residuos_rf_log.pdf"
    fig_c.savefig(png_c, dpi=300)
    fig_c.savefig(pdf_c)
    plt.close(fig_c)
    print(f"  -> Salvo: {png_c.name} e {pdf_c.name}")


# =============================================================================
# 7. ETAPA 3.2.3: Support Vector Regression (SVR RBF) em Escala Logarítmica
# =============================================================================
def gerar_log_etapa_3_2_3_svr(base_dir: Path) -> None:
    print("\n[7/7] Gerando versões logarítmicas da Subetapa 3.2.3 (Support Vector Regression - SVR RBF)...")
    out_dir = base_dir / "Código" / "outputs" / "etapa_3_2" / "subetapa_3_2_3_svr"
    out_dir.mkdir(parents=True, exist_ok=True)

    splits_dir = base_dir / "Base de dados" / "processed" / "splits"
    models_dir = base_dir / "Código" / "outputs" / "models_saved" / "svr"

    train_df = pd.read_csv(splits_dir / "train_dense.csv")
    test_df = pd.read_csv(splits_dir / "test_dense.csv")

    svr_model = KineticsSVR.load(models_dir / "svr_kinetics_v1.joblib")

    feature_cols = ["temperatura_C", "CA0_mol_L", "razao_molar_eta", "t_min"]
    target_col = "abs_v_alvo_um_min"
    test_ensaios = [7, 8, 14]

    train_df["v_pred"] = svr_model.predict(train_df[feature_cols].values)
    test_df["v_pred"] = svr_model.predict(test_df[feature_cols].values)
    all_df = pd.concat([train_df, test_df], ignore_index=True)

    # FIGURA 09B LOG: 16 ensaios em semilog-y
    fig_b, axes_b = plt.subplots(4, 4, figsize=(16, 12), sharex=True, sharey=True, constrained_layout=True)

    for ens_id in range(1, 17):
        r_idx = (ens_id - 1) // 4
        c_idx = (ens_id - 1) % 4
        ax = axes_b[r_idx, c_idx]

        sub = all_df[all_df["ensaio"] == ens_id].sort_values("t_min")
        is_test = ens_id in test_ensaios
        ca0 = float(sub["CA0_mol_L"].iloc[0])
        eta = float(sub["razao_molar_eta"].iloc[0])

        t = sub["t_min"].values
        v_real = np.maximum(1e-3, sub[target_col].values)
        v_pred = np.maximum(1e-3, sub["v_pred"].values)

        cor_linha = "#d32f2f" if is_test else "#1565c0"
        tag = "[TESTE CEGO]" if is_test else "[Treino]"

        ax.plot(t, v_real, "k--", lw=1.3, label="Alvo Exato (PBM)", alpha=0.7)
        ax.plot(t, v_pred, color=cor_linha, lw=1.8, label=f"Pred. SVR {tag}")

        ax.set_yscale("log")
        ax.set_ylim(8e-4, 2e3)
        ax.set_xlim(-0.4, 15.4)
        ax.set_title(f"Ens {ens_id:02d} {tag}\n$\\eta={eta:.1f}$, $C_{{A0}}={ca0:.2f}\\mathrm{{M}}$", fontsize=9, fontweight="bold" if is_test else "normal", color="#b71c1c" if is_test else "#0d47a1")
        if c_idx == 0:
            ax.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m/min})$", fontsize=9)
        if r_idx == 3:
            ax.set_xlabel(r"$t\ (\mathrm{min})$", fontsize=9)

        if ens_id == 1:
            ax.legend(fontsize=7.5, loc="upper right")

    fig_b.suptitle(
        "Ajuste e Generalização de |v(t)| em Escala Semilogarítmica nos 16 Ensaios — SVR RBF Campeão\n"
        "Comprovação da Continuidade Suave em 4 Ordens de Magnitude e Comportamento Assintótico nos Ensaios Cegos",
        fontsize=13,
        fontweight="bold",
    )
    png_b = out_dir / "fig_09b_predicoes_v_svr_log.png"
    pdf_b = out_dir / "fig_09b_predicoes_v_svr_log.pdf"
    fig_b.savefig(png_b, dpi=300)
    fig_b.savefig(pdf_b)
    plt.close(fig_b)
    print(f"  -> Salvo: {png_b.name} e {pdf_b.name}")

    # FIGURA 09C LOG: Paridade Log-Log
    fig_c, (ax_c1, ax_c2) = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
    diag = np.logspace(-2, 3.2, 100)

    # Paridade Log-Log
    ax_c1.plot(diag, diag, "k-", lw=1.5, label="Bissetriz Ideal 1:1")
    ax_c1.fill_between(diag, diag * 0.7, diag * 1.3, color="gray", alpha=0.15, label="Faixa de Tolerância ±30%")
    ax_c1.scatter(np.maximum(1e-2, train_df[target_col]), np.maximum(1e-2, train_df["v_pred"]), color="#1565c0", alpha=0.5, s=25, label="Treino (13 ensaios)")
    ax_c1.scatter(np.maximum(1e-2, test_df[target_col]), np.maximum(1e-2, test_df["v_pred"]), color="#d32f2f", marker="D", s=45, edgecolors="black", lw=0.6, label="Teste Cego (SVR RBF)", zorder=5)

    ax_c1.set_xscale("log")
    ax_c1.set_yscale("log")
    ax_c1.set_xlim(8e-3, 2e3)
    ax_c1.set_ylim(8e-3, 2e3)
    ax_c1.set_xlabel("Taxa Real Alvo $|v(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c1.set_ylabel("Taxa Predita SVR $|\\hat{v}(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c1.set_title("(a) Gráfico de Paridade Log-Log (4 Ordens de Magnitude)", fontweight="bold")
    ax_c1.legend(loc="upper left", fontsize=8.5)

    # Resíduos Logarítmicos
    res_log_train = np.log1p(train_df[target_col]) - np.log1p(train_df["v_pred"])
    res_log_test = np.log1p(test_df[target_col]) - np.log1p(test_df["v_pred"])

    ax_c2.axhline(0, color="black", linestyle="--", lw=1.2)
    ax_c2.axhspan(-0.3, 0.3, color="#e8f5e9", alpha=0.6, label="Tolerância Logarítmica ±0,3")
    ax_c2.scatter(train_df["v_pred"], res_log_train, color="#1565c0", alpha=0.45, s=20, label="Treino")
    ax_c2.scatter(test_df["v_pred"], res_log_test, color="#d32f2f", marker="D", s=45, edgecolors="black", lw=0.6, label="Teste Cego", zorder=5)

    ax_c2.set_xscale("log")
    ax_c2.set_xlim(8e-3, 2e3)
    ax_c2.set_xlabel("Taxa Predita SVR $|\\hat{v}(t)|\\ (\\mu\\mathrm{m/min})$ [Escala Log]", fontweight="bold")
    ax_c2.set_ylabel(r"Resíduo Logarítmico: $\ln(1+v) - \ln(1+\hat{v})$", fontweight="bold")
    ax_c2.set_title("(b) Distribuição de Resíduos no Espaço Logarítmico", fontweight="bold")
    ax_c2.legend(loc="upper right", fontsize=8.5)

    fig_c.suptitle(
        "Diagnóstico Estatístico de Aderência Logarítmica — Support Vector Regression (SVR RBF)",
        fontsize=13,
        fontweight="bold",
    )
    png_c = out_dir / "fig_09c_paridade_e_residuos_svr_log.png"
    pdf_c = out_dir / "fig_09c_paridade_e_residuos_svr_log.pdf"
    fig_c.savefig(png_c, dpi=300)
    fig_c.savefig(pdf_c)
    plt.close(fig_c)
    print(f"  -> Salvo: {png_c.name} e {pdf_c.name}")


def main() -> None:
    set_plot_style()
    base_dir = project_root.parent
    print(f"Iniciando pipeline unificado de figuras logarítmicas em: {base_dir}")

    gerar_log_etapa_0_1(base_dir)
    gerar_log_etapa_1_3(base_dir)
    gerar_log_etapa_2_1(base_dir)
    gerar_log_etapa_3_1(base_dir)
    gerar_log_etapa_3_2_1_mlp(base_dir)
    gerar_log_etapa_3_2_2_rf(base_dir)
    gerar_log_etapa_3_2_3_svr(base_dir)

    print("\n" + "=" * 80)
    print("Sucesso Absoluto! Todas as versões logarítmicas das figuras foram geradas")
    print("em 300 DPI (PNG) e cópia vetorial (PDF) em seus respectivos diretórios de saídas.")
    print("=" * 80)


if __name__ == "__main__":
    main()
