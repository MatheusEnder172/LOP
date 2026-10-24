"""Script para gerar a Figura Comparativa entre a Malha Experimental e a Malha Densa de Treinamento.

Compara a amostragem discreta de bancada (8 instantes por ensaio, totalizando 128 pontos)
com a malha regular fina gerada para Machine Learning (61 instantes por ensaio, totalizando 976 pontos).
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def main() -> None:
    # Caminhos dos diretórios
    base_dir = Path(__file__).resolve().parents[3]
    processed_dir = base_dir / "Base de dados" / "processed"
    raw_dir = base_dir / "Base de dados" / "raw"
    output_dir = base_dir / "Código" / "outputs" / "etapa_2_1"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Carregar dados
    df_raw = pd.read_csv(raw_dir / "cinetica_batelada_A1_4.csv")
    df_targets_exp = pd.read_csv(processed_dir / "alvos_v_treinamento.csv")
    df_targets_dense = pd.read_csv(processed_dir / "alvos_v_treinamento_denso.csv")

    # Configuração de estilo visual científico
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.size"] = 10

    # Criar figura com GridSpec: parte superior com timeline e parte inferior com 2x2 painéis
    fig = plt.figure(figsize=(15, 12))
    gs = fig.add_gridspec(3, 2, height_ratios=[0.55, 1.0, 1.0], hspace=0.32, wspace=0.18)

    # =========================================================================
    # PAINEL SUPERIOR (SPAN NOS 2 QUADRANTES): RÉGUA TEMPORAL DE AMOSTRAGEM
    # =========================================================================
    ax_timeline = fig.add_subplot(gs[0, :])

    t_exp_nodes = np.array([0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0])
    t_dense_nodes = np.linspace(0.0, 15.0, 61)

    # Linha 1: Experimental (y = 1)
    y_exp = np.ones_like(t_exp_nodes) * 1.0
    ax_timeline.plot([-0.5, 15.5], [1.0, 1.0], color="#7f7f7f", linewidth=1.5, zorder=1)
    ax_timeline.scatter(
        t_exp_nodes,
        y_exp,
        color="#d62728",
        s=120,
        edgecolors="black",
        linewidths=1.5,
        zorder=3,
        label=f"Malha Experimental de Bancada (8 nós / ensaio — total 128 pontos)",
    )

    # Rótulos para os pontos experimentais
    for t_val in t_exp_nodes:
        offset_y = 0.18 if t_val in [0.5, 2.0, 4.0] else -0.22
        ax_timeline.text(
            t_val,
            1.0 + offset_y,
            f"{t_val:g}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#b2182b",
        )

    # Destacar o hiato de 10 minutos (posicionado entre as duas linhas de malha para evitar colisão)
    ax_timeline.annotate(
        "",
        xy=(15.0, 1.0),
        xytext=(5.0, 1.0),
        arrowprops=dict(arrowstyle="<->", color="#b2182b", lw=2.0),
    )
    ax_timeline.text(
        10.0,
        0.70,
        "Hiato sem Amostragem Física (Δt = 10 min)",
        ha="center",
        va="center",
        fontsize=9.5,
        fontweight="bold",
        color="#b2182b",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#ffebee", edgecolor="#ef9a9a", alpha=0.95),
    )

    # Linha 2: Malha Densa (y = 0.3)
    y_dense = np.ones_like(t_dense_nodes) * 0.3
    ax_timeline.plot([-0.5, 15.5], [0.3, 0.3], color="#7f7f7f", linewidth=1.5, zorder=1)
    ax_timeline.scatter(
        t_dense_nodes,
        y_dense,
        color="#1f77b4",
        s=35,
        edgecolors="#0d47a1",
        linewidths=0.8,
        alpha=0.85,
        zorder=3,
        label=f"Malha Densa Regular de ML (61 nós / ensaio — total 976 pontos, Δt = 0,25 min)",
    )

    ax_timeline.set_ylim(-0.15, 1.65)
    ax_timeline.set_xlim(-0.6, 15.8)
    ax_timeline.set_yticks([0.3, 1.0])
    ax_timeline.set_yticklabels(
        ["Malha Densa (ML)\n[61 instantes]", "Malha Experimental\n[8 instantes]"],
        fontweight="bold",
        fontsize=10.5,
    )
    ax_timeline.set_xlabel("Eixo Temporal de Reação, t (min)", fontsize=11, fontweight="bold")
    ax_timeline.set_title(
        "Painel (a) — Comparativo da Discretização Temporal: Amostragem de Bancada vs. Malha Fina Regular",
        fontsize=12,
        fontweight="bold",
        pad=10,
    )
    ax_timeline.grid(True, axis="x", linestyle="--", alpha=0.5)
    ax_timeline.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=9.5)

    # =========================================================================
    # PAINÉIS INFERIORES: CURVAS CINÉTICAS X_Zn(t) AGRUPADAS POR ETA (2x2)
    # =========================================================================
    axes_grid = [
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
        fig.add_subplot(gs[2, 0]),
        fig.add_subplot(gs[2, 1]),
    ]

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

    subtitles = [
        "Painel (b) — Razão Molar η = 0,5 (Déficit Estequiométrico Severo)",
        "Painel (c) — Razão Molar η = 1,0 (Proporção Estequiométrica Exata)",
        "Painel (d) — Razão Molar η = 1,5 (Excesso Estequiométrico Moderado)",
        "Painel (e) — Razão Molar η = 3,1 (Amplo Excesso de Ácido)",
    ]

    ca0_values = [0.10, 0.50, 1.00, 1.50]

    for idx, (ax, eta_val, subtitle) in enumerate(zip(axes_grid, eta_grupos, subtitles)):
        for ca0 in ca0_values:
            cor = color_map[ca0]
            marcador = marker_map[ca0]

            # Filtrar dados experimentais (8 pontos)
            sub_exp = df_targets_exp[
                np.isclose(df_targets_exp["razao_molar_eta"], eta_val)
                & np.isclose(df_targets_exp["CA0_mol_L"], ca0)
            ].sort_values("t_min")

            # Filtrar dados densos (61 pontos)
            sub_dense = df_targets_dense[
                np.isclose(df_targets_dense["razao_molar_eta"], eta_val)
                & np.isclose(df_targets_dense["CA0_mol_L"], ca0)
            ].sort_values("t_min")

            if len(sub_exp) == 0 or len(sub_dense) == 0:
                continue

            # 1. Trajetória contínua com nós da malha densa (61 pontos marcados)
            ax.plot(
                sub_dense["t_min"],
                sub_dense["XZn_reconstruido"],
                color=cor,
                linestyle="-",
                linewidth=1.8,
                alpha=0.85,
            )
            ax.scatter(
                sub_dense["t_min"],
                sub_dense["XZn_reconstruido"],
                color=cor,
                s=14,
                alpha=0.65,
                zorder=2,
            )

            # 2. Pontos experimentais discretos de bancada (8 pontos)
            ax.scatter(
                sub_exp["t_min"],
                sub_exp["XZn_exp"],
                color=cor,
                marker=marcador,
                s=65,
                edgecolors="black",
                linewidths=1.1,
                zorder=4,
                label=f"Exp ($C_{{A0}} = {ca0:.2f}\\ \\text{{mol/L}}$)",
            )

        ax.set_title(subtitle, fontsize=11, fontweight="bold", pad=8)
        ax.set_xlim(-0.4, 15.5)
        ax.set_ylim(-0.02, 1.08)
        ax.set_xlabel("Tempo, t (min)", fontsize=10.5, fontweight="bold")
        ax.set_ylabel("Conversão de Zinco, $X_{\\text{Zn}}$ (-)", fontsize=10.5, fontweight="bold")
        ax.grid(True, linestyle="--", alpha=0.55)
        ax.tick_params(axis="both", which="major", labelsize=10)

        # Legenda limpa
        ax.legend(
            loc="lower right" if eta_val != 3.1 else "center right",
            fontsize=8.5,
            frameon=True,
            framealpha=0.92,
            edgecolor="#cccccc",
            ncol=2,
        )

    # Anotação explicativa global no rodapé do gráfico
    fig.text(
        0.5,
        0.01,
        "Nota: Linhas contínuas com pequenos pontos representam a Malha Densa (61 instantes, Δt = 0,25 min; total 976 pontos). "
        "Marcadores destacados com contorno preto representam os Dados Experimentais Reais (8 instantes; total 128 pontos).",
        ha="center",
        fontsize=10,
        fontstyle="italic",
        color="#333333",
    )

    # Salvar nos formatos PNG (300 DPI) e PDF vetorial
    out_png = output_dir / "fig_06_comparacao_malha_experimental_vs_densa.png"
    out_pdf = output_dir / "fig_06_comparacao_malha_experimental_vs_densa.pdf"

    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    plt.close(fig)

    print(f"Gráfico gerado com sucesso em:")
    print(f"  PNG: {out_png}")
    print(f"  PDF: {out_pdf}")

if __name__ == "__main__":
    main()
