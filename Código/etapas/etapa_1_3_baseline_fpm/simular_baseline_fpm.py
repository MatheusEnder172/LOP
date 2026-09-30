"""
Simulação e Validação do Baseline Fenomenológico Puro (FPM Puro) - Etapa 1.3.
Executa a simulação dos 16 ensaios de bancada de lixiviação de zinco com o
modelo puramente fenomenológico (alpha_nominal = 5500 µm/min) e compara os
resultados com os dados experimentais de Bortot Coelho (2017).

Gera:
- Tabela de métricas quantitativas (R², RMSE, MAE) por ensaio e global.
- Gráfico comparativo de alta resolução (300 DPI PNG e PDF vetorial).
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Adicionar a pasta raiz de código ao path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.physics.granulometry import RosinRammlerBennet
from src.physics.kinetics import LeachingKinetics
from src.physics.pbm_batch import BatchPBMSolver


def main() -> None:
    # Configuração de diretórios
    base_dir = project_root.parent
    data_path = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    output_dir = base_dir / "Código" / "outputs" / "etapa_1_3"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Carregando dados experimentais de: {data_path}")
    df_exp = pd.read_csv(data_path)

    # Inicializar o resolvedor PBM com parâmetros nominais
    solver = BatchPBMSolver()

    # Preparar malha temporal fina para traçado suave das curvas teóricas
    t_fine = np.linspace(0.0, 15.0, 300)

    # Dicionário para armazenar métricas e resultados
    results_list = []
    simulations = {}
    all_y_true = []
    all_y_pred = []

    ensaios_unicos = sorted(df_exp["ensaio"].unique())
    print(f"Simulando {len(ensaios_unicos)} ensaios com o modelo FPM Baseline (alpha = 5500 µm/min)...")

    for ens in ensaios_unicos:
        df_ens = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
        ca0 = float(df_ens["CA0_mol_L"].iloc[0])
        eta = float(df_ens["razao_molar_eta"].iloc[0])
        t_exp = df_ens["t_min"].values
        x_exp = df_ens["XZn"].values

        # 1. Simulação nos pontos experimentais para avaliação métrica
        sim_eval = solver.simulate(ca0=ca0, eta=eta, t_eval=t_exp)
        x_pred_points = sim_eval["XZn"]

        # 2. Simulação em malha contínua para geração do gráfico
        sim_fine = solver.simulate(ca0=ca0, eta=eta, t_eval=t_fine)

        # Cálculo das métricas estatísticas
        r2 = float(r2_score(x_exp, x_pred_points))
        rmse = float(np.sqrt(mean_squared_error(x_exp, x_pred_points)))
        mae = float(mean_absolute_error(x_exp, x_pred_points))

        all_y_true.extend(x_exp)
        all_y_pred.extend(x_pred_points)

        results_list.append(
            {
                "ensaio": ens,
                "razao_molar_eta": eta,
                "CA0_mol_L": ca0,
                "R2": round(r2, 4),
                "RMSE": round(rmse, 4),
                "MAE": round(mae, 4),
                "X_exp_final": round(float(x_exp[-1]), 4),
                "X_fpm_final": round(float(x_pred_points[-1]), 4),
                "erro_final_absoluto": round(float(abs(x_exp[-1] - x_pred_points[-1])), 4),
            }
        )

        simulations[ens] = {
            "ca0": ca0,
            "eta": eta,
            "t_exp": t_exp,
            "x_exp": x_exp,
            "t_fine": t_fine,
            "x_fine": sim_fine["XZn"],
            "caf_fine": sim_fine["CAf"],
            "delta_fine": sim_fine["delta"],
        }

    # Métricas globais agregadas
    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)
    r2_global = float(r2_score(all_y_true, all_y_pred))
    rmse_global = float(np.sqrt(mean_squared_error(all_y_true, all_y_pred)))
    mae_global = float(mean_absolute_error(all_y_true, all_y_pred))

    df_metrics = pd.DataFrame(results_list)
    csv_out_path = output_dir / "tabela_metricas_baseline_fpm.csv"
    df_metrics.to_csv(csv_out_path, index=False)
    print(f"Tabela de métricas salva com sucesso em: {csv_out_path}")

    print("\n" + "=" * 65)
    print(f"DESEMPENHO GLOBAL DO FPM PURO (BASELINE FENOMENOLÓGICO):")
    print(f"  R² Global:   {r2_global:.4f}")
    print(f"  RMSE Global: {rmse_global:.4f} ({rmse_global*100:.2f}%)")
    print(f"  MAE Global:  {mae_global:.4f} ({mae_global*100:.2f}%)")
    print("=" * 65 + "\n")

    # =========================================================================
    # GERAÇÃO DO GRÁFICO CIENTÍFICO (PADRÃO 300 DPI + VETORIAL PDF)
    # =========================================================================
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    axes = axes.flatten()

    eta_grupos = [0.5, 1.0, 1.5, 3.1]
    color_map = {
        0.10: "#1f77b4",  # Azul
        0.50: "#2ca02c",  # Verde
        1.00: "#ff7f0e",  # Laranja
        1.50: "#d62728",  # Vermelho
    }
    marker_map = {
        0.10: "o",
        0.50: "s",
        1.00: "^",
        1.50: "D",
    }

    for idx, eta_val in enumerate(eta_grupos):
        ax = axes[idx]
        ensaios_eta = [e for e in ensaios_unicos if np.isclose(simulations[e]["eta"], eta_val)]

        # Ordenar ensaios por concentração inicial CA0 crescente
        ensaios_eta = sorted(ensaios_eta, key=lambda e: simulations[e]["ca0"])

        for ens in ensaios_eta:
            sim = simulations[ens]
            ca0 = sim["ca0"]
            cor = color_map.get(ca0, "black")
            marcador = marker_map.get(ca0, "o")

            # Linha teórica do FPM puro
            ax.plot(
                sim["t_fine"],
                sim["x_fine"],
                color=cor,
                linestyle="-",
                linewidth=2.0,
                alpha=0.85,
                label=f"FPM: $C_{{A0}} = {ca0:.2f}\\ \\text{{mol/L}}$",
            )

            # Pontos experimentais
            ax.plot(
                sim["t_exp"],
                sim["x_exp"],
                color=cor,
                marker=marcador,
                markersize=6.5,
                linestyle="none",
                markeredgecolor="black",
                markeredgewidth=0.8,
                label=f"Exp: $C_{{A0}} = {ca0:.2f}\\ \\text{{mol/L}}$",
            )

        # Configurações estéticas do subplot
        ax.set_title(
            f"Painel ({chr(97 + idx)}) — Razão Molar $\\eta = {eta_val}$",
            fontsize=13,
            fontweight="bold",
            pad=10,
        )
        ax.set_xlim(-0.3, 15.5)
        ax.set_ylim(-0.02, 1.08)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.tick_params(axis="both", which="major", labelsize=11)

        # Adicionar anotações explicativas de comportamento físico
        if eta_val == 0.5:
            ax.axhline(0.50, color="gray", linestyle=":", linewidth=1.2, label="Patamar Esteq. Exp. (0,50)")
            ax.axhline(0.383, color="black", linestyle="--", linewidth=1.2, label="Patamar FPM Nominal (0,38)")
        elif eta_val == 1.0:
            ax.axhline(0.766, color="black", linestyle="--", linewidth=1.2, label="Patamar FPM Nominal (0,766)")

        # Legenda limpa e organizada
        ax.legend(
            loc="lower right" if eta_val in [0.5, 1.0] else "lower right",
            fontsize=8.5,
            frameon=True,
            framealpha=0.9,
            edgecolor="#cccccc",
            ncol=2,
        )

    # Rótulos comuns dos eixos
    fig.text(0.5, 0.04, "Tempo de Reação, $t\\ (\\text{min})$", ha="center", fontsize=13, fontweight="bold")
    fig.text(
        0.04,
        0.5,
        "Conversão Mássica de Zinco, $X_{\\text{Zn}}\\ (-)$",
        va="center",
        rotation="vertical",
        fontsize=13,
        fontweight="bold",
    )

    fig.suptitle(
        f"Simulação do Baseline Fenomenológico Puro (FPM Puro) vs. Dados Experimentais de Bancada\n"
        f"Modelo PBM com $\\alpha_{{\\text{{nominal}}}} = 5500\\ \\mu\\text{{m/min}}$ | Métricas Globais: $R^2 = {r2_global:.4f}$, $\\text{{RMSE}} = {rmse_global:.4f}$, $\\text{{MAE}} = {mae_global:.4f}$",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    plt.subplots_adjust(top=0.90, bottom=0.09, left=0.08, right=0.97, hspace=0.22, wspace=0.15)

    png_path = output_dir / "fig_03_baseline_fpm_vs_experimento.png"
    pdf_path = output_dir / "fig_03_baseline_fpm_vs_experimento.pdf"

    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)

    print(f"Figura de alta resolução salva em: {png_path} (300 DPI)")
    print(f"Figura vetorial salva em: {pdf_path}")
    print("\nExecução da Etapa 1.3 finalizada com sucesso!")


if __name__ == "__main__":
    main()
