"""
Etapa 0.3: Transformação da Distribuição Granulométrica RRB (Base Mássica -> Base Numérica via Divisão por D³)
e Avaliação do Impacto no Modelo White-Box Puro (Sem Parâmetro α) sem Alterar a Equação de Conversão.

Disciplina: Laboratório de Operações e Processos (LOP - DEQ/UFMG)
Referências:
- Bortot Coelho, F. E. (2017). Dissertação de Mestrado, PPGEM/UFMG, Equações (3.45), (3.47), (3.48) e (3.49), p. 73-74.
- Herbst, J. A. (1979). Rate Processes of Extractive Metallurgy. Plenum Press.

Objetivo:
1. Converter a função densidade de probabilidade de Rosin-Rammler-Bennet (originalmente ajustada em base mássica f_m(D)
   na Etapa 0.2) para a função densidade populacional em base numérica f_n(D), dividindo-a por D³ e normalizando
   no domínio [D_min, D_max]:
       f_n(D) = [ D⁻³ · f_m(D) ] / [ ∫ D⁻³ · f_m(D) dD ]
2. Manter a equação de conversão do Balanço Populacional (BatchPBMSolver) 100% inalterada:
       X_Zn(δ) = 1 - [ ∫_δ^D_max (D - δ)³ · f₀(D) dD ] / [ ∫_D_min^D_max D³ · f₀(D) dD ]
3. Comparar gráfica e estatisticamente:
   - As duas distribuições granulométricas ANTES de entrarem na equação de conversão (Antiga: f₀ = f_m da Etapa 0.2
     vs. Nova: f₀ = f_n proporcional a f_m / D³);
   - O peso volumétrico efetivo [D³ · f₀(D)] DENTRO da equação de conversão (mostrando por que o Novo recupera
     exatamente a curva da Etapa 0.2 após multiplicar por D³, enquanto o Antigo distorce a média para 146,9 µm);
   - A curva característica de conversão X_Zn(δ) em função do deslocamento diametral acumulado δ;
   - A simulação White-Box Puro (SEM considerar o parâmetro empírico α, isto é, α = 0) nos 16 ensaios de bancada.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Adicionar diretório raiz de código ao sys.path
PROJECT_CODE_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_CODE_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_CODE_ROOT))

from src.physics.granulometry import RosinRammlerBennet
from src.physics.pbm_batch import BatchPBMSolver


class RosinRammlerNumeroD3(RosinRammlerBennet):
    """Subclasse de RosinRammlerBennet que converte a densidade mássica f_m(D)
    para densidade numérica f_n(D) dividindo por D³ (Equação 3.48 de Bortot Coelho, 2017),
    mantendo intacta toda a interface com o BatchPBMSolver e sua equação de conversão.
    """

    def mass_probability_density(self, d: np.ndarray | float) -> np.ndarray | float:
        """Retorna a densidade original em base mássica f_m(D) = dF/dD."""
        return super().probability_density(d)

    def number_density_unnormalized(self, d: np.ndarray | float) -> np.ndarray | float:
        """Retorna a densidade numérica não-normalizada g_n(D) = f_m(D) / D³."""
        fm = super().probability_density(d)
        d_arr = np.asarray(d, dtype=np.float64)
        d_pos = np.maximum(d_arr, 1e-12)
        gn = fm / (d_pos ** 3)
        if isinstance(gn, np.ndarray):
            gn[d_arr <= 0.0] = 0.0
            return gn
        return float(gn) if d_arr > 0.0 else 0.0

    def generate_mesh(
        self,
        d_min: float = 0.01,
        d_max: float = 297.0,
        n_points: int = 5000,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """Gera a malha de diâmetros e entrega f0_mesh = f_n(D) (dividida por D³ e normalizada)
        para que o BatchPBMSolver aplique exatamente a mesma equação de conversão:
            X_Zn(δ) = 1 - ∫ (D - δ)³ f0(D) dD / ∫ D³ f0(D) dD
        """
        d_mesh = np.linspace(d_min, d_max, n_points)
        fm_mesh = super().probability_density(d_mesh)
        fn_unnorm = fm_mesh / (d_mesh ** 3)
        norm_factor = float(trapezoid(fn_unnorm, d_mesh))
        f0_mesh = fn_unnorm / norm_factor
        m3_numerical = float(trapezoid(f0_mesh * (d_mesh ** 3), d_mesh))
        return d_mesh, f0_mesh, m3_numerical


def configurar_estilo_grafico() -> None:
    """Padroniza estilo visual científico em 300 DPI."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10.5,
        "axes.labelsize": 11.2,
        "axes.titlesize": 11.5,
        "xtick.labelsize": 9.8,
        "ytick.labelsize": 9.8,
        "legend.fontsize": 9.0,
        "figure.titlesize": 13.5,
        "axes.grid": True,
        "grid.alpha": 0.45,
        "grid.linestyle": "--",
    })


