"""
Etapa 0.1: Visualização e Análise Exploratória dos Dados Cinéticos de Bancada
Disciplina: Laboratório de Operações e Processos (LOP - DEQ/UFMG)
Referência dos dados: Dissertação de Fabrício Bortot Coelho (2017), Apêndice A1.1, Tabela A1.4.

Objetivo:
- Carregar as séries temporais de conversão de zinco (X_Zn vs t).
- Gerar gráfico em grid 2x2 agrupado por razão molar eta (0.5, 1.0, 1.5, 3.1).
- Distinguir as curvas por concentração inicial de ácido (CA0).
- Salvar imagens em alta resolução (300 DPI) em PNG e PDF vetorial na pasta de saídas da Etapa 0.1.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def configurar_estilo_grafico() -> None:
    """Configura parâmetros visuais globais para gráficos de padrão científico."""
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


def gerar_grafico_cinetica(
    caminho_dados: Path,
    caminho_saida_dir: Path
) -> None:
    """Carrega os dados e plota as 16 curvas cinéticas organizadas por razão molar.

    Args:
        caminho_dados: Caminho para o arquivo cinetica_batelada_A1_4.csv.
        caminho_saida_dir: Diretório de destino para os gráficos e resumos da Etapa 0.1.
    """
    configurar_estilo_grafico()

    df = pd.read_csv(caminho_dados)

    # Identificar grupos de razão molar e concentrações de ácido
    etas = sorted(df["razao_molar_eta"].unique())
    ca0_vals = sorted(df["CA0_mol_L"].unique())

    # Paleta de cores e marcadores para cada CA0
    estilos = {
        0.1: {"color": "#1f77b4", "marker": "o", "label": "0,10 mol/L"},
        0.5: {"color": "#2ca02c", "marker": "s", "label": "0,50 mol/L"},
        1.0: {"color": "#ff7f0e", "marker": "^", "label": "1,00 mol/L"},
        1.5: {"color": "#d62728", "marker": "D", "label": "1,50 mol/L"},
    }

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(13, 10), sharex=True, sharey=True)
    axes = axes.flatten()

    for i, eta in enumerate(etas):
        ax = axes[i]
        df_eta = df[df["razao_molar_eta"] == eta]

        for ca0 in ca0_vals:
            df_curva = df_eta[df_eta["CA0_mol_L"] == ca0].sort_values("t_min")
            estilo = estilos[ca0]
            ax.plot(
                df_curva["t_min"],
                df_curva["XZn"],
                color=estilo["color"],
                marker=estilo["marker"],
                markersize=6,
                linewidth=1.8,
                label=f"C_A0 = {estilo['label']}",
                alpha=0.9
            )

        # Configurações de cada subplot
        if eta == 0.5:
            titulo = r"$\eta = 0,5$ (Ácido Limitante — Patamar $\approx 0,50$)"
            ax.axhline(0.5, color="gray", linestyle=":", linewidth=1.2, alpha=0.7)
            ax.annotate("Patamar Estequiométrico (X ≈ η)", xy=(7.0, 0.51), color="#555555", fontsize=9)
        elif eta == 1.0:
            titulo = r"$\eta = 1,0$ (Estequiométrico — Patamar $\approx 0,85 - 0,87$)"
            ax.axhline(0.86, color="gray", linestyle=":", linewidth=1.2, alpha=0.7)
        elif eta == 1.5:
            titulo = r"$\eta = 1,5$ (Excesso Moderado — Patamar $\approx 0,97$)"
            ax.axhline(0.97, color="gray", linestyle=":", linewidth=1.2, alpha=0.7)
        else:
            titulo = r"$\eta = 3,1$ (Grande Excesso — Conversão Total $X \approx 1,00$)"
            ax.axhline(1.0, color="gray", linestyle=":", linewidth=1.2, alpha=0.7)

        ax.set_title(titulo, pad=10, weight="bold")
        ax.set_xlim(-0.3, 15.5)
        ax.set_ylim(-0.02, 1.08)
        ax.set_xticks([0, 0.5, 1, 2, 3, 4, 5, 10, 15])
        ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc", loc="lower right")

    # Rótulos gerais
    for ax in axes[2:]:
        ax.set_xlabel("Tempo (min)", weight="semibold")
    for ax in [axes[0], axes[2]]:
        ax.set_ylabel("Conversão de Zinco - $X_{Zn}$ (-)", weight="semibold")

    fig.suptitle(
        "Lixiviação Descontínua em Bancada: Cinética de Conversão do Zinco por Razão Molar (η)\n"
        "(T = 40 °C, Agitação = 1000 rpm, Volume = 0,4 L)",
        weight="bold",
        y=0.99
    )

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Garantir criação do diretório de saída
    caminho_saida_dir.mkdir(parents=True, exist_ok=True)

    caminho_png = caminho_saida_dir / "fig_01_curvas_cineticas_bancada.png"
    caminho_pdf = caminho_saida_dir / "fig_01_curvas_cineticas_bancada.pdf"

    fig.savefig(caminho_png, dpi=300, bbox_inches="tight")
    fig.savefig(caminho_pdf, bbox_inches="tight")
    plt.close(fig)

    print(f"[OK] Gráfico salvo com sucesso em:\n  - {caminho_png}\n  - {caminho_pdf}")


if __name__ == "__main__":
    projeto_raiz = Path(__file__).resolve().parents[3]
    dados_csv = projeto_raiz / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    saida_dir = projeto_raiz / "Código" / "outputs" / "etapa_0_1"

    gerar_grafico_cinetica(dados_csv, saida_dir)
