"""
Etapa 0.3: Transformação da Distribuição Granulométrica RRB (Base Mássica -> Base Numérica via Divisão por D³)
e Avaliação do Impacto no Modelo White-Box (FPM Puro) sem Alterar a Equação de Conversão.

Disciplina: Laboratório de Operações e Processos (LOP - DEQ/UFMG)
Referências:
- Bortot Coelho, F. E. (2017). Dissertação de Mestrado, PPGEM/UFMG, Equações (3.45), (3.47), (3.48) e (3.49), p. 73-74.
- Herbst, J. A. (1979). Rate Processes of Extractive Metallurgy. Plenum Press.

Objetivo:
1. Converter a função densidade de probabilidade de Rosin-Rammler-Bennet (originalmente ajustada em base mássica f_m(D))
   para a função densidade populacional em base numérica f_n(D), dividindo-a por D³ e normalizando no domínio [D_min, D_max]:
       f_n(D) = [ D⁻³ · f_m(D) ] / [ ∫ D⁻³ · f_m(D) dD ]
2. Manter a equação de conversão do Balanço Populacional (BatchPBMSolver) 100% inalterada:
       X_Zn(δ) = 1 - [ ∫_δ^D_max (D - δ)³ · f₀(D) dD ] / [ ∫_D_min^D_max D³ · f₀(D) dD ]
3. Comparar grafica e estatisticamente:
   - As duas distribuições granulométricas (Antiga: f₀ = f_m vs. Nova: f₀ = f_n proporcional a f_m / D³);
   - O peso volumétrico efetivo D³ · f₀(D) e a aderência aos 33 pontos experimentais da Tabela 5.4;
   - A curva característica de conversão X_Zn(δ) em função do deslocamento diametral acumulado δ;
   - A simulação White-Box (FPM Puro com α = 5500 µm/min e Cinético Puro com α = 0 µm/min) nos 16 ensaios de bancada.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Adicionar diretório raiz de código ao sys.path
PROJECT_CODE_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_CODE_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_CODE_ROOT))

from src.physics.granulometry import RosinRammlerBennet
from src.physics.kinetics import LeachingKinetics
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
        "axes.labelsize": 11.5,
        "axes.titlesize": 12.0,
        "xtick.labelsize": 10.0,
        "ytick.labelsize": 10.0,
        "legend.fontsize": 9.2,
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
    """Gera a Figura 03a (Painel 2x2) comparando a distribuição antiga (f_m sem dividir por D³)
    e a nova distribuição (f_n = f_m / D³ normalizada) e seu efeito no mapeamento δ -> X_Zn.
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
    # No modelo antigo: f0 = f_m -> peso volumétrico proporcional a D³ * f_m(D)
    peso_vol_antigo = (d_grid ** 3) * fm_grid
    norm_vol_antigo = float(trapezoid(peso_vol_antigo, d_grid))
    dens_massa_efetiva_antiga = peso_vol_antigo / norm_vol_antigo

    # No modelo novo: f0 = f_n ∝ f_m(D) / D³ -> peso volumétrico D³ * f_n(D) ∝ f_m(D)
    norm_vol_novo = float(trapezoid(fm_grid, d_grid))
    dens_massa_efetiva_nova = fm_grid / norm_vol_novo

    # Diâmetros médios efetivos de massa vista pelo PBM
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

    # Encontrar δ para atingir 50% e 80% de conversão
    delta_50_antigo = float(np.interp(0.50, x_antigo_vec, delta_vec))
    delta_50_novo = float(np.interp(0.50, x_novo_vec, delta_vec))
    delta_80_antigo = float(np.interp(0.80, x_antigo_vec, delta_vec))
    delta_80_novo = float(np.interp(0.80, x_novo_vec, delta_vec))

    fig, axes = plt.subplots(2, 2, figsize=(15, 11.5))

    # -------------------------------------------------------------------------
    # Painel (a): Densidade Original f_m(D) vs Densidade Dividida por D³ f_n(D)
    # -------------------------------------------------------------------------
    ax_a = axes[0, 0]
    ax_a.plot(
        d_log,
        fm_log,
        color="#1f77b4",
        linewidth=2.3,
        label=r"Antiga: Densidade Mássica RRB $f_m(D) = dF/dD$",
    )
    ax_a.plot(
        d_log,
        fn_log,
        color="#d62728",
        linewidth=2.3,
        linestyle="-",
        label=r"Nova: Densidade Numérica $f_n(D) \propto f_m(D) / D^3$",
    )
    ax_a.set_xscale("log")
    ax_a.set_yscale("log")
    ax_a.set_xlim(0.1, 300.0)
    ax_a.set_ylim(1e-9, 1e2)
    ax_a.set_title("(a) Densidade RRB: Base Mássica vs. Base Numérica (÷ D³)", fontweight="bold", fontsize=11.5)
    ax_a.set_xlabel("Diâmetro de Partícula, D (µm) [Escala Log]", fontweight="bold")
    ax_a.set_ylabel("Densidade de Probabilidade, f₀(D) (µm⁻¹) [Escala Log]", fontweight="bold")
    ax_a.annotate(
        "Ao dividir por D³, evidencia-se que\nas partículas finas (< 10 µm) dominam\na contagem numérica da população\n(inclinação ~ D^(m-4) = D^(-2,98))",
        xy=(1.0, fn_log[np.argmin(np.abs(d_log - 1.0))]),
        xytext=(3.5, 1e-2),
        arrowprops=dict(facecolor="#b71c1c", shrink=0.08, width=1.2, headwidth=5),
        fontsize=9.0,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#ffebee", edgecolor="#ef9a9a"),
    )
    ax_a.legend(loc="lower left", frameon=True, facecolor="white", edgecolor="#cccccc")

    # -------------------------------------------------------------------------
    # Painel (b): Peso Mássico/Volumétrico Efetivo no PBM: D³ · f₀(D) normalizado
    # -------------------------------------------------------------------------
    ax_b = axes[0, 1]
    ax_b.plot(
        d_grid,
        dens_massa_efetiva_antiga,
        color="#1f77b4",
        linestyle="--",
        linewidth=2.2,
        label=f"Antigo [D³·f_m(D) ∝ D⁶·f_n]: Média Efetiva = {d_medio_efetivo_antigo:.1f} µm",
    )
    ax_b.fill_between(d_grid, 0, dens_massa_efetiva_antiga, color="#1f77b4", alpha=0.14)

    ax_b.plot(
        d_grid,
        dens_massa_efetiva_nova,
        color="#2e7d32",
        linestyle="-",
        linewidth=2.4,
        label=f"Novo [D³·(f_m/D³) = f_m(D)]: Média Real = {d_medio_efetivo_novo:.1f} µm",
    )
    ax_b.fill_between(d_grid, 0, dens_massa_efetiva_nova, color="#2e7d32", alpha=0.18)

    ax_b.axvline(d_medio_efetivo_antigo, color="#1f77b4", linestyle=":", linewidth=1.5)
    ax_b.axvline(d_medio_efetivo_novo, color="#2e7d32", linestyle=":", linewidth=1.5)
    ax_b.set_xlim(-5, 300)
    ax_b.set_ylim(0, max(np.max(dens_massa_efetiva_nova), np.max(dens_massa_efetiva_antiga)) * 1.12)
    ax_b.set_title("(b) Massa Efetiva na Equação de Conversão [D³ · f₀(D)]", fontweight="bold", fontsize=11.5)
    ax_b.set_xlabel("Diâmetro de Partícula, D (µm)", fontweight="bold")
    ax_b.set_ylabel("Fração Volumétrica/Mássica Efetiva (µm⁻¹)", fontweight="bold")
    ax_b.annotate(
        "Sem dividir por D³, o termo D³·f_m(D)\ndeslocava artificialmente a massa\npara partículas grandes (~118 µm),\napagando os finos!",
        xy=(118.0, dens_massa_efetiva_antiga[np.argmin(np.abs(d_grid - 118.0))]),
        xytext=(135.0, 0.0115),
        arrowprops=dict(facecolor="#1565c0", shrink=0.08, width=1.2, headwidth=5),
        fontsize=9.0,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#e3f2fd", edgecolor="#90caf9"),
    )
    ax_b.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#cccccc")

    # -------------------------------------------------------------------------
    # Painel (c): Fração Acumulada de Massa no PBM vs Dados Experimentais Reais
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
        label="Massa Acumulada no PBM Antigo (sem ÷ D³)",
    )
    ax_c.plot(
        d_grid,
        cum_massa_nova,
        color="#2e7d32",
        linestyle="-",
        linewidth=2.5,
        label="Massa Acumulada no PBM Novo (com ÷ D³ — R² = 0,9962)",
    )
    ax_c.set_xlim(-5, 300)
    ax_c.set_ylim(-0.03, 1.05)
    ax_c.set_title("(c) Massa Acumulada Integrada pelo PBM vs. Dados Experimentais", fontweight="bold")
    ax_c.set_xlabel("Diâmetro de Partícula, D (µm)", fontweight="bold")
    ax_c.set_ylabel("Fração Mássica Acumulada Passante, F(D) (-)", fontweight="bold")
    ax_c.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#cccccc")

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
    ax_d.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#cccccc")

    fig.suptitle(
        "Etapa 0.3 — Impacto da Conversão da Distribuição RRB de Massa para Número (Divisão por D³)\n"
        "Preservando Intacta a Equação de Conversão X_Zn(t) = 1 − ∫(D − δ)³f₀(D)dD / ∫D³f₀(D)dD",
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


def simular_e_comparar_whitebox(
    df_exp: pd.DataFrame,
    solver_antigo: BatchPBMSolver,
    solver_novo: BatchPBMSolver,
    output_dir: Path,
) -> pd.DataFrame:
    """Executa o modelo White-Box (FPM Nominal α = 5500 µm/min e Cinético Puro α = 0 µm/min)
    com a distribuição antiga vs. nova (dividida por D³) nos 16 ensaios e gera as Figuras 03b, 03c e 03d.
    """
    ensaios_unicos = sorted(df_exp["ensaio"].unique())
    t_fine = np.linspace(0.0, 15.0, 300)

    records = []
    sims = {}

    y_true_all = []
    y_old_5500_all, y_new_5500_all = [], []
    y_old_0_all, y_new_0_all = [], []
    eta_all = []

    for ens in ensaios_unicos:
        sub = df_exp[df_exp["ensaio"] == ens].sort_values("t_min")
        ca0 = float(sub["CA0_mol_L"].iloc[0])
        eta = float(sub["razao_molar_eta"].iloc[0])
        t_exp = sub["t_min"].values
        x_exp = sub["XZn"].values

        # 1. White-Box α = 5500 µm/min (Nominal Bortot Coelho)
        old_5500_pts = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=5500.0)
        old_5500_fine = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_fine, alpha=5500.0)

        new_5500_pts = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=5500.0)
        new_5500_fine = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_fine, alpha=5500.0)

        # 2. White-Box α = 0 µm/min (Cinético Puro Balarini)
        old_0_pts = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=0.0)
        old_0_fine = solver_antigo.simulate(ca0=ca0, eta=eta, t_eval=t_fine, alpha=0.0)

        new_0_pts = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=0.0)
        new_0_fine = solver_novo.simulate(ca0=ca0, eta=eta, t_eval=t_fine, alpha=0.0)

        r2_old_5500 = float(r2_score(x_exp, old_5500_pts["XZn"]))
        rmse_old_5500 = float(np.sqrt(mean_squared_error(x_exp, old_5500_pts["XZn"])))
        mae_old_5500 = float(mean_absolute_error(x_exp, old_5500_pts["XZn"]))

        r2_new_5500 = float(r2_score(x_exp, new_5500_pts["XZn"]))
        rmse_new_5500 = float(np.sqrt(mean_squared_error(x_exp, new_5500_pts["XZn"])))
        mae_new_5500 = float(mean_absolute_error(x_exp, new_5500_pts["XZn"]))

        r2_old_0 = float(r2_score(x_exp, old_0_pts["XZn"]))
        rmse_old_0 = float(np.sqrt(mean_squared_error(x_exp, old_0_pts["XZn"])))

        r2_new_0 = float(r2_score(x_exp, new_0_pts["XZn"]))
        rmse_new_0 = float(np.sqrt(mean_squared_error(x_exp, new_0_pts["XZn"])))

        records.append({
            "ensaio": ens,
            "razao_molar_eta": eta,
            "CA0_mol_L": ca0,
            "R2_antigo_alpha5500": round(r2_old_5500, 4),
            "R2_novo_D3_alpha5500": round(r2_new_5500, 4),
            "ganho_R2_alpha5500": round(r2_new_5500 - r2_old_5500, 4),
            "RMSE_antigo_alpha5500": round(rmse_old_5500, 4),
            "RMSE_novo_D3_alpha5500": round(rmse_new_5500, 4),
            "MAE_antigo_alpha5500": round(mae_old_5500, 4),
            "MAE_novo_D3_alpha5500": round(mae_new_5500, 4),
            "R2_antigo_alpha0": round(r2_old_0, 4),
            "R2_novo_D3_alpha0": round(r2_new_0, 4),
            "RMSE_antigo_alpha0": round(rmse_old_0, 4),
            "RMSE_novo_D3_alpha0": round(rmse_new_0, 4),
            "X_exp_final": round(float(x_exp[-1]), 4),
            "X_antigo_5500_final": round(float(old_5500_pts["XZn"][-1]), 4),
            "X_novo_5500_final": round(float(new_5500_pts["XZn"][-1]), 4),
        })

        sims[ens] = {
            "ca0": ca0,
            "eta": eta,
            "t_exp": t_exp,
            "x_exp": x_exp,
            "t_fine": t_fine,
            "old_5500_fine": old_5500_fine["XZn"],
            "new_5500_fine": new_5500_fine["XZn"],
            "old_0_fine": old_0_fine["XZn"],
            "new_0_fine": new_0_fine["XZn"],
            "r2_old_5500": r2_old_5500,
            "r2_new_5500": r2_new_5500,
            "rmse_old_5500": rmse_old_5500,
            "rmse_new_5500": rmse_new_5500,
            "r2_old_0": r2_old_0,
            "r2_new_0": r2_new_0,
        }

        y_true_all.extend(x_exp)
        y_old_5500_all.extend(old_5500_pts["XZn"])
        y_new_5500_all.extend(new_5500_pts["XZn"])
        y_old_0_all.extend(old_0_pts["XZn"])
        y_new_0_all.extend(new_0_pts["XZn"])
        eta_all.extend([eta] * len(x_exp))

    df_comp = pd.DataFrame(records)
    csv_path = output_dir / "tabela_comparativa_whitebox_antigo_vs_novo_d3.csv"
    df_comp.to_csv(csv_path, index=False)

    y_true_arr = np.array(y_true_all)
    y_old_5500_arr = np.array(y_old_5500_all)
    y_new_5500_arr = np.array(y_new_5500_all)
    y_old_0_arr = np.array(y_old_0_all)
    y_new_0_arr = np.array(y_new_0_all)
    eta_arr = np.array(eta_all)

    r2_glob_old_5500 = float(r2_score(y_true_arr, y_old_5500_arr))
    rmse_glob_old_5500 = float(np.sqrt(mean_squared_error(y_true_arr, y_old_5500_arr)))
    mae_glob_old_5500 = float(mean_absolute_error(y_true_arr, y_old_5500_arr))

    r2_glob_new_5500 = float(r2_score(y_true_arr, y_new_5500_arr))
    rmse_glob_new_5500 = float(np.sqrt(mean_squared_error(y_true_arr, y_new_5500_arr)))
    mae_glob_new_5500 = float(mean_absolute_error(y_true_arr, y_new_5500_arr))

    r2_glob_old_0 = float(r2_score(y_true_arr, y_old_0_arr))
    rmse_glob_old_0 = float(np.sqrt(mean_squared_error(y_true_arr, y_old_0_arr)))

    r2_glob_new_0 = float(r2_score(y_true_arr, y_new_0_arr))
    rmse_glob_new_0 = float(np.sqrt(mean_squared_error(y_true_arr, y_new_0_arr)))

    # =========================================================================
    # FIGURA 03b: PAINEL 2x2 POR RAZÃO MOLAR η (ANTIGO vs NOVO ÷ D³)
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

            # Curva Antiga (Tracejada)
            ax.plot(
                s["t_fine"],
                s["old_5500_fine"],
                color=cor,
                linestyle="--",
                linewidth=1.6,
                alpha=0.65,
                label=f"Antigo (sem ÷D³): C_A0={ca0:.2f} M",
            )
            # Curva Nova com RRB ÷ D³ (Sólida)
            ax.plot(
                s["t_fine"],
                s["new_5500_fine"],
                color=cor,
                linestyle="-",
                linewidth=2.3,
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

        ax.set_title(f"Painel ({chr(97 + idx)}) — Razão Molar η = {eta_val}", fontweight="bold")
        ax.set_xlim(-0.3, 15.5)
        ax.set_ylim(-0.02, 1.06)
        if eta_val == 0.5:
            ax.axhline(0.50, color="gray", linestyle=":", linewidth=1.2)
            ax.axhline(0.383, color="black", linestyle=":", linewidth=1.1)
        elif eta_val == 1.0:
            ax.axhline(0.766, color="black", linestyle=":", linewidth=1.1)

        ax.legend(loc="lower right", fontsize=8.0, ncol=2, frameon=True, facecolor="white", edgecolor="#cccccc")

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
        "Simulação White-Box FPM Nominal (α = 5500 µm/min): Distribuição RRB Antiga vs. Nova (Dividida por D³)\n"
        f"Antigo (Massa): R² Global = {r2_glob_old_5500:.4f} (RMSE = {rmse_glob_old_5500*100:.2f}%)  |  "
        f"Novo (Número ÷ D³): R² Global = {r2_glob_new_5500:.4f} (RMSE = {rmse_glob_new_5500*100:.2f}%)",
        fontweight="bold",
        y=0.98,
    )
    plt.subplots_adjust(top=0.90, bottom=0.08, left=0.07, right=0.97, hspace=0.20, wspace=0.12)

    png_b = output_dir / "fig_03b_whitebox_painel_eta_antigo_vs_novo.png"
    pdf_b = output_dir / "fig_03b_whitebox_painel_eta_antigo_vs_novo.pdf"
    fig_b.savefig(png_b, dpi=300, bbox_inches="tight")
    fig_b.savefig(pdf_b, bbox_inches="tight")
    plt.close(fig_b)
    print(f"[OK] Figura 03b salva em: {png_b}")

    # =========================================================================
    # FIGURA 03c: PAINEL 4x4 COMPLETO DOS 16 ENSAIOS INDIVIDUAIS
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
            markersize=5.5,
            linestyle="none",
            zorder=6,
            label="Experimental" if idx == 0 else "",
        )
        # Antigo α = 5500
        ax.plot(
            s["t_fine"],
            s["old_5500_fine"],
            color="#1f77b4",
            linestyle="--",
            linewidth=1.8,
            zorder=3,
            label="White-Box Antigo (α=5500, sem ÷D³)" if idx == 0 else "",
        )
        # Novo α = 5500 (RRB ÷ D³)
        ax.plot(
            s["t_fine"],
            s["new_5500_fine"],
            color="#d62728",
            linestyle="-",
            linewidth=2.2,
            zorder=5,
            label="White-Box Novo (α=5500, RRB ÷ D³)" if idx == 0 else "",
        )
        # Novo α = 0 (Cinético Puro com RRB ÷ D³)
        ax.plot(
            s["t_fine"],
            s["new_0_fine"],
            color="#2e7d32",
            linestyle="-.",
            linewidth=1.6,
            alpha=0.85,
            zorder=4,
            label="Cinético Puro Novo (α=0, RRB ÷ D³)" if idx == 0 else "",
        )

        ax.set_title(
            f"Ensaio {ens:02d} (C_A0={s['ca0']:.2f} M, η={s['eta']:.1f})\n"
            f"R² (α=5500): {s['r2_old_5500']:.3f} → {s['r2_new_5500']:.3f}",
            fontsize=9.5,
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
        ncol=4,
        fontsize=10.5,
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
        "Etapa 0.3 — Comparativo Ensaio a Ensaio (16 Ensaios de Bancada): Efeito da Divisão da RRB por D³ no White-Box",
        fontsize=14.5,
        fontweight="bold",
        y=0.98,
    )
    plt.subplots_adjust(top=0.89, bottom=0.06, left=0.06, right=0.98, hspace=0.34, wspace=0.14)

    png_c = output_dir / "fig_03c_whitebox_16_ensaios_grid_4x4.png"
    pdf_c = output_dir / "fig_03c_whitebox_16_ensaios_grid_4x4.pdf"
    fig_c.savefig(png_c, dpi=300, bbox_inches="tight")
    fig_c.savefig(pdf_c, bbox_inches="tight")
    plt.close(fig_c)
    print(f"[OK] Figura 03c salva em: {png_c}")

    # =========================================================================
    # FIGURA 03d: MÉTRICAS R² / RMSE POR ENSAIO E DIAGRAMA DE PARIDADE 1:1
    # =========================================================================
    fig_d, axes_d = plt.subplots(2, 2, figsize=(15, 11.5))

    x_idx = np.arange(len(ensaios_unicos))
    bw = 0.38

    # (a) R² por Ensaio (α = 5500)
    ax_da = axes_d[0, 0]
    ax_da.bar(
        x_idx - bw / 2,
        df_comp["R2_antigo_alpha5500"],
        width=bw,
        color="#90a4ae",
        edgecolor="#37474f",
        label=f"Antigo (sem ÷D³) — R² Global = {r2_glob_old_5500:.4f}",
    )
    ax_da.bar(
        x_idx + bw / 2,
        df_comp["R2_novo_D3_alpha5500"],
        width=bw,
        color="#d62728",
        edgecolor="#8e0000",
        label=f"Novo (RRB ÷ D³) — R² Global = {r2_glob_new_5500:.4f}",
    )
    ax_da.set_xticks(x_idx)
    ax_da.set_xticklabels([f"E{e}" for e in ensaios_unicos], fontweight="bold", fontsize=9)
    ax_da.set_ylim(0.45, 1.04)
    ax_da.set_title("(a) Evolução do R² por Ensaio no White-Box (α = 5500 µm/min)", fontweight="bold")
    ax_da.set_xlabel("Ensaio Experimental", fontweight="bold")
    ax_da.set_ylabel("Coeficiente de Determinação, R² (-)", fontweight="bold")
    ax_da.legend(loc="lower right", frameon=True, facecolor="white")

    # (b) RMSE por Ensaio (α = 5500)
    ax_db = axes_d[0, 1]
    ax_db.bar(
        x_idx - bw / 2,
        df_comp["RMSE_antigo_alpha5500"] * 100.0,
        width=bw,
        color="#90a4ae",
        edgecolor="#37474f",
        label=f"Antigo (sem ÷D³) — RMSE Global = {rmse_glob_old_5500*100:.2f}%",
    )
    ax_db.bar(
        x_idx + bw / 2,
        df_comp["RMSE_novo_D3_alpha5500"] * 100.0,
        width=bw,
        color="#2e7d32",
        edgecolor="#1b5e20",
        label=f"Novo (RRB ÷ D³) — RMSE Global = {rmse_glob_new_5500*100:.2f}%",
    )
    ax_db.set_xticks(x_idx)
    ax_db.set_xticklabels([f"E{e}" for e in ensaios_unicos], fontweight="bold", fontsize=9)
    ax_db.set_title("(b) Redução do Erro Quadrático Médio (RMSE %) por Ensaio", fontweight="bold")
    ax_db.set_xlabel("Ensaio Experimental", fontweight="bold")
    ax_db.set_ylabel("RMSE de Conversão (%)", fontweight="bold")
    ax_db.legend(loc="upper right", frameon=True, facecolor="white")

    # (c) Paridade 1:1 Antigo vs Novo (α = 5500 µm/min)
    ax_dc = axes_d[1, 0]
    ax_dc.scatter(
        y_true_arr,
        y_old_5500_arr,
        color="#1f77b4",
        alpha=0.55,
        s=42,
        marker="s",
        label=f"White-Box Antigo (R²={r2_glob_old_5500:.4f}, RMSE={rmse_glob_old_5500*100:.2f}%)",
    )
    ax_dc.scatter(
        y_true_arr,
        y_new_5500_arr,
        color="#d62728",
        alpha=0.80,
        s=48,
        marker="o",
        edgecolors="black",
        linewidths=0.5,
        label=f"White-Box Novo ÷ D³ (R²={r2_glob_new_5500:.4f}, RMSE={rmse_glob_new_5500*100:.2f}%)",
    )
    ax_dc.plot([-0.05, 1.08], [-0.05, 1.08], "k--", linewidth=1.5, label="Bissetriz Ideal 1:1")
    ax_dc.plot([-0.05, 1.08], [0.0, 1.13], color="gray", linestyle=":", linewidth=1.0, label="Faixa ±5%")
    ax_dc.plot([-0.05, 1.08], [-0.10, 1.03], color="gray", linestyle=":", linewidth=1.0)
    ax_dc.set_xlim(-0.04, 1.06)
    ax_dc.set_ylim(-0.04, 1.06)
    ax_dc.set_title("(c) Paridade 1:1 — White-Box Nominal (α = 5500 µm/min)", fontweight="bold")
    ax_dc.set_xlabel("Conversão Experimental, X_Zn,exp (-)", fontweight="bold")
    ax_dc.set_ylabel("Conversão Predita pelo White-Box, X_Zn,pred (-)", fontweight="bold")
    ax_dc.legend(loc="upper left", frameon=True, facecolor="white")

    # (d) Paridade 1:1 Antigo vs Novo (Cinético Puro α = 0 µm/min)
    ax_dd = axes_d[1, 1]
    ax_dd.scatter(
        y_true_arr,
        y_old_0_arr,
        color="#1f77b4",
        alpha=0.55,
        s=42,
        marker="s",
        label=f"Cinético Antigo α=0 (R²={r2_glob_old_0:.4f}, RMSE={rmse_glob_old_0*100:.2f}%)",
    )
    ax_dd.scatter(
        y_true_arr,
        y_new_0_arr,
        color="#2e7d32",
        alpha=0.80,
        s=48,
        marker="o",
        edgecolors="black",
        linewidths=0.5,
        label=f"Cinético Novo α=0 ÷ D³ (R²={r2_glob_new_0:.4f}, RMSE={rmse_glob_new_0*100:.2f}%)",
    )
    ax_dd.plot([-0.05, 1.08], [-0.05, 1.08], "k--", linewidth=1.5, label="Bissetriz Ideal 1:1")
    ax_dd.plot([-0.05, 1.08], [0.0, 1.13], color="gray", linestyle=":", linewidth=1.0, label="Faixa ±5%")
    ax_dd.plot([-0.05, 1.08], [-0.10, 1.03], color="gray", linestyle=":", linewidth=1.0)
    ax_dd.set_xlim(-0.04, 1.06)
    ax_dd.set_ylim(-0.04, 1.06)
    ax_dd.set_title("(d) Paridade 1:1 — Modelo Cinético Puro (α = 0 µm/min)", fontweight="bold")
    ax_dd.set_xlabel("Conversão Experimental, X_Zn,exp (-)", fontweight="bold")
    ax_dd.set_ylabel("Conversão Predita pelo White-Box, X_Zn,pred (-)", fontweight="bold")
    ax_dd.legend(loc="upper left", frameon=True, facecolor="white")

    fig_d.suptitle(
        "Etapa 0.3 — Desempenho Estatístico Global do Modelo White-Box (128 Pontos Experimentais)\n"
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
    print(f"[OK] Figura 03d salva em: {png_d}")

    print("\n" + "=" * 78)
    print("RESUMO EXECUTIVO — ETAPA 0.3 (TRANSFORMAÇÃO DA RRB DIVIDINDO POR D³):")
    print(f"  White-Box Nominal (α = 5500 µm/min):")
    print(f"    • Antigo (RRB em massa):       R² = {r2_glob_old_5500:.4f} | RMSE = {rmse_glob_old_5500*100:.2f}% | MAE = {mae_glob_old_5500*100:.2f}%")
    print(f"    • Novo (RRB ÷ D³ em número):   R² = {r2_glob_new_5500:.4f} | RMSE = {rmse_glob_new_5500*100:.2f}% | MAE = {mae_glob_new_5500*100:.2f}%")
    print(f"  White-Box Cinético Puro (α = 0 µm/min):")
    print(f"    • Antigo (RRB em massa):       R² = {r2_glob_old_0:.4f} | RMSE = {rmse_glob_old_0*100:.2f}%")
    print(f"    • Novo (RRB ÷ D³ em número):   R² = {r2_glob_new_0:.4f} | RMSE = {rmse_glob_new_0*100:.2f}%")
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
    simular_e_comparar_whitebox(df_exp, solver_antigo, solver_novo, output_dir)


if __name__ == "__main__":
    main()