def gerar_figura_03a_distribuicoes(
    df_gran: pd.DataFrame,
    solver_antigo: BatchPBMSolver,
    solver_novo: BatchPBMSolver,
    output_dir: Path,
) -> pd.DataFrame:
    """Gera a Figura 03a (Painel 2x2) comparando:
    (a) A densidade f₀(D) ANTES de entrar na equação de conversão (Antiga f_m da Etapa 0.2 vs. Nova f_n = f_m / D³);
    (b) O peso [D³ · f₀(D)] DENTRO da equação de conversão (explicando por que o Novo recupera a curva da Etapa 0.2);
    (c) A massa acumulada integrada pelo PBM vs. dados experimentais da Tabela 5.4;
    (d) A resposta da equação de conversão X_Zn(δ) ao encolhimento δ.
    """
    rrb_base = RosinRammlerBennet()
    d_min, d_max = 0.01, 297.0
    d_grid = np.linspace(0.5, d_max, 2000)
    d_log = np.geomspace(0.1, d_max, 1500)

    # 1. Densidades f_m(D) e f_n(D)
    fm_grid = rrb_base.probability_density(d_grid)
    fm_log = rrb_base.probability_density(d_log)
    fn_unnorm_log = fm_log / (d_log ** 3)
    norm_fn = float(trapezoid(fn_unnorm_log, d_log))
    fn_log = fn_unnorm_log / norm_fn

    # 2. Distribuição de massa efetiva vista pela integral de conversão D³ * f0(D)
    peso_vol_antigo = (d_grid ** 3) * fm_grid
    norm_vol_antigo = float(trapezoid(peso_vol_antigo, d_grid))
    dens_massa_efetiva_antiga = peso_vol_antigo / norm_vol_antigo

    norm_vol_novo = float(trapezoid(fm_grid, d_grid))
    dens_massa_efetiva_nova = fm_grid / norm_vol_novo

    d_medio_efetivo_antigo = float(trapezoid(d_grid * dens_massa_efetiva_antiga, d_grid))
    d_medio_efetivo_novo = float(trapezoid(d_grid * dens_massa_efetiva_nova, d_grid))

    # 3. Curva Acumulada Passante de Massa Efetiva no PBM vs Dados Experimentais Tabela 5.4
    cum_massa_antiga = np.zeros_like(d_grid)
    cum_massa_nova = np.zeros_like(d_grid)
    for i in range(1, len(d_grid)):
        cum_massa_antiga[i] = trapezoid(dens_massa_efetiva_antiga[: i + 1], d_grid[: i + 1])
        cum_massa_nova[i] = trapezoid(dens_massa_efetiva_nova[: i + 1], d_grid[: i + 1])

    # 4. Curva de Conversão X_Zn(δ) vs Deslocamento δ
    delta_vec = np.linspace(0.0, d_max, 600)
    x_antigo_vec = solver_antigo.compute_conversion_from_delta(delta_vec)
    x_novo_vec = solver_novo.compute_conversion_from_delta(delta_vec)

    delta_50_antigo = float(np.interp(0.50, x_antigo_vec, delta_vec))
    delta_50_novo = float(np.interp(0.50, x_novo_vec, delta_vec))
    delta_80_antigo = float(np.interp(0.80, x_antigo_vec, delta_vec))
    delta_80_novo = float(np.interp(0.80, x_novo_vec, delta_vec))

    fig, axes = plt.subplots(2, 2, figsize=(15.5, 11.8))

    # -------------------------------------------------------------------------
    # Painel (a): Entrada f₀(D) ANTES da Equação de Conversão
    # -------------------------------------------------------------------------
    ax_a = axes[0, 0]
    ax_a.plot(
        d_log,
        fm_log,
        color="#1f77b4",
        linewidth=2.3,
        label="RRB Antiga (Etapa 0.2): f₀(D) = f_m(D) [Base Mássica]",
    )
    ax_a.plot(
        d_log,
        fn_log,
        color="#d62728",
        linewidth=2.3,
        linestyle="-",
        label="RRB Nova (Etapa 0.3): f₀(D) = f_n(D) ∝ f_m(D) / D³ [Base Numérica]",
    )
    ax_a.set_xscale("log")
    ax_a.set_yscale("log")
    ax_a.set_xlim(0.1, 300.0)
    ax_a.set_ylim(1e-9, 1e2)
    ax_a.set_title("(a) Entrada f₀(D) ANTES da Equação de Conversão (Escala Log-Log)", fontweight="bold")
    ax_a.set_xlabel("Diâmetro de Partícula, D (µm) [Escala Log]", fontweight="bold")
    ax_a.set_ylabel("Densidade de Entrada, f₀(D) (µm⁻¹) [Escala Log]", fontweight="bold")
    ax_a.annotate(
        "Ao dividir a RRB da Etapa 0.2 por D³,\na curva vermelha f_n(D) concentra-se\nnas partículas finas (< 10 µm)\ncom inclinação D^(m−4) ≈ D^(−2,98)",
        xy=(1.0, fn_log[np.argmin(np.abs(d_log - 1.0))]),
        xytext=(3.2, 1e-2),
        arrowprops=dict(facecolor="#b71c1c", shrink=0.08, width=1.2, headwidth=5),
        fontsize=8.9,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#ffebee", edgecolor="#ef9a9a"),
    )
    ax_a.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=8.5)

    # -------------------------------------------------------------------------
    # Painel (b): Peso Efetivo [D³ · f₀(D)] DENTRO da Equação de Conversão
    # -------------------------------------------------------------------------
    ax_b = axes[0, 1]
    ax_b.plot(
        d_grid,
        dens_massa_efetiva_antiga,
        color="#1f77b4",
        linestyle="--",
        linewidth=2.2,
        label=f"No PBM Antigo [D³ · f_m(D)]: Distorcida (Média = {d_medio_efetivo_antigo:.1f} µm)",
    )
    ax_b.fill_between(d_grid, 0, dens_massa_efetiva_antiga, color="#1f77b4", alpha=0.14)

    ax_b.plot(
        d_grid,
        dens_massa_efetiva_nova,
        color="#2e7d32",
        linestyle="-",
        linewidth=2.4,
        label=f"No PBM Novo [D³ · (f_m/D³) = f_m(D)]: Recupera Etapa 0.2 (Média = {d_medio_efetivo_novo:.1f} µm)",
    )
    ax_b.fill_between(d_grid, 0, dens_massa_efetiva_nova, color="#2e7d32", alpha=0.18)

    ax_b.axvline(d_medio_efetivo_antigo, color="#1f77b4", linestyle=":", linewidth=1.5)
    ax_b.axvline(d_medio_efetivo_novo, color="#2e7d32", linestyle=":", linewidth=1.5)
    ax_b.set_xlim(-5, 300)
    ax_b.set_ylim(0, max(np.max(dens_massa_efetiva_nova), np.max(dens_massa_efetiva_antiga)) * 1.15)
    ax_b.set_title("(b) Peso Efetivo [D³ · f₀(D)] DENTRO da Equação de Conversão", fontweight="bold")
    ax_b.set_xlabel("Diâmetro de Partícula, D (µm)", fontweight="bold")
    ax_b.set_ylabel("Fração Mássica Efetiva no Integrando (µm⁻¹)", fontweight="bold")
    ax_b.annotate(
        "Por que o Novo coincide com a Etapa 0.2?\nPorque D³ · [f_m(D)/D³] = f_m(D)!\nJá o Antigo multiplicava f_m por D³ de novo\n(D³·f_m), empurrando a média p/ 146,9 µm.",
        xy=(118.0, dens_massa_efetiva_antiga[np.argmin(np.abs(d_grid - 118.0))]),
        xytext=(120.0, 0.0110),
        arrowprops=dict(facecolor="#1565c0", shrink=0.08, width=1.2, headwidth=5),
        fontsize=8.8,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#e3f2fd", edgecolor="#90caf9"),
    )
    ax_b.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=8.3)

    # -------------------------------------------------------------------------
    # Painel (c): Fração Acumulada de Massa Efetiva no PBM vs Dados Experimentais
    # -------------------------------------------------------------------------
    ax_c = axes[1, 0]
    df_pen = df_gran[df_gran["metodo"] == "Peneiramento a umido"]
    df_las = df_gran[df_gran["metodo"] == "Difracao a Laser"]

    ax_c.scatter(
        df_pen["peneira_ou_diametro_um"],
        df_pen["passante_acumulada_pct"] / 100.0,
        color="#0d47a1",
        marker="D",
        s=42,
        zorder=5,
        label="Exp: Peneiramento a Úmido (Tab. 5.4)",
    )
    ax_c.scatter(
        df_las["peneira_ou_diametro_um"],
        df_las["passante_acumulada_pct"] / 100.0,
        color="#ff8f00",
        marker="o",
        s=32,
        zorder=4,
        label="Exp: Difração a Laser (Tab. 5.4)",
    )
    ax_c.plot(
        d_grid,
        cum_massa_antiga,
        color="#1f77b4",
        linestyle="--",
        linewidth=2.2,
        label="Massa Acumulada no PBM Antigo (∫ D³·f_m dD — Distorcida)",
    )
    ax_c.plot(
        d_grid,
        cum_massa_nova,
        color="#2e7d32",
        linestyle="-",
        linewidth=2.5,
        label="Massa Acumulada no PBM Novo (∫ D³·(f_m/D³) dD = Curva da Etapa 0.2)",
    )
    ax_c.set_xlim(-5, 300)
    ax_c.set_ylim(-0.03, 1.05)
    ax_c.set_title("(c) Massa Acumulada Vista pelo PBM vs. Dados da Tabela 5.4", fontweight="bold")
    ax_c.set_xlabel("Diâmetro de Partícula, D (µm)", fontweight="bold")
    ax_c.set_ylabel("Fração Mássica Acumulada Passante, F(D) (-)", fontweight="bold")
    ax_c.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=8.4)

    # -------------------------------------------------------------------------
    # Painel (d): Mapeamento Monótono de Conversão X_Zn(δ) vs Encolhimento δ
    # -------------------------------------------------------------------------
    ax_d = axes[1, 1]
    ax_d.plot(
        delta_vec,
        x_antigo_vec,
        color="#1f77b4",
        linestyle="--",
        linewidth=2.3,
        label=f"PBM Antigo (sem ÷ D³): δ₅₀% = {delta_50_antigo:.2f} µm | δ₈₀% = {delta_80_antigo:.1f} µm",
    )
    ax_d.plot(
        delta_vec,
        x_novo_vec,
        color="#d62728",
        linestyle="-",
        linewidth=2.5,
        label=f"PBM Novo (com ÷ D³): δ₅₀% = {delta_50_novo:.2f} µm | δ₈₀% = {delta_80_novo:.1f} µm",
    )
    ax_d.axhline(0.50, color="gray", linestyle=":", linewidth=1.2)
    ax_d.plot([delta_50_novo, delta_50_antigo], [0.50, 0.50], color="#444444", marker="o", markersize=6)
    ax_d.annotate(
        f"Para atingir X_Zn = 50%:\n• Novo (÷ D³): δ = {delta_50_novo:.2f} µm\n• Antigo: δ = {delta_50_antigo:.2f} µm",
        xy=(delta_50_novo, 0.50),
        xytext=(42.0, 0.35),
        arrowprops=dict(facecolor="#333333", shrink=0.06, width=1.2, headwidth=5),
        fontsize=9.2,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f8f9fa", edgecolor="#bdbdbd"),
    )
    ax_d.set_xlim(-3, 200)
    ax_d.set_ylim(-0.02, 1.05)
    ax_d.set_title("(d) Resposta da Equação de Conversão X_Zn(δ) ao Encolhimento δ", fontweight="bold")
    ax_d.set_xlabel("Deslocamento Diametral Acumulado, δ(t) (µm)", fontweight="bold")
    ax_d.set_ylabel("Conversão Fracionária de Zinco, X_Zn(δ) (-)", fontweight="bold")
    ax_d.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=8.8)

    fig.suptitle(
        "Etapa 0.3 — Transformação da Distribuição RRB (Divisão por D³) Antes da Equação de Conversão\n"
        "Explicação de Como D³ · [f_m(D) / D³] Cancela o Excesso Volumétrico e Recupera a Granulometria Real da Etapa 0.2",
        fontweight="bold",
        y=0.99,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    png_path = output_dir / "fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.png"
    pdf_path = output_dir / "fig_03a_comparacao_distribuicoes_rrb_massa_vs_numero.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    df_delta = pd.DataFrame({
        "delta_um": delta_vec,
        "XZn_antigo_sem_div_D3": np.round(x_antigo_vec, 6),
        "XZn_novo_com_div_D3": np.round(x_novo_vec, 6),
        "diferenca_XZn": np.round(x_novo_vec - x_antigo_vec, 6),
    })
    df_delta.to_csv(output_dir / "tabela_comparativa_distribuicoes_delta_XZn.csv", index=False)
    print(f"[OK] Figura 03a salva em: {png_path}")
    return df_delta


