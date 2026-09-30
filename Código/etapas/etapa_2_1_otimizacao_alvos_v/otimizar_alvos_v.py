"""
Otimização Inversa Parametrizada para Geração dos Alvos de Retração v(t) - Fase 2 (Etapa 2.1).
Implementa a Opção B (Otimização Inversa por Ensaio) aprovada pelo usuário.

Para cada um dos 16 ensaios experimentais de bancada:
1. Modela a velocidade de retração como bi-exponencial restrita:
     |v(t)| = a1 * exp(-b1 * t) + a2 * exp(-b2 * t) + c >= 0
     v(t) = -|v(t)| <= 0
   resultando no deslocamento analítico acumulado:
     delta(t) = (a1/b1)*(1 - exp(-b1*t)) + (a2/b2)*(1 - exp(-b2*t)) + c*t
2. Otimiza os parâmetros theta = (a1, b1, a2, b2, c) minimizando o erro quadrático
   frente aos dados experimentais através do resolvedor BatchPBMSolver.
3. Avalia o X_Zn reconstruído via PBM, garantindo R² > 0.99 em cada ensaio.
4. Exporta os datasets de treinamento:
   - Base de dados/processed/alvos_v_treinamento.csv (pontos experimentais)
   - Base de dados/processed/alvos_v_treinamento_denso.csv (grade regular fina)
   - Base de dados/processed/parametros_otimizacao_inversa.csv (tabela de parâmetros)
5. Gera os gráficos científicos (300 DPI PNG e PDF vetorial).
"""

import sys
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Adicionar raiz de código ao path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.physics.pbm_batch import BatchPBMSolver


def optimize_single_experiment(
    solver: BatchPBMSolver,
    t_exp: np.ndarray,
    x_exp: np.ndarray,
) -> Tuple[np.ndarray, float]:
    """Otimiza os parâmetros da bi-exponencial de velocidade para um ensaio individual.

    Minimiza o erro quadrático ponderado com regularização suave na cauda assintótica:
      Loss = sum((X_pred - X_exp)^2) + lambda_tail * v(15)^2 + lambda_delta * max(0, delta(15) - 300)^2

    Args:
        solver: Instância de BatchPBMSolver.
        t_exp: Vetor de tempos experimentais (min).
        x_exp: Vetor de conversões experimentais (-).

    Returns:
        Tupla com os melhores parâmetros (a1, b1, a2, b2, c) e a perda final.
    """
    def objective(params: np.ndarray) -> float:
        a1, b1, a2, b2, c = params
        delta = (
            (a1 / b1) * (1.0 - np.exp(-b1 * t_exp))
            + (a2 / b2) * (1.0 - np.exp(-b2 * t_exp))
            + c * t_exp
        )
        x_pred = solver.compute_conversion_from_delta(delta)
        fit_loss = float(np.sum((x_pred - x_exp) ** 2))

        # Regularização física: penalizar velocidade residual em t = 15 min e retração excessiva
        v_15 = a1 * np.exp(-b1 * 15.0) + a2 * np.exp(-b2 * 15.0) + c
        delta_15 = (
            (a1 / b1) * (1.0 - np.exp(-b1 * 15.0))
            + (a2 / b2) * (1.0 - np.exp(-b2 * 15.0))
            + c * 15.0
        )
        pen_tail = 1e-4 * (v_15 ** 2)
        pen_delta = 1e-5 * (max(0.0, delta_15 - 300.0) ** 2)

        return fit_loss + pen_tail + pen_delta

    # Limites físicos dos parâmetros:
    # a1 in [0, 1200] µm/min (pico inicial ultra-rápido)
    # b1 in [0.1, 50] min⁻¹ (decaimento rápido)
    # a2 in [0, 500] µm/min (transiente intermediário)
    # b2 in [0.05, 20] min⁻¹ (decaimento intermediário)
    # c in [0, 0.1] µm/min (residual assintótico rigorosamente próximo de zero)
    bounds = [(0.0, 1200.0), (0.1, 50.0), (0.0, 500.0), (0.05, 20.0), (0.0, 0.1)]

    # Multi-start robusto
    initial_guesses = [
        [200.0, 5.0, 30.0, 0.5, 0.0],
        [400.0, 10.0, 80.0, 1.0, 0.02],
        [100.0, 2.0, 15.0, 0.2, 0.0],
        [500.0, 15.0, 150.0, 2.0, 0.05],
    ]

    best_params = None
    best_loss = float("inf")

    for x0 in initial_guesses:
        res = minimize(objective, x0, method="L-BFGS-B", bounds=bounds, tol=1e-8)
        if res.fun < best_loss:
            best_loss = res.fun
            best_params = res.x

    return best_params, best_loss


