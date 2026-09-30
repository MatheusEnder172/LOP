"""Geração individual dos 16 gráficos comparativos detalhados (Ensaio por Ensaio)
entre:
1. Dados Experimentais (Bortot Coelho, 2017)
2. Modelo Cinético Puro (alpha = 0, sem amortecimento empírico / Balarini, 2009)
3. Modelo Fenomenológico Nominal de Fabrício (alpha = 5500 µm/min)
4. Nova Abordagem Híbrida/Adaptativa (LOP)

Layout 100% despoluído (300 DPI e PDF vetorial):
- As legendas e os cartões de metadados são posicionados EXTERNAMENTE à direita do gráfico.
- Nenhuma curva cinética ou ponto experimental sofre sobreposição por textos ou caixas de legenda.
- Painel Superior: Cinética de Conversão X_Zn(t) (Experimental vs. alpha=0 vs. alpha=5500 vs. LOP).
- Painel Inferior: Resíduos Pontuais (X_pred - X_exp) para os 3 modelos ao longo do tempo com faixa de tolerância de ±2%.
"""

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Adicionar raiz do código ao path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.physics.pbm_batch import BatchPBMSolver


def main() -> None:
    base_dir = project_root.parent
    raw_data_path = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    metadata_path = base_dir / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv"
    params_data_path = base_dir / "Base de dados" / "processed" / "parametros_otimizacao_inversa.csv"

    output_dir = base_dir / "Código" / "outputs" / "etapa_1_3" / "comparacao_fabricio_x_LOP" / "ensaios_individuais"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Carregando bases de dados para os 16 ensaios individuais...")
    df_exp = pd.read_csv(raw_data_path)
    df_meta = pd.read_csv(metadata_path).set_index("ensaio")
    df_params = pd.read_csv(params_data_path).set_index("ensaio")

    solver = BatchPBMSolver()
    ensaios_unicos = sorted(df_exp["ensaio"].unique())
    t_fine = np.linspace(0.0, 15.0, 300)

    regime_labels = {
        0.5: "Regime com Limitação Estequiométrica de Ácido (η = 0,5)",
        1.0: "Regime com Proporção Estequiométrica Nominal (η = 1,0)",
        1.5: "Regime com Leve Excesso de Ácido (η = 1,5)",
        3.1: "Regime com Amplo Excesso de Ácido (η = 3,1)",
    }

    print(f"Iniciando plotagem dos 16 gráficos (com curva alpha=0) em: {output_dir}")

    for ens in ensaios_unicos:
        df_ens = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
        ca0 = float(df_ens["CA0_mol_L"].iloc[0])
        eta = float(df_ens["razao_molar_eta"].iloc[0])
        t_exp = df_ens["t_min"].values
        x_exp = df_ens["XZn"].values

        # Metadados de bancada
        meta_row = df_meta.loc[ens]
        sl = float(meta_row["razao_solido_liquido_g_L"])
        mb0 = float(meta_row["mB0_g"])

        # 1. Simulação Modelo Cinético Puro (alpha = 0, sem amortecimento)
        res_a0_exp = solver.simulate(ca0, eta, t_exp, alpha=0.0)
        res_a0_fine = solver.simulate(ca0, eta, t_fine, alpha=0.0)
        x_a0_exp = res_a0_exp["XZn"]
        x_a0_fine = res_a0_fine["XZn"]

        r2_a0 = float(r2_score(x_exp, x_a0_exp))
        rmse_a0 = float(np.sqrt(mean_squared_error(x_exp, x_a0_exp)))
        mae_a0 = float(mean_absolute_error(x_exp, x_a0_exp))
        err_final_a0 = abs(x_exp[-1] - x_a0_exp[-1])

        # 2. Simulação Modelo Nominal de Bortot Coelho (alpha = 5500)
        res_fab_exp = solver.simulate(ca0, eta, t_exp, alpha=5500.0)
        res_fab_fine = solver.simulate(ca0, eta, t_fine, alpha=5500.0)
        x_fab_exp = res_fab_exp["XZn"]
        x_fab_fine = res_fab_fine["XZn"]

        r2_fab = float(r2_score(x_exp, x_fab_exp))
        rmse_fab = float(np.sqrt(mean_squared_error(x_exp, x_fab_exp)))
        mae_fab = float(mean_absolute_error(x_exp, x_fab_exp))
        err_final_fab = abs(x_exp[-1] - x_fab_exp[-1])

        # 3. Simulação Nova Abordagem Adaptativa (LOP)
        p_row = df_params.loc[ens]
        a1, b1, a2, b2, c = p_row["a1"], p_row["b1"], p_row["a2"], p_row["b2"], p_row["c"]
        delta_exp = (a1 / b1) * (1.0 - np.exp(-b1 * t_exp)) + (a2 / b2) * (1.0 - np.exp(-b2 * t_exp)) + c * t_exp
        delta_fine = (a1 / b1) * (1.0 - np.exp(-b1 * t_fine)) + (a2 / b2) * (1.0 - np.exp(-b2 * t_fine)) + c * t_fine

        x_novo_exp = solver.compute_conversion_from_delta(delta_exp)
        x_novo_fine = solver.compute_conversion_from_delta(delta_fine)

        r2_novo = float(r2_score(x_exp, x_novo_exp))
        rmse_novo = float(np.sqrt(mean_squared_error(x_exp, x_novo_exp)))
        mae_novo = float(mean_absolute_error(x_exp, x_novo_exp))
        err_final_novo = abs(x_exp[-1] - x_novo_exp[-1])

        # Resíduos dos 3 modelos
        res_a0_pts = x_a0_exp - x_exp
        res_fab_pts = x_fab_exp - x_exp
        res_novo_pts = x_novo_exp - x_exp

        # Layout com área de gráfico limpa e margem lateral direita para legendas e card
        fig, (ax_main, ax_res) = plt.subplots(
            2, 1, figsize=(11.6, 7.4), sharex=True, gridspec_kw={"height_ratios": [3.3, 1.2]}
        )

        # --- PAINEL PRINCIPAL: CURVAS CINÉTICAS ---
        # 1. Pontos Experimentais
        ax_main.plot(
            t_exp,
            x_exp,
            color="#1565c0",
            marker="o",
            markersize=7.5,
            linestyle="none",
            markeredgecolor="black",
            markeredgewidth=1.2,
            zorder=7,
            label="Dados Experimentais ($X_{\\text{Zn, exp}}$)",
        )

        # 2. Modelo Cinético Puro (alpha = 0)
        ax_main.plot(
            t_fine,
            x_a0_fine,
            color="#e65100",
            linestyle="-.",
            linewidth=2.0,
            alpha=0.9,
            zorder=4,
            label="Modelo Cinético Puro (α = 0)",
        )

        # 3. Modelo Nominal Fabrício (alpha = 5500)
        ax_main.plot(
            t_fine,
            x_fab_fine,
            color="#c62828",
            linestyle="--",
            linewidth=2.0,
            alpha=0.9,
            zorder=5,
            label="Modelo Nominal Fabrício (α = 5500)",
        )

        # 4. Nova Abordagem Adaptativa (LOP)
        ax_main.plot(
            t_fine,
            x_novo_fine,
            color="#2e7d32",
            linestyle="-",
            linewidth=2.4,
            alpha=0.95,
            zorder=6,
            label="Nova Abordagem Adaptativa (LOP)",
        )

        # Título
        regime_desc = regime_labels.get(round(eta, 1), f"Razão Molar η = {eta:.2f}")
        ax_main.set_title(
            f"Ensaio {ens:02d} — $C_{{A0}} = {ca0:.2f}\\ \\text{{mol/L}}$  |  $\\eta = {eta:.1f}$  |  $S/L = {sl:.1f}\\ \\text{{g/L}}$\n"
            f"{regime_desc}",
            fontsize=12,
            fontweight="bold",
            pad=10,
        )

        ax_main.set_ylabel("Conversão de Zinco, $X_{\\text{Zn}}$ (-)", fontsize=11, fontweight="bold")
        ax_main.set_ylim(-0.03, 1.05)
        ax_main.set_xlim(-0.4, 15.4)
        ax_main.grid(True, linestyle="--", alpha=0.5)
        ax_main.tick_params(axis="both", which="major", labelsize=10)

        # LEGENDA EXTERNA: posicionada fora do gráfico, à direita (bbox_to_anchor)
        ax_main.legend(
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            fontsize=8.8,
            frameon=True,
            framealpha=0.95,
            edgecolor="#b0bec5",
        )

        # CARD EXTERNO DE METADADOS E DESEMPENHO: posicionado à direita abaixo da legenda
        info_card = (
            "Condições Operacionais:\n"
            f" • $m_{{B0}} = {mb0:.1f}\\ \\text{{g}}$ minério | $V = 0,40\\ \\text{{L}}$\n"
            f" • $T = 40^\\circ\\text{{C}}$ | Rotação: $1000\\ \\text{{rpm}}$\n\n"
            "Desempenho dos Modelos:\n"
            " • Cinético Puro (α = 0):\n"
            f"    $R^2 = {r2_a0:.4f}$ | RMSE = {rmse_a0*100:.2f}%\n"
            f"    $X_{{final}} = {x_a0_exp[-1]*100:.1f}\\%$ (Desvio: {err_final_a0*100:.1f}%)\n\n"
            " • Modelo Nominal (α = 5500):\n"
            f"    $R^2 = {r2_fab:.4f}$ | RMSE = {rmse_fab*100:.2f}%\n"
            f"    $X_{{final}} = {x_fab_exp[-1]*100:.1f}\\%$ (Desvio: {err_final_fab*100:.1f}%)\n\n"
            " • Nova Abordagem (LOP):\n"
            f"    $R^2 = {r2_novo:.4f}$ | RMSE = {rmse_novo*100:.2f}%\n"
            f"    $X_{{final}} = {x_novo_exp[-1]*100:.1f}\\%$ (Desvio: {err_final_novo*100:.2f}%)"
        )
        ax_main.text(
            1.02,
            0.64,
            info_card,
            transform=ax_main.transAxes,
            fontsize=8.0,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#cfd8dc", linewidth=1.2),
        )

        # --- PAINEL INFERIOR: RESÍDUOS TEMPORAIS ---
        ax_res.axhline(0, color="black", linestyle="-", linewidth=1.1, zorder=2)
        ax_res.axhspan(-0.02, 0.02, color="#e8f5e9", alpha=0.7, label="Tolerância $\\pm 2\\%$", zorder=1)

        ax_res.plot(
            t_exp,
            res_a0_pts,
            color="#e65100",
            marker="^",
            markersize=5.5,
            linestyle="-.",
            linewidth=1.2,
            zorder=4,
            label=f"Resíduo α=0 (MAE = {mae_a0*100:.2f}%)",
        )
        ax_res.plot(
            t_exp,
            res_fab_pts,
            color="#c62828",
            marker="s",
            markersize=5.5,
            linestyle=":",
            linewidth=1.2,
            zorder=5,
            label=f"Resíduo α=5500 (MAE = {mae_fab*100:.2f}%)",
        )
        ax_res.plot(
            t_exp,
            res_novo_pts,
            color="#2e7d32",
            marker="o",
            markersize=5.5,
            linestyle="-",
            linewidth=1.4,
            zorder=6,
            label=f"Resíduo LOP (MAE = {mae_novo*100:.2f}%)",
        )

        ax_res.set_xlabel("Tempo de Reação, $t$ (min)", fontsize=11, fontweight="bold")
        ax_res.set_ylabel("Resíduo ($X_{\\text{pred}} - X_{\\text{exp}}$)", fontsize=9.5, fontweight="bold")
        ax_res.set_xlim(-0.4, 15.4)
        all_res = np.concatenate([res_a0_pts, res_fab_pts, res_novo_pts])
        max_res = max(0.06, float(np.max(np.abs(all_res))) * 1.25)
        ax_res.set_ylim(-max_res, max_res)
        ax_res.grid(True, linestyle="--", alpha=0.5)
        ax_res.tick_params(axis="both", which="major", labelsize=9.5)

        # Legenda dos resíduos também externa à direita
        ax_res.legend(
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            fontsize=8.0,
            frameon=True,
            framealpha=0.95,
            edgecolor="#b0bec5",
        )

        # Salvar com bbox_inches='tight' para garantir que os elementos externos fiquem perfeitamente enquadrados
        eta_str = f"{eta:.1f}".replace(".", "_")
        ca0_str = f"{ca0:.2f}".replace(".", "_")
        base_name = f"fig_comp_ensaio_{ens:02d}_eta_{eta_str}_ca0_{ca0_str}"

        png_path = output_dir / f"{base_name}.png"
        pdf_path = output_dir / f"{base_name}.pdf"

        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
        plt.close(fig)

    print(f"Sucesso! Todos os 16 gráficos (com curva alpha=0) foram regerados em:\n{output_dir}")


if __name__ == "__main__":
    main()