def simular_e_comparar_whitebox_sem_alpha(
    df_exp: pd.DataFrame,
    solver_antigo: BatchPBMSolver,
    solver_novo: BatchPBMSolver,
    output_dir: Path,
) -> pd.DataFrame:
    """Executa o modelo White-Box Puro SEM considerar o parâmetro α (α = 0)
    com a distribuição antiga (f_m direto) vs. nova (f_n ∝ f_m / D³) nos 16 ensaios
    e gera as Figuras 03b, 03c e 03d.
    """
    ensaios_unicos = sorted(df_exp["ensaio"].unique())
    t_fine = np.linspace(0.0, 15.0, 300)

    records = []
    sims = {}

    y_true_all = []
    y_old_0_all, y_new_0_all = [], []

    for ens in ensaios_unicos:
        sub = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
        ca0 = float(sub["CA0_mol_L"].iloc[0])
        eta = float(sub["razao_molar_eta"].iloc[0])
        t_exp = sub["t_min"].values
        x_exp = sub["XZn"].values

        # Simulação White-Box SEM considerar α (α = 0.0)
        old_0_pts = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=0.0)
        old_0_fine = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_fine, alpha=0.0)

        new_0_pts = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=0.0)
        new_0_fine = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_fine, alpha=0.0)

        r2_old_0 = float(r2_score(x_exp, old_0_pts["XZn"]))
        rmse_old_0 = float(np.sqrt(mean_squared_error(x_exp, old_0_pts["XZn"])))
        mae_old_0 = float(mean_absolute_error(x_exp, old_0_pts["XZn"]))

        r2_new_0 = float(r2_score(x_exp, new_0_pts["XZn"]))
        rmse_new_0 = float(np.sqrt(mean_squared_error(x_exp, new_0_pts["XZn"])))
        mae_new_0 = float(mean_absolute_error(x_exp, new_0_pts["XZn"]))

        records.append({
            "ensaio": ens,
            "razao_molar_eta": eta,
            "CA0_mol_L": ca0,
            "R2_antigo_sem_alpha": round(r2_old_0, 4),
            "R2_novo_D3_sem_alpha": round(r2_new_0, 4),
            "ganho_R2_sem_alpha": round(r2_new_0 - r2_old_0, 4),
            "RMSE_antigo_sem_alpha": round(rmse_old_0, 4),
            "RMSE_novo_D3_sem_alpha": round(rmse_new_0, 4),
            "MAE_antigo_sem_alpha": round(mae_old_0, 4),
            "MAE_novo_D3_sem_alpha": round(mae_new_0, 4),
            "X_exp_final": round(float(x_exp[-1]), 4),
            "X_antigo_sem_alpha_final": round(float(old_0_pts["XZn"][-1]), 4),
            "X_novo_sem_alpha_final": round(float(new_0_pts["XZn"][-1]), 4),
        })

        sims[ens] = {
            "ca0": ca0,
            "eta": eta,
            "t_exp": t_exp,
            "x_exp": x_exp,
            "t_fine": t_fine,
            "old_0_fine": old_0_fine["XZn"],
            "new_0_fine": new_0_fine["XZn"],
            "r2_old_0": r2_old_0,
            "r2_new_0": r2_new_0,
            "rmse_old_0": rmse_old_0,
            "rmse_new_0": rmse_new_0,
        }

        y_true_all.extend(x_exp)
        y_old_0_all.extend(old_0_pts["XZn"])
        y_new_0_all.extend(new_0_pts["XZn"])

    df_comp = pd.DataFrame(records)
    csv_path = output_dir / "tabela_comparativa_whitebox_antigo_vs_novo_d3.csv"
    df_comp.to_csv(csv_path, index=False)

    y_true_arr = np.array(y_true_all)
    y_old_0_arr = np.array(y_old_0_all)
    y_new_0_arr = np.array(y_new_0_all)

    r2_glob_old_0 = float(r2_score(y_true_arr, y_old_0_arr))
    rmse_glob_old_0 = float(np.sqrt(mean_squared_error(y_true_arr, y_old_0_arr)))
    mae_glob_old_0 = float(mean_absolute_error(y_true_arr, y_old_0_arr))

    r2_glob_new_0 = float(r2_score(y_true_arr, y_new_0_arr))
    rmse_glob_new_0 = float(np.sqrt(mean_squared_error(y_true_arr, y_new_0_arr)))
    mae_glob_new_0 = float(mean_absolute_error(y_true_arr, y_new_0_arr))

    # =========================================================================
    # FIGURA 03b: PAINEL 2x2 POR RAZÃO MOLAR η (WHITE-BOX SEM α: ANTIGO vs NOVO ÷ D³)
    # =========================================================================
    fig_b, axes_b = plt.subplots(2, 2, figsize=(15, 11.5), sharex=True, sharey=True)
    axes_b = axes_b.flatten()
    eta_grupos = [0.5, 1.0, 1.5, 3.1]
    color_map = {
        0.10: "#1f77b4",
        0.50: "#2ca02c",
        1.00: "#ff7f0e",
        1.50: "#d62728",
    }
    marker_map = {0.10: "o", 0.50: "s", 1.00: "^", 1.50: "D"}

    for idx, eta_val in enumerate(eta_grupos):
        ax = axes_b[idx]
        ensaios_eta = sorted(
            [e for e in ensaios_unicos if np.isclose(sims[e]["eta"], eta_val)],
            key=lambda e: sims[e]["ca0"],
        )
        for ens in ensaios_eta:
            s = sims[ens]
            ca0 = s["ca0"]
            cor = color_map[ca0]
            mk = marker_map[ca0]

            # Curva Antiga sem α (Tracejada)
            ax.plot(
                s["t_fine"],
                s["old_0_fine"],
                color=cor,
                linestyle="--",
                linewidth=1.7,
                alpha=0.65,
                label=f"Antigo (sem ÷D³): C_A0={ca0:.2f} M",
            )
            # Curva Nova com RRB ÷ D³ sem α (Sólida)
            ax.plot(
                s["t_fine"],
                s["new_0_fine"],
                color=cor,
                linestyle="-",
                linewidth=2.4,
                alpha=0.95,
                label=f"Novo (RRB ÷ D³): C_A0={ca0:.2f} M",
            )
            # Dados Experimentais
            ax.plot(
                s["t_exp"],
                s["x_exp"],
                color=cor,
                marker=mk,
                markersize=6.5,
                linestyle="none",
                markeredgecolor="black",
                markeredgewidth=0.9,
                zorder=5,
            )

        ax.set_title(f"Painel ({chr(97 + idx)}) — Razão Molar η = {eta_val} (Sem α)", fontweight="bold")
        ax.set_xlim(-0.3, 15.5)
        ax.set_ylim(-0.02, 1.06)
        if eta_val == 0.5:
            ax.axhline(0.50, color="black", linestyle=":", linewidth=1.2)
        else:
            ax.axhline(1.00, color="gray", linestyle=":", linewidth=1.0)

        ax.legend(loc="lower right", fontsize=7.9, ncol=2, frameon=True, facecolor="white", edgecolor="#cccccc")

    fig_b.text(0.5, 0.03, "Tempo de Reação, t (min)", ha="center", fontsize=12.5, fontweight="bold")
    fig_b.text(
        0.03,
        0.5,
        "Conversão Mássica de Zinco, X_Zn (-)",
        va="center",
        rotation="vertical",
        fontsize=12.5,
        fontweight="bold",
    )
    fig_b.suptitle(
        "Simulação White-Box Puro (Sem Parâmetro α): Distribuição RRB Antiga vs. Nova (Dividida por D³)\n"
        f"Antigo (sem ÷ D³): R² Global = {r2_glob_old_0:.4f} (RMSE = {rmse_glob_old_0*100:.2f}%)  |  "
        f"Novo (RRB ÷ D³): R² Global = {r2_glob_new_0:.4f} (RMSE = {rmse_glob_new_0*100:.2f}%)",
        fontweight="bold",
        y=0.98,
    )
    plt.subplots_adjust(top=0.90, bottom=0.08, left=0.07, right=0.97, hspace=0.20, wspace=0.12)

    png_b = output_dir / "fig_03b_whitebox_painel_eta_antigo_vs_novo.png"
    pdf_b = output_dir / "fig_03b_whitebox_painel_eta_antigo_vs_novo.pdf"
    fig_b.savefig(png_b, dpi=300, bbox_inches="tight")
    fig_b.savefig(pdf_b, bbox_inches="tight")
    plt.close(fig_b)
    print(f"[OK] Figura 03b (sem α) salva em: {png_b}")

    # =========================================================================
    # FIGURA 03c: PAINEL 4x4 COMPLETO DOS 16 ENSAIOS INDIVIDUAIS (SEM α)
    # =========================================================================
    fig_c, axes_c = plt.subplots(4, 4, figsize=(18, 15), sharex=True, sharey=True)
    axes_c = axes_c.flatten()

    for idx, ens in enumerate(ensaios_unicos):
        ax = axes_c[idx]
        s = sims[ens]
        # Experimental
        ax.plot(
            s["t_exp"],
            s["x_exp"],
            color="black",
            marker="o",
            markersize=5.8,
            linestyle="none",
            zorder=6,
            label="Dados Experimentais" if idx == 0 else "",
        )
        # White-Box Antigo sem α
        ax.plot(
            s["t_fine"],
            s["old_0_fine"],
            color="#1f77b4",
            linestyle="--",
            linewidth=2.0,
            zorder=4,
            label="White-Box Antigo (Sem α, RRB sem ÷ D³)" if idx == 0 else "",
        )
        # White-Box Novo sem α (RRB ÷ D³)
        ax.plot(
            s["t_fine"],
            s["new_0_fine"],
            color="#d62728",
            linestyle="-",
            linewidth=2.4,
            zorder=5,
            label="White-Box Novo (Sem α, RRB ÷ D³)" if idx == 0 else "",
        )

        ax.set_title(
            f"Ensaio {ens:02d} (C_A0={s['ca0']:.2f} M, η={s['eta']:.1f})\n"
            f"R²: {s['r2_old_0']:.3f} → {s['r2_new_0']:.3f} | RMSE: {s['rmse_old_0']*100:.1f}% → {s['rmse_new_0']*100:.1f}%",
            fontsize=9.2,
            fontweight="bold",
        )
        ax.set_xlim(-0.4, 15.5)
        ax.set_ylim(-0.03, 1.06)

    handles, labels = axes_c[0].get_legend_handles_labels()
    fig_c.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.945),
        ncol=3,
        fontsize=11.0,
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
    )
    fig_c.text(0.5, 0.02, "Tempo de Reação, t (min)", ha="center", fontsize=13, fontweight="bold")
    fig_c.text(
        0.02,
        0.5,
        "Conversão Mássica de Zinco, X_Zn (-)",
        va="center",
        rotation="vertical",
        fontsize=13,
        fontweight="bold",
    )
    fig_c.suptitle(
        "Etapa 0.3 — Comparativo White-Box Puro (Sem Parâmetro α) nos 16 Ensaios: RRB Antiga vs. RRB Nova (÷ D³)",
        fontsize=14.2,
        fontweight="bold",
        y=0.98,
    )
    plt.subplots_adjust(top=0.89, bottom=0.06, left=0.06, right=0.98, hspace=0.35, wspace=0.14)

    png_c = output_dir / "fig_03c_whitebox_16_ensaios_grid_4x4.png"
    pdf_c = output_dir / "fig_03c_whitebox_16_ensaios_grid_4x4.pdf"
    fig_c.savefig(png_c, dpi=300, bbox_inches="tight")
    fig_c.savefig(pdf_c, bbox_inches="tight")
    plt.close(fig_c)
    print(f"[OK] Figura 03c (sem α) salva em: {png_c}")

    # =========================================================================
    # FIGURA 03d: MÉTRICAS R² / RMSE POR ENSAIO E PARIDADE 1:1 (WHITE-BOX SEM α)
    # =========================================================================
    fig_d, axes_d = plt.subplots(2, 2, figsize=(15.5, 11.5))

    x_idx = np.arange(len(ensaios_unicos))
    bw = 0.38

    # (a) R² por Ensaio (Sem α)
    ax_da = axes_d[0, 0]
    ax_da.bar(
        x_idx - bw / 2,
        df_comp["R2_antigo_sem_alpha"],
        width=bw,
        color="#90a4ae",
        edgecolor="#37474f",
        label=f"Antigo (sem ÷D³) — R² Global = {r2_glob_old_0:.4f}",
    )
    ax_da.bar(
        x_idx + bw / 2,
        df_comp["R2_novo_D3_sem_alpha"],
        width=bw,
        color="#d62728",
        edgecolor="#8e0000",
        label=f"Novo (RRB ÷ D³) — R² Global = {r2_glob_new_0:.4f}",
    )
    ax_da.set_xticks(x_idx)
    ax_da.set_xticklabels([f"E{e}" for e in ensaios_unicos], fontweight="bold", fontsize=9)
    ax_da.set_ylim(0.50, 1.04)
    ax_da.set_title("(a) Coeficiente R² por Ensaio no White-Box Puro (Sem α)", fontweight="bold")
    ax_da.set_xlabel("Ensaio Experimental", fontweight="bold")
    ax_da.set_ylabel("Coeficiente de Determinação, R² (-)", fontweight="bold")
    ax_da.legend(loc="lower right", frameon=True, facecolor="white")

    # (b) RMSE por Ensaio (Sem α)
    ax_db = axes_d[0, 1]
    ax_db.bar(
        x_idx - bw / 2,
        df_comp["RMSE_antigo_sem_alpha"] * 100.0,
        width=bw,
        color="#90a4ae",
        edgecolor="#37474f",
        label=f"Antigo (sem ÷D³) — RMSE Global = {rmse_glob_old_0*100:.2f}%",
    )
    ax_db.bar(
        x_idx + bw / 2,
        df_comp["RMSE_novo_D3_sem_alpha"] * 100.0,
        width=bw,
        color="#2e7d32",
        edgecolor="#1b5e20",
        label=f"Novo (RRB ÷ D³) — RMSE Global = {rmse_glob_new_0*100:.2f}%",
    )
    ax_db.set_xticks(x_idx)
    ax_db.set_xticklabels([f"E{e}" for e in ensaios_unicos], fontweight="bold", fontsize=9)
    ax_db.set_title("(b) Erro Quadrático Médio (RMSE %) por Ensaio no White-Box Puro (Sem α)", fontweight="bold")
    ax_db.set_xlabel("Ensaio Experimental", fontweight="bold")
    ax_db.set_ylabel("RMSE de Conversão (%)", fontweight="bold")
    ax_db.legend(loc="upper right", frameon=True, facecolor="white")

    # (c) Paridade 1:1 Antigo vs Novo (Sem α)
    ax_dc = axes_d[1, 0]
    ax_dc.scatter(
        y_true_arr,
        y_old_0_arr,
        color="#1f77b4",
        alpha=0.55,
        s=42,
        marker="s",
        label=f"White-Box Antigo Sem α (R²={r2_glob_old_0:.4f}, RMSE={rmse_glob_old_0*100:.2f}%)",
    )
    ax_dc.scatter(
        y_true_arr,
        y_new_0_arr,
        color="#d62728",
        alpha=0.80,
        s=48,
        marker="o",
        edgecolors="black",
        linewidths=0.5,
        label=f"White-Box Novo ÷ D³ Sem α (R²={r2_glob_new_0:.4f}, RMSE={rmse_glob_new_0*100:.2f}%)",
    )
    ax_dc.plot([-0.05, 1.08], [-0.05, 1.08], "k--", linewidth=1.5, label="Bissetriz Ideal 1:1")
    ax_dc.plot([-0.05, 1.08], [0.0, 1.13], color="gray", linestyle=":", linewidth=1.0, label="Faixa ±5%")
    ax_dc.plot([-0.05, 1.08], [-0.10, 1.03], color="gray", linestyle=":", linewidth=1.0)
    ax_dc.set_xlim(-0.04, 1.06)
    ax_dc.set_ylim(-0.04, 1.06)
    ax_dc.set_title("(c) Diagrama de Paridade 1:1 — White-Box Puro (Sem α)", fontweight="bold")
    ax_dc.set_xlabel("Conversão Experimental, X_Zn,exp (-)", fontweight="bold")
    ax_dc.set_ylabel("Conversão Predita pelo White-Box (Sem α), X_Zn,pred (-)", fontweight="bold")
    ax_dc.legend(loc="upper left", frameon=True, facecolor="white")

    # (d) Resíduos (X_exp - X_pred) vs Conversão Experimental (Sem α)
    ax_dd = axes_d[1, 1]
    res_old = (y_true_arr - y_old_0_arr) * 100.0
    res_new = (y_true_arr - y_new_0_arr) * 100.0
    ax_dd.scatter(
        y_true_arr,
        res_old,
        color="#1f77b4",
        alpha=0.55,
        s=40,
        marker="s",
        label=f"Resíduos Antigo Sem α (MAE = {mae_glob_old_0*100:.2f}%)",
    )
    ax_dd.scatter(
        y_true_arr,
        res_new,
        color="#2e7d32",
        alpha=0.80,
        s=46,
        marker="o",
        edgecolors="black",
        linewidths=0.5,
        label=f"Resíduos Novo ÷ D³ Sem α (MAE = {mae_glob_new_0*100:.2f}%)",
    )
    ax_dd.axhline(0.0, color="black", linestyle="--", linewidth=1.4, label="Erro Zero")
    ax_dd.axhline(5.0, color="gray", linestyle=":", linewidth=1.0, label="Faixa ±5 p.p.")
    ax_dd.axhline(-5.0, color="gray", linestyle=":", linewidth=1.0)
    ax_dd.set_xlim(-0.04, 1.06)
    ax_dd.set_ylim(-25.0, 32.0)
    ax_dd.set_title("(d) Dispersão dos Resíduos (X_exp − X_pred) no White-Box Puro (Sem α)", fontweight="bold")
    ax_dd.set_xlabel("Conversão Experimental, X_Zn,exp (-)", fontweight="bold")
    ax_dd.set_ylabel("Resíduo de Conversão (pontos percentuais, %)", fontweight="bold")
    ax_dd.legend(loc="upper right", frameon=True, facecolor="white")

    fig_d.suptitle(
        "Etapa 0.3 — Desempenho Estatístico Global do Modelo White-Box Puro (Sem Parâmetro α, 128 Pontos)\n"
        "Efeito Isolado da Transformação da RRB (f_n ∝ f_m / D³) sem Modificar a Equação de Conversão",
        fontweight="bold",
        y=0.99,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    png_d = output_dir / "fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.png"
    pdf_d = output_dir / "fig_03d_whitebox_metricas_e_paridade_antigo_vs_novo.pdf"
    fig_d.savefig(png_d, dpi=300, bbox_inches="tight")
    fig_d.savefig(pdf_d, bbox_inches="tight")
    plt.close(fig_d)
    print(f"[OK] Figura 03d (sem α) salva em: {png_d}")

    print("\n" + "=" * 78)
    print("RESUMO EXECUTIVO — ETAPA 0.3 (WHITE-BOX PURO SEM α — RRB ANTIGA vs. RRB ÷ D³):")
    print(f"  • Antigo (RRB em massa, sem ÷ D³): R² = {r2_glob_old_0:.4f} | RMSE = {rmse_glob_old_0*100:.2f}% | MAE = {mae_glob_old_0*100:.2f}%")
    print(f"  • Novo (RRB ÷ D³ em número):       R² = {r2_glob_new_0:.4f} | RMSE = {rmse_glob_new_0*100:.2f}% | MAE = {mae_glob_new_0*100:.2f}%")
    print("=" * 78 + "\n")

    return df_comp


def main() -> None:
    configurar_estilo_grafico()
    base_dir = PROJECT_CODE_ROOT.parent
    gran_csv = base_dir / "Base de dados" / "raw" / "granulometria_RRB.csv"
    cin_csv = base_dir / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    output_dir = base_dir / "Código" / "outputs" / "etapa_0_3"
    output_dir.mkdir(parents=True, exist_ok=True)

    df_gran = pd.read_csv(gran_csv)
    df_exp = pd.read_csv(cin_csv)

    # Instanciar BatchPBMSolver padrão (antigo) e com RRB dividida por D³ (novo)
    # A equação de conversão em BatchPBMSolver permanece 100% intocada!
    solver_antigo = BatchPBMSolver(granulometry=RosinRammlerBennet(), n_mesh_points=5000)
    solver_novo = BatchPBMSolver(granulometry=RosinRammlerNumeroD3(), n_mesh_points=5000)

    gerar_figura_03a_distribuicoes(df_gran, solver_antigo, solver_novo, output_dir)
    simular_e_comparar_whitebox_sem_alpha(df_exp, solver_antigo, solver_novo, output_dir)


if __name__ == "__main__":
    main()