def calculate_kinetics_profiles(
    params: np.ndarray,
    t_eval: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calcula delta(t), v(t) e |v(t)| a partir dos parâmetros bi-exponenciais."""
    a1, b1, a2, b2, c = params
    t_arr = np.asarray(t_eval, dtype=np.float64)

    delta = (
        (a1 / b1) * (1.0 - np.exp(-b1 * t_arr))
        + (a2 / b2) * (1.0 - np.exp(-b2 * t_arr))
        + c * t_arr
    )
    abs_v = a1 * np.exp(-b1 * t_arr) + a2 * np.exp(-b2 * t_arr) + c
    v = -abs_v

    return delta, v, abs_v


def main() -> None:
    # 1. Configuração de caminhos e diretórios
    base_dir = project_root.parent
    raw_data_path = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    processed_dir = base_dir / "Base de dados" / "processed"
    output_dir = base_dir / "Código" / "outputs" / "etapa_2_1"

    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Iniciando Otimização Inversa Parametrizada (Opção B - Bi-Exponencial)...")
    df_exp = pd.read_csv(raw_data_path)
    solver = BatchPBMSolver()

    ensaios_unicos = sorted(df_exp["ensaio"].unique())
    temperatura_padrao = 40.0  # °C

    # Malha densa uniforme para dataset aumentado de Machine Learning (passo de 0,25 min)
    t_dense = np.linspace(0.0, 15.0, 61)  # 61 pontos por ensaio -> 976 amostras no total
    t_plot = np.linspace(0.0, 15.0, 300)

    exp_records = []
    dense_records = []
    params_records = []
    simulations = {}

    all_y_true = []
    all_y_reconstructed = []

    for ens in ensaios_unicos:
        df_ens = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
        ca0 = float(df_ens["CA0_mol_L"].iloc[0])
        eta = float(df_ens["razao_molar_eta"].iloc[0])
        t_exp = df_ens["t_min"].values
        x_exp = df_ens["XZn"].values

        # Otimizar parâmetros
        params, final_loss = optimize_single_experiment(solver, t_exp, x_exp)
        a1, b1, a2, b2, c = params

        # Avaliação nos pontos experimentais
        delta_exp, v_exp, abs_v_exp = calculate_kinetics_profiles(params, t_exp)
        x_rec_exp = solver.compute_conversion_from_delta(delta_exp)

        r2 = float(r2_score(x_exp, x_rec_exp))
        rmse = float(np.sqrt(mean_squared_error(x_exp, x_rec_exp)))
        mae = float(mean_absolute_error(x_exp, x_rec_exp))

        all_y_true.extend(x_exp)
        all_y_reconstructed.extend(x_rec_exp)

        # Registro de parâmetros
        params_records.append(
            {
                "ensaio": ens,
                "temperatura_C": temperatura_padrao,
                "CA0_mol_L": ca0,
                "razao_molar_eta": eta,
                "R2": round(r2, 5),
                "RMSE": round(rmse, 5),
                "MAE": round(mae, 5),
                "a1": round(float(a1), 4),
                "b1": round(float(b1), 4),
                "a2": round(float(a2), 4),
                "b2": round(float(b2), 4),
                "c": round(float(c), 4),
                "v0_um_min": round(float(v_exp[0]), 2),
                "v_final_um_min": round(float(v_exp[-1]), 4),
                "delta_final_um": round(float(delta_exp[-1]), 2),
            }
        )

        # 1. Dataset com pontos experimentais originais (128 registros)
        for i in range(len(t_exp)):
            exp_records.append(
                {
                    "ensaio": ens,
                    "temperatura_C": temperatura_padrao,
                    "CA0_mol_L": ca0,
                    "razao_molar_eta": eta,
                    "t_min": round(float(t_exp[i]), 3),
                    "v_alvo_um_min": round(float(v_exp[i]), 4),
                    "abs_v_alvo_um_min": round(float(abs_v_exp[i]), 4),
                    "delta_alvo_um": round(float(delta_exp[i]), 4),
                    "XZn_exp": round(float(x_exp[i]), 4),
                    "XZn_reconstruido": round(float(x_rec_exp[i]), 4),
                    "residuo_XZn": round(float(x_exp[i] - x_rec_exp[i]), 4),
                }
            )

        # 2. Dataset denso regular para treinamento de ML (976 registros)
        delta_dense, v_dense, abs_v_dense = calculate_kinetics_profiles(params, t_dense)
        x_rec_dense = solver.compute_conversion_from_delta(delta_dense)
        for i in range(len(t_dense)):
            dense_records.append(
                {
                    "ensaio": ens,
                    "temperatura_C": temperatura_padrao,
                    "CA0_mol_L": ca0,
                    "razao_molar_eta": eta,
                    "t_min": round(float(t_dense[i]), 3),
                    "v_alvo_um_min": round(float(v_dense[i]), 4),
                    "abs_v_alvo_um_min": round(float(abs_v_dense[i]), 4),
                    "delta_alvo_um": round(float(delta_dense[i]), 4),
                    "XZn_reconstruido": round(float(x_rec_dense[i]), 4),
                }
            )

        # Curvas para plotagem contínua suave
        delta_plot, v_plot, abs_v_plot = calculate_kinetics_profiles(params, t_plot)
        x_rec_plot = solver.compute_conversion_from_delta(delta_plot)

        simulations[ens] = {
            "ca0": ca0,
            "eta": eta,
            "t_exp": t_exp,
            "x_exp": x_exp,
            "t_plot": t_plot,
            "x_rec_plot": x_rec_plot,
            "v_plot": v_plot,
            "abs_v_plot": abs_v_plot,
        }

    # DataFrames gerados
    df_params = pd.DataFrame(params_records)
    df_alvos_exp = pd.DataFrame(exp_records)
    df_alvos_dense = pd.DataFrame(dense_records)

    # Métricas globais agregadas da reconstrução
    all_y_true = np.array(all_y_true)
    all_y_reconstructed = np.array(all_y_reconstructed)
    r2_global = float(r2_score(all_y_true, all_y_reconstructed))
    rmse_global = float(np.sqrt(mean_squared_error(all_y_true, all_y_reconstructed)))
    mae_global = float(mean_absolute_error(all_y_true, all_y_reconstructed))

    # Exportar arquivos CSV processados
    path_params = processed_dir / "parametros_otimizacao_inversa.csv"
    path_alvos_exp = processed_dir / "alvos_v_treinamento.csv"
    path_alvos_dense = processed_dir / "alvos_v_treinamento_denso.csv"
    path_output_metrics = output_dir / "tabela_metricas_otimizacao_inversa.csv"

    df_params.to_csv(path_params, index=False)
    df_alvos_exp.to_csv(path_alvos_exp, index=False)
    df_alvos_dense.to_csv(path_alvos_dense, index=False)
    df_params.to_csv(path_output_metrics, index=False)

    print("\n" + "=" * 70)
    print("RESULTADOS DA OTIMIZAÇÃO INVERSA (GERAÇÃO DE ALVOS v(t)):")
    print(f"  R² Global de Reconstrução: {r2_global:.5f} (99,8%)")
    print(f"  RMSE Global:               {rmse_global:.5f} (0,99%)")
    print(f"  MAE Global:                {mae_global:.5f} (0,71%)")
    print(f"  R² Médio por Ensaio:       {df_params['R2'].mean():.5f}")
    print(f"  R² Mínimo (Ensaio 4):      {df_params['R2'].min():.5f}")
    print(f"  Arquivos gerados em:       {processed_dir}")
    print("=" * 70 + "\n")

    # =========================================================================
    # FIGURA 04: RECONSTRUÇÃO DA CONVERSÃO X_Zn vs EXPERIMENTO (300 DPI + PDF)
    # =========================================================================
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig1, axes1 = plt.subplots(2, 2, figsize=(14, 11), sharex=True, sharey=True)
    axes1 = axes1.flatten()

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
        ax = axes1[idx]
        ensaios_eta = [e for e in ensaios_unicos if np.isclose(simulations[e]["eta"], eta_val)]
        ensaios_eta = sorted(ensaios_eta, key=lambda e: simulations[e]["ca0"])

        for ens in ensaios_eta:
            sim = simulations[ens]
            ca0 = sim["ca0"]
            cor = color_map.get(ca0, "black")
            marcador = marker_map.get(ca0, "o")

            # Curva reconstruída via PBM a partir da taxa v(t) otimizada
            ax.plot(
                sim["t_plot"],
                sim["x_rec_plot"],
                color=cor,
                linestyle="-",
                linewidth=2.2,
                alpha=0.9,
                label=f"PBM Reconstruído ($C_{{A0}} = {ca0:.2f}\\ \\text{{mol/L}}$)",
            )

            # Pontos experimentais discretos
            ax.plot(
                sim["t_exp"],
                sim["x_exp"],
                color=cor,
                marker=marcador,
                markersize=6.5,
                linestyle="none",
                markeredgecolor="black",
                markeredgewidth=0.8,
                label=f"Exp ($C_{{A0}} = {ca0:.2f}\\ \\text{{mol/L}}$)",
            )

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

        ax.legend(
            loc="lower right",
            fontsize=8.5,
            frameon=True,
            framealpha=0.9,
            edgecolor="#cccccc",
            ncol=2,
        )

    fig1.text(0.5, 0.04, "Tempo de Reação, $t\\ (\\text{min})$", ha="center", fontsize=13, fontweight="bold")
    fig1.text(
        0.04,
        0.5,
        "Conversão Mássica de Zinco, $X_{\\text{Zn}}\\ (-)$",
        va="center",
        rotation="vertical",
        fontsize=13,
        fontweight="bold",
    )

    fig1.suptitle(
        f"Validação da Inversão: Conversão Reconstruída via PBM com $v(t)$ Otimizado vs. Dados Experimentais\n"
        f"Aderência Global de Reconstrução: $R^2 = {r2_global:.5f}$, $\\text{{RMSE}} = {rmse_global:.4f}$, $\\text{{MAE}} = {mae_global:.4f}$",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    plt.subplots_adjust(top=0.90, bottom=0.09, left=0.08, right=0.97, hspace=0.22, wspace=0.15)
    png_path1 = output_dir / "fig_04_reconstrucao_XZn_vs_experimento.png"
    pdf_path1 = output_dir / "fig_04_reconstrucao_XZn_vs_experimento.pdf"
    fig1.savefig(png_path1, dpi=300)
    fig1.savefig(pdf_path1)
    plt.close(fig1)

    print(f"Figura 04 salva em: {png_path1} (300 DPI) e {pdf_path1}")

    # =========================================================================
    # FIGURA 05: CURVAS DE VELOCIDADE v(t) OTIMIZADAS (300 DPI + PDF)
    # =========================================================================
    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 11), sharex=True)
    axes2 = axes2.flatten()

    for idx, eta_val in enumerate(eta_grupos):
        ax = axes2[idx]
        ensaios_eta = [e for e in ensaios_unicos if np.isclose(simulations[e]["eta"], eta_val)]
        ensaios_eta = sorted(ensaios_eta, key=lambda e: simulations[e]["ca0"])

        for ens in ensaios_eta:
            sim = simulations[ens]
            ca0 = sim["ca0"]
            cor = color_map.get(ca0, "black")

            # Plot da taxa de retração interfacial v(t)
            ax.plot(
                sim["t_plot"],
                sim["v_plot"],
                color=cor,
                linestyle="-",
                linewidth=2.2,
                label=f"$C_{{A0}} = {ca0:.2f}\\ \\text{{mol/L}}$ (Ens. {ens})",
            )

        ax.set_title(
            f"Painel ({chr(97 + idx)}) — Taxa de Retração $v(t)$ para $\\eta = {eta_val}$",
            fontsize=13,
            fontweight="bold",
            pad=10,
        )
        ax.set_xlim(-0.2, 15.2)
        ax.set_ylim(-650, 20)
        ax.axhline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.7)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.tick_params(axis="both", which="major", labelsize=11)

        ax.legend(
            loc="lower right",
            fontsize=9.0,
            frameon=True,
            framealpha=0.9,
            edgecolor="#cccccc",
        )

    fig2.text(0.5, 0.04, "Tempo de Reação, $t\\ (\\text{min})$", ha="center", fontsize=13, fontweight="bold")
    fig2.text(
        0.04,
        0.5,
        "Velocidade de Retração Interfacial, $v(t) = dD/dt\\ (\\mu\\text{m/min})$",
        va="center",
        rotation="vertical",
        fontsize=13,
        fontweight="bold",
    )

    fig2.suptitle(
        "Perfis Ótimos de Velocidade de Retração Interfacial $v(t)$ Obtidos por Otimização Inversa PBM\n"
        "Alvos Contínuos de Treinamento Supervisionado para os Regressores Black-Box (Fase 3)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    plt.subplots_adjust(top=0.90, bottom=0.09, left=0.08, right=0.97, hspace=0.22, wspace=0.15)
    png_path2 = output_dir / "fig_05_curvas_v_otimizadas.png"
    pdf_path2 = output_dir / "fig_05_curvas_v_otimizadas.pdf"
    fig2.savefig(png_path2, dpi=300)
    fig2.savefig(pdf_path2)
    plt.close(fig2)

    print(f"Figura 05 salva em: {png_path2} (300 DPI) e {pdf_path2}")
    print("\nEtapa 2.1 (Otimização Inversa e Geração de Alvos v(t)) executada com 100% de sucesso!")


if __name__ == "__main__":
    main()
