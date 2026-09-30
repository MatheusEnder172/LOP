"""
Etapa 0.2: Visualização e Validação da Distribuição Granulométrica (RRB)
Disciplina: Laboratório de Operações e Processos (LOP - DEQ/UFMG)
Referência dos dados: Dissertação de Fabrício Bortot Coelho (2017), Capítulo 5, Tabelas 5.4, 5.5 e 5.6.

Objetivo:
- Carregar os dados combinados de peneiramento a úmido e difração a laser.
- Avaliar a aderência ao modelo de Rosin-Rammler-Bennet (RRB).
- Gerar gráfico 2x2 com:
  (a) Curva acumulada passante F(D) em escala linear.
  (b) Curva acumulada passante F(D) em escala semi-log (estilo Figura 5.4 da dissertação).
  (c) Função densidade de frequência f0(D) = dF/dD.
  (d) Linearização clássica do modelo RRB: ln(ln(1/(1-F))) vs ln(D).
- Calcular as métricas estatísticas de ajuste (R², RMSE, MAE).
- Salvar imagens em alta resolução (300 DPI) em PNG e PDF vetorial na pasta de saídas da Etapa 0.2.
"""

from pathlib import Path
from typing import Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def configurar_estilo_grafico() -> None:
    """Configura parâmetros visuais globais para gráficos científicos de alta qualidade."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "grid.linestyle": "--",
    })


def calcular_metricas_rrb(
    diametros: np.ndarray,
    fracao_exp: np.ndarray,
    d63_2: float = 41.65,
    m: float = 1.022
) -> Dict[str, float]:
    """Calcula R², RMSE e MAE entre os dados experimentais e o modelo RRB.

    Args:
        diametros: Diâmetros das partículas (µm).
        fracao_exp: Fração acumulada passante experimental (0 a 1).
        d63_2: Diâmetro característico RRB (µm).
        m: Módulo de dispersão RRB.

    Returns:
        Dicionário com R2, RMSE e MAE.
    """
    f_pred = 1.0 - np.exp(-((diametros / d63_2) ** m))
    residuos = fracao_exp - f_pred
    ss_res = np.sum(residuos ** 2)
    ss_tot = np.sum((fracao_exp - np.mean(fracao_exp)) ** 2)
    r2 = 1.0 - (ss_res / ss_tot)
    rmse = np.sqrt(np.mean(residuos ** 2))
    mae = np.mean(np.abs(residuos))

    return {
        "R2": float(r2),
        "RMSE": float(rmse),
        "MAE": float(mae),
        "SS_res": float(ss_res)
    }


def gerar_grafico_granulometria(
    caminho_dados: Path,
    caminho_saida_dir: Path,
    d63_2: float = 41.65,
    m: float = 1.022
) -> Dict[str, float]:
    """Gera visualização completa da distribuição granulométrica da calcina de zinco."""
    configurar_estilo_grafico()

    df = pd.read_csv(caminho_dados)
    # Converter porcentagem para fração (0 a 1)
    df["fracao_acumulada"] = df["passante_acumulada_pct"] / 100.0

    df_peneira = df[df["metodo"] == "Peneiramento a umido"].sort_values("peneira_ou_diametro_um")
    df_laser = df[df["metodo"] == "Difracao a Laser"].sort_values("peneira_ou_diametro_um")

    # Avaliação métrica global
    metricas = calcular_metricas_rrb(
        df["peneira_ou_diametro_um"].values,
        df["fracao_acumulada"].values,
        d63_2=d63_2,
        m=m
    )

    # Malhas contínuas para curvas do modelo
    d_cont_linear = np.linspace(0.1, 300.0, 1000)
    f_cont_linear = 1.0 - np.exp(-((d_cont_linear / d63_2) ** m))
    f0_densidade = (m / d63_2) * ((d_cont_linear / d63_2) ** (m - 1.0)) * np.exp(-((d_cont_linear / d63_2) ** m))

    d_cont_log = np.logspace(-1.0, 3.0, 1000)
    f_cont_log = 1.0 - np.exp(-((d_cont_log / d63_2) ** m))

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(14, 11))

    # -------------------------------------------------------------
    # Subplot (a): Fração Acumulada - Escala Linear
    # -------------------------------------------------------------
    ax_a = axes[0, 0]
    ax_a.plot(d_cont_linear, f_cont_linear, color="#d62728", linewidth=2.0, label=f"Modelo RRB (D₆₃,₂={d63_2:.2f} µm, m={m:.3f})")
    ax_a.scatter(df_peneira["peneira_ou_diametro_um"], df_peneira["fracao_acumulada"], color="#1f77b4", marker="D", s=45, label="Peneiramento a Úmido", zorder=4)
    ax_a.scatter(df_laser["peneira_ou_diametro_um"], df_laser["fracao_acumulada"], color="#2ca02c", marker="o", s=35, label="Difração a Laser", alpha=0.8, zorder=3)
    ax_a.axvline(d63_2, color="gray", linestyle=":", linewidth=1.2)
    ax_a.axhline(0.632, color="gray", linestyle=":", linewidth=1.2)
    ax_a.annotate(f"D₆₃,₂ = {d63_2} µm (F = 63,2%)", xy=(d63_2 + 8, 0.60), fontsize=9, color="#444444")
    ax_a.set_title("(a) Fração Mássica Acumulada Passante F(D) - Escala Linear", weight="bold")
    ax_a.set_xlabel("Diâmetro de Partícula D (µm)", weight="semibold")
    ax_a.set_ylabel("Fração Acumulada F(D) (-)", weight="semibold")
    ax_a.set_xlim(-5, 305)
    ax_a.set_ylim(-0.02, 1.05)
    ax_a.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#cccccc")

    # -------------------------------------------------------------
    # Subplot (b): Fração Acumulada - Escala Semi-Log (Figura 5.4 da dissertação)
    # -------------------------------------------------------------
    ax_b = axes[0, 1]
    ax_b.plot(d_cont_log, f_cont_log, color="#d62728", linewidth=2.0, label="Modelo RRB")
    ax_b.scatter(df["peneira_ou_diametro_um"], df["fracao_acumulada"], color="#1f77b4", marker="o", s=30, label="Passante Acumulada Experimental", zorder=4)
    ax_b.set_xscale("log")
    ax_b.set_title("(b) Distribuição Granulométrica Acumulada - Escala Semi-Log", weight="bold")
    ax_b.set_xlabel("Diâmetro de Partícula D (µm) [Escala Log]", weight="semibold")
    ax_b.set_ylabel("Fração Acumulada F(D) (-)", weight="semibold")
    ax_b.set_xlim(0.1, 1000.0)
    ax_b.set_ylim(-0.02, 1.05)
    ax_b.annotate(f"Ajuste Global:\nR² = {metricas['R2']:.4f}\nRMSE = {metricas['RMSE']:.4f}", xy=(0.2, 0.75), fontsize=10, bbox=dict(boxstyle="round,pad=0.4", fc="#f8f9fa", ec="#cccccc"))
    ax_b.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#cccccc")

    # -------------------------------------------------------------
    # Subplot (c): Função Densidade de Distribuição f0(D)
    # -------------------------------------------------------------
    ax_c = axes[1, 0]
    ax_c.plot(d_cont_linear, f0_densidade, color="#9467bd", linewidth=2.2, label=r"Densidade $f_0(D) = dF/dD$")
    ax_c.fill_between(d_cont_linear, 0, f0_densidade, color="#9467bd", alpha=0.18)
    # Destacar diâmetro médio da dissertação: 41.28 um
    d_medio = 41.28
    ax_c.axvline(d_medio, color="#d62728", linestyle="--", linewidth=1.4, label=f"Diâmetro Médio (µ = {d_medio} µm)")
    ax_c.axvline(d63_2, color="#ff7f0e", linestyle=":", linewidth=1.4, label=f"D₆₃,₂ = {d63_2} µm")
    ax_c.set_title("(c) Função Densidade de Frequência Inicial f₀(D)", weight="bold")
    ax_c.set_xlabel("Diâmetro de Partícula D (µm)", weight="semibold")
    ax_c.set_ylabel("Densidade de Probabilidade f₀(D) (µm⁻¹)", weight="semibold")
    ax_c.set_xlim(-5, 305)
    ax_c.set_ylim(0, np.max(f0_densidade) * 1.15)
    ax_c.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#cccccc")

    # -------------------------------------------------------------
    # Subplot (d): Linearização RRB (Figura 5.2 da dissertação)
    # ln[ln(1/(1-F))] = m*ln(D) - m*ln(D63_2)
    # -------------------------------------------------------------
    ax_d = axes[1, 1]
    # Filtrar pontos para evitar log de zero ou log de número negativo
    df_lin = df[(df["fracao_acumulada"] > 0.001) & (df["fracao_acumulada"] < 0.999)].copy()
    x_lin = np.log(df_lin["peneira_ou_diametro_um"].values)
    y_lin = np.log(np.log(1.0 / (1.0 - df_lin["fracao_acumulada"].values)))

    # Ajuste por regressão linear para conferência
    poly_fit = np.polyfit(x_lin, y_lin, 1)
    m_reg = poly_fit[0]
    intercept_reg = poly_fit[1]
    d63_2_reg = np.exp(-intercept_reg / m_reg)
    y_reg_pred = np.polyval(poly_fit, x_lin)
    r2_reg = 1.0 - np.sum((y_lin - y_reg_pred) ** 2) / np.sum((y_lin - np.mean(y_lin)) ** 2)

    x_line_lin = np.linspace(np.min(x_lin) - 0.2, np.max(x_lin) + 0.2, 200)
    y_line_lin = np.polyval(poly_fit, x_line_lin)

    ax_d.scatter(x_lin, y_lin, color="#1f77b4", marker="^", s=40, label="Dados Transformados", zorder=3)
    ax_d.plot(x_line_lin, y_line_lin, color="#d62728", linestyle="--", linewidth=1.8, label=f"Reta Ajustada: y = {m_reg:.4f}x {intercept_reg:+.4f}")
    ax_d.set_title("(d) Linearização RRB: ln[ln(1/(1-F))] vs. ln(D)", weight="bold")
    ax_d.set_xlabel("ln(D) [D em µm]", weight="semibold")
    ax_d.set_ylabel("ln[ln(1/(1-F(D)))] (-)", weight="semibold")
    ax_d.annotate(
        f"Parâmetros da Regressão:\nm = {m_reg:.4f}\nD₆₃,₂ = {d63_2_reg:.2f} µm\nR² = {r2_reg:.4f}",
        xy=(np.min(x_lin) + 0.3, np.max(y_lin) - 2.0),
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.4", fc="#f8f9fa", ec="#cccccc")
    )
    ax_d.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#cccccc")

    fig.suptitle(
        "Caracterização da Distribuição Granulométrica do Concentrado Ustulado de Zinco (Calcina)\n"
        "Ajuste ao Modelo Rosin-Rammler-Bennet (RRB) — Dados Experimentais de Bortot Coelho (2017)",
        weight="bold",
        y=0.99
    )

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Garantir criação do diretório de saída
    caminho_saida_dir.mkdir(parents=True, exist_ok=True)

    caminho_png = caminho_saida_dir / "fig_02_granulometria_RRB.png"
    caminho_pdf = caminho_saida_dir / "fig_02_granulometria_RRB.pdf"

    fig.savefig(caminho_png, dpi=300, bbox_inches="tight")
    fig.savefig(caminho_pdf, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Gráfico da granulometria salvo com sucesso em:\n  - {caminho_png}\n  - {caminho_pdf}")
    print(f"[INFO] Métricas de Aderência RRB: R² = {metricas['R2']:.4f}, RMSE = {metricas['RMSE']:.4f}, MAE = {metricas['MAE']:.4f}")

    return metricas


if __name__ == "__main__":
    projeto_raiz = Path(__file__).resolve().parents[3]
    dados_csv = projeto_raiz / "Base de dados" / "raw" / "granulometria_RRB.csv"
    saida_dir = projeto_raiz / "Código" / "outputs" / "etapa_0_2"

    gerar_grafico_granulometria(dados_csv, saida_dir)
