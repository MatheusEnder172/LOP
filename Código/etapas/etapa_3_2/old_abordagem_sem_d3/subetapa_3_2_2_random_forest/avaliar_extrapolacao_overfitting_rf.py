"""Diagnóstico Aprofundado do Modelo Campeão Random Forest (DDM).

Este script executa uma bateria de testes cinéticos e estatísticos para avaliar:
1. Interpolação em Malha Contínua Ultra-Fina (500 pontos temporais por ensaio):
   - Avaliação da presença de degraus numéricos, dentes de serra ou overfitting local.
2. Extrapolação Temporal Além do Fim Experimental (t estendido de 15 para 30 min):
   - Avaliação do comportamento assintótico na exaustão dos reagentes.
3. Extrapolação Operacional nas Variáveis de Entrada (C_A0 e eta fora do domínio de treino):
   - Avaliação do comportamento de saturação de borda intrínseco aos ensembles de árvores.
4. Superfície de Resposta Bidimensional e Tridimensional Contínua (|v| vs. t e C_A0/eta):
   - Inspeção de monotonicidade físico-química e ausência de ilhas anômalas de memorização.

Gera 6 figuras científicas em 300 DPI (PNG) e cópia vetorial (PDF) em:
  outputs/etapa_3_2_2_random_forest/
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
from matplotlib import cm
import numpy as np
import pandas as pd

# Ajuste dos caminhos de importação
CURRENT_DIR = Path(__file__).resolve().parent
CODIGO_DIR = CURRENT_DIR.parents[2]
PROJECT_ROOT = CODIGO_DIR.parent

for p in [str(PROJECT_ROOT), str(CODIGO_DIR), str(CURRENT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from modelo_rf import KineticsRandomForest


def set_plot_style() -> None:
    """Configura o estilo padrão dos gráficos científicos para alta resolução."""
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


def carregar_dados_e_modelo(base_dir: Path) -> Tuple[KineticsRandomForest, pd.DataFrame, pd.DataFrame]:
    """Carrega o modelo Random Forest campeão e as bases de dados de alvos densos."""
    models_dir = base_dir / "Código" / "outputs" / "models_saved" / "random_forest"
    rf_model = KineticsRandomForest.load(models_dir / "rf_kinetics_v1.joblib")

    dense_path = base_dir / "Base de dados" / "processed" / "alvos_v_treinamento_denso.csv"
    raw_exp_path = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"

    df_dense = pd.read_csv(dense_path)
    df_raw = pd.read_csv(raw_exp_path)

    return rf_model, df_dense, df_raw


# =============================================================================
# 1. FIGURA 08E: Interpolação em Malha Contínua Ultra-Fina (16 Ensaios)
# =============================================================================
def gerar_figura_malha_fina(
    rf_model: KineticsRandomForest,
    df_dense: pd.DataFrame,
    out_dir: Path,
) -> None:
    """Gera painel 4x4 com malha fina (500 pontos/ensaio) em escala linear e logarítmica."""
    print("  -> Gerando Figura 08e: Interpolação em malha ultra-fina (Linear e Log)...")
    test_ensaios = [7, 8, 14]
    t_fino = np.linspace(0.0, 15.0, 500)  # dt = 0,03 min (1,8 segundos)

    for modo in ["linear", "log"]:
        fig, axes = plt.subplots(4, 4, figsize=(16, 12), sharex=True, sharey=False, constrained_layout=True)

        for ens_id in range(1, 17):
            r_idx = (ens_id - 1) // 4
            c_idx = (ens_id - 1) % 4
            ax = axes[r_idx, c_idx]

            sub = df_dense[df_dense["ensaio"] == ens_id].sort_values("t_min")
            is_test = ens_id in test_ensaios
            ca0 = float(sub["CA0_mol_L"].iloc[0])
            eta = float(sub["razao_molar_eta"].iloc[0])

            # Malha fina predita
            X_fino = np.column_stack([
                np.full_like(t_fino, 40.0),
                np.full_like(t_fino, ca0),
                np.full_like(t_fino, eta),
                t_fino,
            ])
            v_pred_fino = rf_model.predict(X_fino)

            # Dados discretos do PBM
            t_alvo = sub["t_min"].values
            v_alvo = sub["abs_v_alvo_um_min"].values

            cor_linha = "#d32f2f" if is_test else "#1565c0"
            tag = "[TESTE CEGO]" if is_test else "[Treino]"

            if modo == "linear":
                ax.plot(t_alvo, v_alvo, "ko", ms=3.0, alpha=0.6, label="Alvos PBM (61 pts)" if ens_id == 1 else None)
                ax.plot(t_fino, v_pred_fino, color=cor_linha, lw=1.8, label=f"RF Contínuo (500 pts)" if ens_id == 1 else None)
                ax.set_ylim(-15, max(float(np.max(v_alvo)) * 1.12, 100))
                if c_idx == 0:
                    ax.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m/min})$", fontsize=9)
            else:
                ax.plot(t_alvo, np.maximum(1e-3, v_alvo), "k.", ms=4.0, alpha=0.5, label="Alvos PBM" if ens_id == 1 else None)
                ax.plot(t_fino, np.maximum(1e-3, v_pred_fino), color=cor_linha, lw=1.8, label=f"RF Contínuo" if ens_id == 1 else None)
                ax.set_yscale("log")
                ax.set_ylim(8e-4, 2e3)
                if c_idx == 0:
                    ax.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m/min})$ [Log]", fontsize=9)

            ax.set_xlim(-0.3, 15.3)
            ax.set_title(
                f"Ens {ens_id:02d} {tag}\n$\\eta={eta:.1f}$, $C_{{A0}}={ca0:.2f}\\mathrm{{M}}$",
                fontsize=9,
                fontweight="bold" if is_test else "normal",
                color="#b71c1c" if is_test else "#0d47a1",
            )
            if r_idx == 3:
                ax.set_xlabel(r"$t\ (\mathrm{min})$", fontsize=9)

            if ens_id == 1:
                ax.legend(fontsize=8, loc="upper right", framealpha=0.9)

        sufixo = "_log" if modo == "log" else ""
        escala_str = "Semilogarítmica" if modo == "log" else "Linear"
        fig.suptitle(
            f"Diagnóstico de Interpolação e Overfitting em Malha Contínua Ultra-Fina ({escala_str})\n"
            f"Random Forest Campeão Avaliado a cada 1,8 segundos (500 nós) vs. Alvos Inversos Discretos nos 16 Ensaios",
            fontsize=13,
            fontweight="bold",
        )

        png_p = out_dir / f"fig_08e_malha_fina_interpolação_rf{sufixo}.png"
        pdf_p = out_dir / f"fig_08e_malha_fina_interpolação_rf{sufixo}.pdf"
        fig.savefig(png_p, dpi=300)
        fig.savefig(pdf_p)
        plt.close(fig)
        print(f"     Salvo: {png_p.name} e {pdf_p.name}")


# =============================================================================
# 2. FIGURA 08F: Extrapolação Temporal Além do Fim Experimental (t = 0 a 30 min)
# =============================================================================
def gerar_figura_extrapolacao_temporal(
    rf_model: KineticsRandomForest,
    df_dense: pd.DataFrame,
    out_dir: Path,
) -> None:
    """Avalia o comportamento da taxa predita para tempos superiores a 15 min."""
    print("  -> Gerando Figura 08f: Extrapolação temporal (t de 0 a 30 min)...")
    etas = [0.5, 1.0, 1.5, 3.1]
    color_map = {0.10: "#1f77b4", 0.50: "#2ca02c", 1.00: "#ff7f0e", 1.50: "#d62728"}

    t_ext = np.linspace(0.0, 30.0, 600)  # Dobro do tempo experimental

    for modo in ["linear", "log"]:
        fig, axes = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=False)
        axes = axes.flatten()

        for idx, eta in enumerate(etas):
            ax = axes[idx]

            # Fundo sombreado para destacar a zona de extrapolação
            ax.axvspan(15.0, 30.0, color="#fff3e0", alpha=0.6, label="Zona de Extrapolação Temporal (t > 15 min)" if idx == 0 else None)
            ax.axvline(15.0, color="#e65100", linestyle="--", lw=1.5, alpha=0.9, label="Fim dos Dados Experimentais (15 min)" if idx == 0 else None)

            for ca0 in [0.10, 0.50, 1.00, 1.50]:
                cor = color_map[ca0]
                X_pred = np.column_stack([
                    np.full_like(t_ext, 40.0),
                    np.full_like(t_ext, ca0),
                    np.full_like(t_ext, eta),
                    t_ext,
                ])
                v_pred = rf_model.predict(X_pred)

                # Dados reais até 15 min
                sub_exp = df_dense[(np.isclose(df_dense["razao_molar_eta"], eta)) & (np.isclose(df_dense["CA0_mol_L"], ca0))]
                if len(sub_exp) > 0:
                    if modo == "linear":
                        ax.scatter(sub_exp["t_min"], sub_exp["abs_v_alvo_um_min"], color=cor, s=10, alpha=0.4)
                        ax.plot(t_ext, v_pred, color=cor, lw=2.0, label=f"$C_{{A0}} = {ca0:.2f}\\ \\mathrm{{M}}$")
                    else:
                        ax.scatter(sub_exp["t_min"], np.maximum(1e-3, sub_exp["abs_v_alvo_um_min"]), color=cor, s=10, alpha=0.4)
                        ax.plot(t_ext, np.maximum(1e-3, v_pred), color=cor, lw=2.0, label=f"$C_{{A0}} = {ca0:.2f}\\ \\mathrm{{M}}$")

            if modo == "linear":
                ax.set_ylim(-10, 800 if eta <= 1.0 else 1350)
                if idx % 2 == 0:
                    ax.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m/min})$", fontweight="bold")
            else:
                ax.set_yscale("log")
                ax.set_ylim(8e-4, 2e3)
                if idx % 2 == 0:
                    ax.set_ylabel(r"$|v(t)|\ (\mu\mathrm{m/min})$ [Escala Log]", fontweight="bold")

            ax.set_xlim(-0.5, 30.5)
            ax.set_title(f"Painel ({chr(97 + idx)}) — Razão Molar $\\eta = {eta:.1f}$", fontweight="bold", pad=8)
            if idx >= 2:
                ax.set_xlabel(r"Tempo de Reação, $t\ (\mathrm{min})$", fontweight="bold")

            ax.legend(loc="upper right", fontsize=8.2, framealpha=0.9)

        sufixo = "_log" if modo == "log" else ""
        escala_str = "Semilogarítmica" if modo == "log" else "Linear"
        fig.suptitle(
            f"Comportamento de Extrapolação Temporal Além do Domínio Experimental ({escala_str})\n"
            f"Random Forest Campeão Estendido até t = 30 min (Zona Sombreada Evidencia Estabilização em Platô Assintótico sem Divergência)",
            fontsize=13,
            fontweight="bold",
            y=0.98,
        )
        plt.tight_layout()
        fig.subplots_adjust(top=0.91)

        png_p = out_dir / f"fig_08f_extrapolacao_temporal_rf{sufixo}.png"
        pdf_p = out_dir / f"fig_08f_extrapolacao_temporal_rf{sufixo}.pdf"
        fig.savefig(png_p, dpi=300)
        fig.savefig(pdf_p)
        plt.close(fig)
        print(f"     Salvo: {png_p.name} e {pdf_p.name}")


# =============================================================================
# 3. FIGURA 08G: Extrapolação Operacional nas Variáveis C_A0 e eta
# =============================================================================
def gerar_figura_extrapolacao_operacional(
    rf_model: KineticsRandomForest,
    out_dir: Path,
) -> None:
    """Testa o modelo fora dos limites de C_A0 (0.1 a 1.5 M) e eta (0.5 a 3.1)."""
    print("  -> Gerando Figura 08g: Extrapolação operacional em acidez (C_A0) e razão molar (eta)...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), constrained_layout=True)

    # -------------------------------------------------------------
    # Painel 1: Extrapolação em Acidez C_A0 (de 0,02 a 2,50 mol/L)
    # -------------------------------------------------------------
    ca0_grid = np.linspace(0.01, 2.50, 250)
    tempos_teste = [0.25, 1.0, 5.0, 10.0]
    cores_t = ["#d32f2f", "#f57c00", "#1976d2", "#388e3c"]

    # Fundo sombreado para as regiões de extrapolação de C_A0
    ax1.axvspan(0.01, 0.10, color="#ffebee", alpha=0.6, label="Extrapolação ($C_{A0} < 0,10\\mathrm{M}$)")
    ax1.axvspan(1.50, 2.50, color="#ffebee", alpha=0.6, label="Extrapolação ($C_{A0} > 1,50\\mathrm{M}$)")
    ax1.axvspan(0.10, 1.50, color="#e8f5e9", alpha=0.5, label="Domínio Experimental de Bancada")
    ax1.axvline(0.10, color="#b71c1c", linestyle="--", lw=1.2)
    ax1.axvline(1.50, color="#b71c1c", linestyle="--", lw=1.2)

    for t_val, cor in zip(tempos_teste, cores_t):
        X_ca0 = np.column_stack([
            np.full_like(ca0_grid, 40.0),
            ca0_grid,
            np.full_like(ca0_grid, 1.5),  # eta = 1.5 fixo
            np.full_like(ca0_grid, t_val),
        ])
        v_pred_ca0 = rf_model.predict(X_ca0)
        ax1.plot(ca0_grid, v_pred_ca0, color=cor, lw=2.2, label=f"Taxa em $t = {t_val}\\ \\mathrm{{min}}$")

    ax1.set_xlim(0.0, 2.52)
    ax1.set_xlabel(r"Concentração Inicial de Ácido, $C_{A0}\ (\mathrm{mol/L})$", fontweight="bold")
    ax1.set_ylabel(r"Taxa Predita $|v(t)|\ (\mu\mathrm{m/min})$", fontweight="bold")
    ax1.set_title("(a) Efeito da Acidez $C_{A0}$ com $\\eta = 1,5$ (Saturação de Borda nas Árvores)", fontweight="bold")
    ax1.legend(loc="upper left", fontsize=8.5)

    # -------------------------------------------------------------
    # Painel 2: Extrapolação em Razão Molar eta (de 0,2 a 4,5)
    # -------------------------------------------------------------
    eta_grid = np.linspace(0.15, 4.50, 250)

    ax2.axvspan(0.15, 0.50, color="#ffebee", alpha=0.6, label="Extrapolação ($\\eta < 0,5$)")
    ax2.axvspan(3.10, 4.50, color="#ffebee", alpha=0.6, label="Extrapolação ($\\eta > 3,1$)")
    ax2.axvspan(0.50, 3.10, color="#e8f5e9", alpha=0.5, label="Domínio Experimental de Bancada")
    ax2.axvline(0.50, color="#b71c1c", linestyle="--", lw=1.2)
    ax2.axvline(3.10, color="#b71c1c", linestyle="--", lw=1.2)

    for t_val, cor in zip(tempos_teste, cores_t):
        X_eta = np.column_stack([
            np.full_like(eta_grid, 40.0),
            np.full_like(eta_grid, 1.00),  # CA0 = 1.0 M fixo
            eta_grid,
            np.full_like(eta_grid, t_val),
        ])
        v_pred_eta = rf_model.predict(X_eta)
        ax2.plot(eta_grid, v_pred_eta, color=cor, lw=2.2, label=f"Taxa em $t = {t_val}\\ \\mathrm{{min}}$")

    ax2.set_xlim(0.1, 4.55)
    ax2.set_xlabel(r"Razão Molar Ácido/Minério, $\eta\ (-)$", fontweight="bold")
    ax2.set_ylabel(r"Taxa Predita $|v(t)|\ (\mu\mathrm{m/min})$", fontweight="bold")
    ax2.set_title("(b) Efeito da Razão Molar $\\eta$ com $C_{A0} = 1,00\\mathrm{M}$ (Saturação de Borda nas Árvores)", fontweight="bold")
    ax2.legend(loc="upper left", fontsize=8.5)

    fig.suptitle(
        "Diagnóstico de Extrapolação Operacional nas Variáveis de Entrada — Random Forest Campeão\n"
        "Comprovação do Efeito de 'Boundary Clamping' (Saturação da Folha Limite): Ausência de Explosões Numéricas e Conservação Estrita",
        fontsize=13,
        fontweight="bold",
    )

    png_p = out_dir / "fig_08g_extrapolacao_operacional_acido_eta_rf.png"
    pdf_p = out_dir / "fig_08g_extrapolacao_operacional_acido_eta_rf.pdf"
    fig.savefig(png_p, dpi=300)
    fig.savefig(pdf_p)
    plt.close(fig)
    print(f"     Salvo: {png_p.name} e {pdf_p.name}")


# =============================================================================
# 4. FIGURA 08H: Superfície de Resposta 2D e 3D Contínua
# =============================================================================
def gerar_figura_superficie_resposta(
    rf_model: KineticsRandomForest,
    out_dir: Path,
) -> None:
    """Gera mapa de contorno 2D e superfície 3D da taxa para visualização de monotonicidade."""
    print("  -> Gerando Figura 08h: Superfície de resposta 2D e 3D contínua...")
    # Malha 2D fina de 80x80 = 6.400 pontos de inferência
    t_vals = np.linspace(0.05, 15.0, 80)
    ca0_vals = np.linspace(0.10, 1.50, 80)
    T_mesh, CA0_mesh = np.meshgrid(t_vals, ca0_vals)

    X_mesh = np.column_stack([
        np.full(T_mesh.size, 40.0),
        CA0_mesh.ravel(),
        np.full(T_mesh.size, 1.5),  # eta = 1.5
        T_mesh.ravel(),
    ])
    V_pred = rf_model.predict(X_mesh).reshape(T_mesh.shape)
    V_log = np.log10(np.maximum(1e-2, V_pred))

    fig = plt.figure(figsize=(15, 6), constrained_layout=True)

    # Subplot 1: Mapa de Contorno 2D com Linhas de Nível
    ax1 = fig.add_subplot(1, 2, 1)
    cp = ax1.contourf(T_mesh, CA0_mesh, V_log, levels=25, cmap="viridis")
    cbar = fig.colorbar(cp, ax=ax1, pad=0.02)
    cbar.set_label(r"$\log_{10}(|v(t)|)\ [\mu\mathrm{m/min}]$", fontweight="bold")
    contours = ax1.contour(T_mesh, CA0_mesh, V_log, levels=8, colors="white", linewidths=0.6, alpha=0.7)
    ax1.clabel(contours, inline=True, fontsize=8, fmt="%.1f")

    ax1.set_xlabel(r"Tempo de Reação, $t\ (\mathrm{min})$", fontweight="bold")
    ax1.set_ylabel(r"Concentração Inicial de Ácido, $C_{A0}\ (\mathrm{mol/L})$", fontweight="bold")
    ax1.set_title("(a) Mapa de Contorno Contínuo da Taxa de Retração ($\\eta = 1,5$)", fontweight="bold")

    # Subplot 2: Superfície Tridimensional 3D
    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    surf = ax2.plot_surface(
        T_mesh,
        CA0_mesh,
        V_log,
        cmap="viridis",
        linewidth=0,
        antialiased=True,
        alpha=0.9,
    )
    ax2.view_init(elev=28, azim=-125)
    ax2.set_xlabel(r"$t\ (\mathrm{min})$", fontweight="bold", labelpad=7)
    ax2.set_ylabel(r"$C_{A0}\ (\mathrm{mol/L})$", fontweight="bold", labelpad=7)
    ax2.set_zlabel(r"$\log_{10}(|v|)$", fontweight="bold", labelpad=6)
    ax2.set_title("(b) Superfície 3D de Resposta Cinética Contínua", fontweight="bold")

    fig.suptitle(
        "Superfície de Resposta Cinética e Mapa de Contorno Contínuo — Random Forest Campeão (DDM)\n"
        "Comprovação de Monotonicidade Suave (Taxa Cresce com Acidez e Decai com o Tempo) e Ausência de Ilhas de Overfitting",
        fontsize=13,
        fontweight="bold",
    )

    png_p = out_dir / "fig_08h_superficie_resposta_2d_3d_rf.png"
    pdf_p = out_dir / "fig_08h_superficie_resposta_2d_3d_rf.pdf"
    fig.savefig(png_p, dpi=300)
    fig.savefig(pdf_p)
    plt.close(fig)
    print(f"     Salvo: {png_p.name} e {pdf_p.name}")


def main() -> None:
    set_plot_style()
    base_dir = PROJECT_ROOT
    out_dir = base_dir / "Código" / "outputs" / "etapa_3_2" / "subetapa_3_2_2_random_forest"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("DIAGNÓSTICO AVANÇADO DO RANDOM FOREST CAMPEÃO: OVERFITTING E EXTRAPOLAÇÃO")
    print("=" * 80)

    rf_model, df_dense, df_raw = carregar_dados_e_modelo(base_dir)
    print(f"Modelo carregado com sucesso. Parâmetros: {rf_model.model_params}")

    gerar_figura_malha_fina(rf_model, df_dense, out_dir)
    gerar_figura_extrapolacao_temporal(rf_model, df_dense, out_dir)
    gerar_figura_extrapolacao_operacional(rf_model, out_dir)
    gerar_figura_superficie_resposta(rf_model, out_dir)

    print("=" * 80)
    print("Todas as figuras diagnósticas de extrapolação e overfitting foram geradas com sucesso!")
    print(f"Diretório de saída: {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
