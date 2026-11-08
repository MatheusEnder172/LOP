"""Figuras ilustrativas da metodologia do modelo híbrido serial (relatório final LOP).

Gera, em 300 DPI (.png) e vetorial (.pdf), as figuras esquemáticas usadas na seção
de Materiais e Métodos do modelo híbrido serial:
- fig_hs_01_arquitetura_serial: arquitetura MLP -> nu(t) -> delta(t) -> PBM -> X_Zn, C_A
- fig_hs_02_fluxograma_etapas: etapas de desenvolvimento do modelo híbrido
- fig_hs_03_retracao_uniforme: retração uniforme das partículas e deslocamento da distribuição
- fig_hs_04_curva_conversao_delta: curva X_Zn(delta) pré-calculada pelo BatchPBMSolver

Uso: python gerar_figuras_hibrido_serial.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

FIG_DIR = Path(__file__).resolve().parent
CODIGO_DIR = FIG_DIR.parents[1] / "Código"
sys.path.insert(0, str(CODIGO_DIR))

from src.physics.granulometry import RosinRammlerBennet  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

# Paleta próxima à das figuras já presentes no documento (azul-marinho e azul-claro)
NAVY = "#1F3A5F"
BLUE = "#2E6DA4"
LIGHT = "#DCE8F4"
LIGHTER = "#EEF4FA"
TEAL = "#2A9D8F"
TEAL_LIGHT = "#D7EFEC"
ORANGE = "#D9822B"
ORANGE_LIGHT = "#FBE9D7"
GRAY = "#6B7280"

plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "mathtext.fontset": "dejavusans",
        "savefig.dpi": 300,
    }
)


def save(fig: plt.Figure, name: str) -> None:
    """Salva a figura em PNG (300 DPI) e PDF vetorial."""
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def box(ax, xy, w, h, text, fc=LIGHT, ec=NAVY, fs=11, bold=False, lw=1.4, color=NAVY):
    """Desenha uma caixa arredondada com texto centralizado."""
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
        fc=fc, ec=ec, lw=lw, zorder=2,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
        color=color, fontweight="bold" if bold else "normal", zorder=3, linespacing=1.35,
    )
    return patch


def arrow(ax, p0, p1, color=NAVY, lw=1.6, style="-|>", ls="-", rad=0.0, ms=16):
    """Desenha uma seta entre dois pontos."""
    ax.add_patch(
        FancyArrowPatch(
            p0, p1, arrowstyle=style, mutation_scale=ms, color=color, lw=lw,
            linestyle=ls, connectionstyle=f"arc3,rad={rad}", zorder=1,
        )
    )


def fig_arquitetura_serial() -> None:
    """Figura 1: arquitetura híbrida serial adotada."""
    fig, ax = plt.subplots(figsize=(11.5, 5.0))
    ax.set_xlim(0, 23)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Bloco de entradas
    box(ax, (0.2, 3.3), 3.2, 3.4,
        "Condições\noperacionais\n\n$C_{A0}$, $\\eta$\n\ntempo, $t$", fc=LIGHTER)

    # Bloco orientado por dados
    ax.add_patch(FancyBboxPatch((4.4, 1.3), 5.4, 7.0, boxstyle="round,pad=0.02,rounding_size=0.2",
                                fc=ORANGE_LIGHT, ec=ORANGE, lw=1.4, ls="--", zorder=0))
    ax.text(7.1, 8.75, "Modelo orientado por dados", ha="center", fontsize=11.5,
            color=ORANGE, fontweight="bold")
    # Mini-rede neural ilustrativa
    layers = [3, 4, 4, 1]
    xs = [5.3, 6.6, 7.9, 9.1]
    coords = []
    for n, x in zip(layers, xs):
        ys = np.linspace(5.0 - 0.7 * (n - 1), 5.0 + 0.7 * (n - 1), n) if n > 1 else [5.0]
        ys = np.array(ys) + 0.2
        coords.append([(x, y) for y in ys])
    for a, b in zip(coords[:-1], coords[1:]):
        for p in a:
            for q in b:
                ax.plot([p[0], q[0]], [p[1], q[1]], color=GRAY, lw=0.5, alpha=0.6, zorder=1)
    for i, layer in enumerate(coords):
        for (x, y) in layer:
            fc = TEAL_LIGHT if i == len(coords) - 1 else "white"
            ax.add_patch(Circle((x, y), 0.26, fc=fc, ec=NAVY, lw=1.1, zorder=2))
    ax.text(7.1, 1.8, "Rede neural MLP", ha="center", fontsize=11, color=NAVY)

    # Saída da rede
    box(ax, (10.7, 3.9), 2.6, 2.2, "Taxa de\nretração\n$\\nu(t)$", fc=TEAL_LIGHT, ec=TEAL, color=NAVY)

    # Bloco fenomenológico
    ax.add_patch(FancyBboxPatch((14.1, 0.5), 8.6, 9.0, boxstyle="round,pad=0.02,rounding_size=0.2",
                                fc="#F4F7FB", ec=BLUE, lw=1.4, ls="--", zorder=0))
    ax.text(18.4, 9.0, "Modelo fenomenológico", ha="center", fontsize=11.5,
            color=BLUE, fontweight="bold")
    box(ax, (14.6, 6.1), 7.6, 2.1, "", fc=LIGHT)
    ax.text(18.4, 7.65, "Integração no tempo", ha="center", va="center", fontsize=11, color=NAVY)
    ax.text(18.4, 6.75, "$\\delta(t)=\\int_{0}^{\\,t}\\ \\nu(\\tau)\\,d\\tau$", ha="center", va="center",
            fontsize=11, color=NAVY)
    box(ax, (14.6, 3.45), 7.6, 2.1,
        "Balanço populacional\n$X_{Zn}(t)=f\\,[\\delta(t),\\ \\bar{\\psi}_0(D)]$", fc=LIGHT)
    box(ax, (14.6, 0.8), 7.6, 2.1,
        "Balanço de ácido\n$C_A(t)=C_{A0}\\,[1-X_{Zn}(t)/\\eta]$", fc=LIGHT)

    arrow(ax, (3.4, 5.0), (4.9, 5.0))
    arrow(ax, (9.5, 5.0), (10.7, 5.0))
    arrow(ax, (13.3, 5.0), (14.6, 7.1))
    arrow(ax, (18.4, 6.1), (18.4, 5.55))
    arrow(ax, (18.4, 3.45), (18.4, 2.9))

    # Saídas finais
    ax.text(18.4, 0.15, "Saídas: $X_{Zn}(t)$ e $C_A(t)$", ha="center", fontsize=11, color=NAVY,
            fontweight="bold")
    save(fig, "fig_hs_01_arquitetura_serial")


def fig_fluxograma_etapas() -> None:
    """Figura 2: etapas de desenvolvimento do modelo híbrido serial (fluxo vertical)."""
    etapas = [
        (r"Dados experimentais", r"16 ensaios em batelada; $X_{Zn}(t)$ medida em 7 instantes com $t>0$", LIGHTER, NAVY),
        (r"Problema inverso", r"estimativa de $\nu(t)$ que reproduz a curva $X_{Zn}(t)$ de cada ensaio", ORANGE_LIGHT, ORANGE),
        (r"Base de dados de $\nu$", r"entradas $C_{A0}$, $\eta$ e $t$; saída $\nu$ em malha de 0,25 min", LIGHTER, NAVY),
        (r"Partição", r"13 ensaios para treino e 3 para teste cego (Ensaios 7, 8 e 14)", LIGHTER, NAVY),
        (r"Treinamento da MLP", r"busca de hiperparâmetros por validação cruzada e comitê de 10 redes", TEAL_LIGHT, TEAL),
        (r"Acoplamento serial", r"MLP $\rightarrow\ \nu(t)\ \rightarrow\ \delta(t)\ \rightarrow\ X_{Zn}(t),\ C_A(t)$", LIGHT, BLUE),
        (r"Avaliação", r"$R^2$, RMSE e MAE sobre $X_{Zn}$ nos conjuntos de treino e de teste cego", LIGHTER, NAVY),
    ]
    n = len(etapas)
    row_h, gap = 1.0, 0.55
    total_h = n * row_h + (n - 1) * gap
    fig, ax = plt.subplots(figsize=(10.0, (total_h + 0.6) / 2.0))
    ax.set_xlim(0, 20)
    ax.set_ylim(-0.3, total_h + 0.3)
    ax.axis("off")
    for i, (titulo, desc, fc, ec) in enumerate(etapas):
        y = total_h - (i + 1) * row_h - i * gap
        box(ax, (1.6, y), 18.0, row_h, "", fc=fc, ec=ec)
        ax.add_patch(Circle((0.75, y + row_h / 2), 0.42, fc=NAVY, ec=NAVY, zorder=3))
        ax.text(0.75, y + row_h / 2, str(i + 1), ha="center", va="center", color="white",
                fontsize=12, fontweight="bold", zorder=4)
        ax.text(2.0, y + row_h / 2, titulo, ha="left", va="center", fontsize=11.5,
                color=NAVY, fontweight="bold", zorder=3)
        ax.text(6.9, y + row_h / 2, desc, ha="left", va="center", fontsize=10.5,
                color="#1F2937", zorder=3)
        if i < n - 1:
            arrow(ax, (0.75, y + row_h / 2 - 0.44), (0.75, y - gap - row_h / 2 + 0.44), lw=1.3, ms=10)
    save(fig, "fig_hs_02_fluxograma_etapas")


def fig_retracao_uniforme() -> None:
    """Figura 3: retração uniforme das partículas e deslocamento da distribuição em número."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.6), gridspec_kw={"width_ratios": [1.15, 1]})

    # (a) Partículas de tamanhos diferentes perdendo a mesma espessura
    ax1.set_xlim(0, 12)
    ax1.set_ylim(-0.6, 5.2)
    ax1.set_aspect("equal")
    ax1.axis("off")
    diam = [0.6, 1.2, 2.0, 3.0]
    delta = 0.9
    xc = [1.0, 2.8, 5.3, 9.0]
    yc = 2.3
    for d, x in zip(diam, xc):
        ax1.add_patch(Circle((x, yc), d / 2, fc="none", ec=GRAY, lw=1.3, ls="--"))
        if d > delta:
            ax1.add_patch(Circle((x, yc), (d - delta) / 2, fc=LIGHT, ec=NAVY, lw=1.5))
        else:
            ax1.text(x, yc - d / 2 - 0.45, "dissolvida", ha="center", fontsize=9, color=ORANGE)
        ax1.text(x, yc + d / 2 + 0.3, f"$D_0$ = {d:.1f}", ha="center", fontsize=9.5, color=GRAY)
    # Destaque da retração na maior partícula
    x, d = xc[-1], diam[-1]
    ax1.annotate("", xy=(x + d / 2, yc), xytext=(x + (d - delta) / 2, yc),
                 arrowprops=dict(arrowstyle="<->", color=ORANGE, lw=1.4))
    ax1.text(x + d / 2 + 0.15, yc + 0.25, "$\\delta/2$", color=ORANGE, fontsize=11)
    ax1.text(6.0, -0.45, "– – –  diâmetro inicial $D_0$        ●  diâmetro no instante $t$: $D_0-\\delta(t)$",
             ha="center", fontsize=9.5, color=NAVY)
    ax1.set_title("(a) Todas as partículas perdem a mesma espessura", fontsize=12, color=NAVY, loc="left")

    # (b) Deslocamento da distribuição em número
    rrb = RosinRammlerBennet(use_number_density_d3=True)
    d_mesh, f0, _ = rrb.generate_mesh(d_min=0.01, d_max=297.0, n_points=5000)
    # Massa remanescente por faixa de diâmetro (D^3 f_n), normalizada pela massa inicial
    m_ini = np.trapezoid(d_mesh ** 3 * f0, d_mesh)
    for dl, ls, lab, col in [(0.0, "-", r"$t=0$", NAVY), (10.0, "--", r"$\delta$ = 10 µm", BLUE),
                             (25.0, ":", r"$\delta$ = 25 µm", TEAL)]:
        mask = d_mesh >= dl
        d_new = d_mesh[mask] - dl
        w_new = (d_new ** 3) * f0[mask]
        w_new = w_new / m_ini
        ax2.plot(d_new, w_new, ls, color=col, lw=2.0, label=lab)
    ax2.set_xlim(0, 160)
    ax2.set_ylim(bottom=0)
    ax2.set_xlabel("Diâmetro da partícula, $D$ (µm)")
    ax2.set_ylabel("Massa remanescente por faixa de\ndiâmetro (fração da inicial, µm$^{-1}$)")
    ax2.legend(frameon=False, fontsize=10)
    ax2.annotate("partículas finas são\nas primeiras a dissolver", xy=(10, 0.0025), xytext=(45, 0.0135),
                 fontsize=10, color=NAVY, arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.2))
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.set_title(r"(b) Massa remanescente após a retração $\delta$", fontsize=12, color=NAVY, loc="left")
    fig.tight_layout()
    save(fig, "fig_hs_03_retracao_uniforme")


def fig_curva_conversao_delta() -> None:
    """Figura 4: curva X_Zn(delta) pré-calculada pelo BatchPBMSolver (base em número)."""
    solver = BatchPBMSolver(granulometry=RosinRammlerBennet(use_number_density_d3=True))
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    delta = np.linspace(0, 120, 600)
    ax.plot(delta, solver.compute_conversion_from_delta(delta), color=NAVY, lw=2.2,
            label="Interpolação PCHIP")
    sel = solver.delta_grid <= 120
    ax.plot(solver.delta_grid[sel][::6], solver.x_grid[sel][::6], "o", ms=4.5, mfc="white",
            mec=BLUE, mew=1.2, label="Nós pré-calculados (Eq. de $X_{Zn}(\\delta)$)")
    ax.set_xlabel("Retração diametral acumulada, $\\delta$ (µm)")
    ax.set_ylabel("Conversão de zinco, $X_{Zn}$ (–)")
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 1.02)
    ax.grid(True, ls=":", alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower right", fontsize=10)
    fig.tight_layout()
    save(fig, "fig_hs_04_curva_conversao_delta")


def fig_problema_inverso() -> None:
    """Figura 5: ciclo de otimização do problema inverso para um ensaio."""
    fig, ax = plt.subplots(figsize=(11.5, 5.6))
    ax.set_xlim(0, 23)
    ax.set_ylim(0, 11.2)
    ax.axis("off")

    box(ax, (0.3, 7.6), 4.6, 2.6, "Parâmetros\n$\\theta=(a_1,b_1,a_2,b_2,c)$\n6 estimativas iniciais", fc=ORANGE_LIGHT, ec=ORANGE)
    box(ax, (6.1, 7.6), 4.8, 2.6, "Taxa de retração\n$\\nu(t;\\theta)$\n(bi-exponencial)", fc=TEAL_LIGHT, ec=TEAL)
    box(ax, (12.1, 7.6), 4.8, 2.6, "Retração acumulada\n$\\delta(t_k)$\n(regra do trapézio)", fc=LIGHT)
    box(ax, (18.1, 7.6), 4.6, 2.6, "Conversão\n$X_{Zn}(t_k)=X_{Zn}(\\delta_k)$\n(curva pré-calculada)", fc=LIGHT)
    box(ax, (18.1, 3.2), 4.6, 2.6, "Dados do ensaio\n$X_{Zn}^{exp}(t_i)$\n7 instantes com $t>0$", fc=LIGHTER)
    box(ax, (10.6, 3.2), 6.4, 2.6, "Função objetivo\n$J(\\theta)$ = erro quadrático\n+ penalizações", fc="#F3F4F6", ec=NAVY)
    box(ax, (3.0, 3.2), 6.4, 2.6, "Otimizador L-BFGS-B\n(com limites para $\\theta$)\natualiza $\\theta$", fc=ORANGE_LIGHT, ec=ORANGE)

    arrow(ax, (4.9, 8.9), (6.1, 8.9))
    arrow(ax, (10.9, 8.9), (12.1, 8.9))
    arrow(ax, (16.9, 8.9), (18.1, 8.9))
    arrow(ax, (20.4, 7.6), (16.2, 5.8), rad=0.0)
    arrow(ax, (18.1, 4.5), (17.0, 4.5))
    arrow(ax, (10.6, 4.5), (9.4, 4.5))
    arrow(ax, (6.2, 5.8), (2.6, 7.6))
    ax.text(2.2, 6.5, "repetir até\na convergência", ha="center", fontsize=10, color=GRAY, style="italic")
    ax.text(13.6, 2.35, "ao convergir", ha="left", fontsize=10, color=GRAY, style="italic")
    box(ax, (5.0, 0.2), 13.0, 1.5,
        r"Saída: $\theta^*$ do ensaio $\rightarrow\ \nu(t)$, $\delta(t)$ e $X_{Zn}(t)$ nas malhas experimental e densa",
        fc=TEAL_LIGHT, ec=TEAL, fs=10.5)
    arrow(ax, (13.8, 3.2), (12.6, 1.7))
    save(fig, "fig_hs_05_problema_inverso")


def fig_parametrizacao_biexponencial() -> None:
    """Figura 6: forma da parametrização bi-exponencial (valores ilustrativos)."""
    a1, b1, a2, b2, c = 120.0, 4.0, 15.0, 0.5, 0.01
    t = np.linspace(0.0, 15.0, 1500)
    rapido = a1 * np.exp(-b1 * t)
    lento = a2 * np.exp(-b2 * t)
    nu = rapido + lento + c
    delta = np.concatenate([[0.0], np.cumsum(0.5 * (nu[1:] + nu[:-1]) * np.diff(t))])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.4))
    ax1.semilogy(t, nu, color=NAVY, lw=2.4, label="$\\nu(t)$ total")
    ax1.semilogy(t, rapido, "--", color=ORANGE, lw=1.8, label="$a_1 e^{-b_1 t}$ (etapa rápida)")
    ax1.semilogy(t, lento, "-.", color=TEAL, lw=1.8, label="$a_2 e^{-b_2 t}$ (etapa lenta)")
    ax1.axhline(c, color=GRAY, ls=":", lw=1.4, label="$c$ (taxa residual)")
    ax1.set_ylim(1e-3, 300)
    ax1.set_xlim(0, 15)
    ax1.set_xlabel("Tempo, $t$ (min)")
    ax1.set_ylabel("Taxa de retração, $\\nu$ (µm/min)")
    ax1.legend(frameon=False, fontsize=9.5, loc="upper right")
    ax1.set_title("(a) Componentes da taxa de retração", fontsize=12, color=NAVY, loc="left")

    ax2.plot(t, delta, color=NAVY, lw=2.4)
    ax2.set_xlim(0, 15)
    ax2.set_ylim(bottom=0)
    ax2.set_xlabel("Tempo, $t$ (min)")
    ax2.set_ylabel("Retração acumulada, $\\delta$ (µm)")
    ax2.set_title("(b) Retração acumulada $\\delta(t)$", fontsize=12, color=NAVY, loc="left")
    for ax in (ax1, ax2):
        ax.grid(True, ls=":", alpha=0.5)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_hs_06_parametrizacao_biexponencial")


def fig_malhas_temporais() -> None:
    """Figura 7: instantes experimentais e malha densa usada na integração e no treinamento."""
    t_exp = np.array([0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 15.0])
    t_dense = np.linspace(0.25, 15.0, 60)
    fig, ax = plt.subplots(figsize=(11.0, 2.6))
    ax.hlines(1.0, 0, 15.3, color=GRAY, lw=1.0)
    ax.hlines(0.0, 0, 15.3, color=GRAY, lw=1.0)
    ax.plot(t_dense, np.ones_like(t_dense), "|", ms=14, mew=1.4, color=BLUE)
    ax.plot(t_exp, np.zeros_like(t_exp), "o", ms=9, mfc=ORANGE, mec=NAVY, mew=1.0)
    ax.plot([0], [0], "s", ms=8, mfc="white", mec=NAVY, mew=1.2)
    ax.plot([0], [1], "s", ms=8, mfc="white", mec=NAVY, mew=1.2)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Instantes\nexperimentais (7)", "Malha densa\n(60 nós, $\\Delta t$ = 0,25 min)"])
    ax.set_xticks([0, 0.5, 1, 2, 3, 4, 5, 15])
    ax.set_xlim(-0.3, 15.5)
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlabel("Tempo, $t$ (min)")
    ax.text(0.15, -0.45, "$t=0$: condição inicial imposta ($X_{Zn}=0$, $\\delta=0$)", fontsize=9.5, color=NAVY)
    ax.annotate("sem medições entre 5 e 15 min", xy=(10.0, 0.0), xytext=(8.0, 0.45), fontsize=9.5,
                color=GRAY, arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    save(fig, "fig_hs_07_malhas_temporais")

SPLITS_DIR = FIG_DIR.parents[1] / "Base de dados" / "processed" / "splits"


def fig_particao_dobras() -> None:
    """Figura 8: partição dos ensaios no plano C_A0 x eta e dobras da validação cruzada."""
    import json

    import pandas as pd

    cond = (
        pd.read_csv(FIG_DIR.parents[1] / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv")
        .groupby("ensaio")[["CA0_mol_L", "razao_molar_eta"]].first()
    )
    folds = json.loads((SPLITS_DIR / "cv_folds_info.json").read_text(encoding="utf-8"))
    fold_of = {e: f["fold"] for f in folds for e in f["val_ensaios"]}
    teste = [7, 8, 14]
    cores = {1: BLUE, 2: TEAL, 3: "#7B5EA7", 4: "#C2185B"}
    eta_pos = {0.5: 0, 1.0: 1, 1.5: 2, 3.1: 3}
    ca_pos = {0.1: 0, 0.5: 1, 1.0: 2, 1.5: 3}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 4.9), gridspec_kw={"width_ratios": [1, 1.25]})
    for ens, row in cond.iterrows():
        x, y = ca_pos[round(row.CA0_mol_L, 2)], eta_pos[round(row.razao_molar_eta, 2)]
        if ens in teste:
            ax1.plot(x, y, "*", ms=22, mfc=ORANGE, mec=NAVY, mew=1.0, zorder=3)
        else:
            ax1.plot(x, y, "o", ms=17, mfc=cores[fold_of[ens]], mec=NAVY, mew=1.0, alpha=0.9, zorder=3)
        ax1.text(x, y, str(ens), ha="center", va="center", fontsize=8.5, color="white",
                 fontweight="bold", zorder=4)
    ax1.set_xticks(range(4), ["0,10", "0,50", "1,00", "1,50"])
    ax1.set_yticks(range(4), ["0,5", "1,0", "1,5", "3,1"])
    ax1.set_xlim(-0.6, 3.6)
    ax1.set_ylim(-0.6, 3.6)
    ax1.set_xlabel("Concentração inicial de ácido, $C_{A0}$ (mol/L)")
    ax1.set_ylabel("Razão molar estequiométrica, $\\eta$ (–)")
    ax1.grid(True, ls=":", alpha=0.5)
    ax1.set_title("(a) Ensaios de treino e de teste cego", fontsize=12, color=NAVY, loc="left")
    handles = [plt.Line2D([], [], marker="*", ls="", ms=14, mfc=ORANGE, mec=NAVY, label="Teste cego")]
    handles += [plt.Line2D([], [], marker="o", ls="", ms=10, mfc=cores[k], mec=NAVY,
                           label=f"Treino – validação na dobra {k}") for k in range(1, 5)]
    ax1.legend(handles=handles, frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(1.0, 1.0))

    # (b) esquema das dobras
    treino = sorted(fold_of)
    ax2.set_xlim(-2.8, len(treino) + 0.2)
    ax2.set_ylim(-0.9, 4.4)
    ax2.axis("off")
    for j, ens in enumerate(treino):
        ax2.text(j + 0.5, 4.05, str(ens), ha="center", fontsize=9.5, color=NAVY)
    ax2.text(-1.4, 4.05, "Ensaio", ha="center", fontsize=9.5, color=NAVY, fontweight="bold")
    for i, f in enumerate(folds):
        y = 3 - i
        ax2.text(-1.4, y + 0.4, f"Dobra {f['fold']}", ha="center", va="center", fontsize=10, color=NAVY)
        for j, ens in enumerate(treino):
            val = ens in f["val_ensaios"]
            ax2.add_patch(FancyBboxPatch((j + 0.06, y + 0.08), 0.88, 0.64,
                                         boxstyle="round,pad=0.0,rounding_size=0.08",
                                         fc=cores[f["fold"]] if val else LIGHT, ec=NAVY, lw=0.8))
    ax2.add_patch(FancyBboxPatch((0.5, -0.75), 0.6, 0.4, boxstyle="round,pad=0,rounding_size=0.05", fc=LIGHT, ec=NAVY, lw=0.8))
    ax2.text(1.3, -0.55, "ajuste dos pesos", va="center", fontsize=9.5)
    ax2.add_patch(FancyBboxPatch((6.0, -0.75), 0.6, 0.4, boxstyle="round,pad=0,rounding_size=0.05", fc=GRAY, ec=NAVY, lw=0.8))
    ax2.text(6.8, -0.55, "validação (ensaios inteiros)", va="center", fontsize=9.5)
    ax2.set_title("(b) Validação cruzada por ensaio (4 dobras)", fontsize=12, color=NAVY, loc="left")
    fig.tight_layout()
    save(fig, "fig_hs_08_particao_dobras")


def fig_distribuicao_alvo() -> None:
    """Figura 9: distribuição da taxa de retração no conjunto de treino, em escala linear e log1p."""
    import pandas as pd

    nu = pd.read_csv(SPLITS_DIR / "train_dense.csv")["abs_v_alvo_um_min"].to_numpy()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 3.9))
    ax1.hist(nu, bins=40, color=BLUE, ec="white", lw=0.5)
    ax1.set_xlabel("Taxa de retração, $\\nu$ (µm/min)")
    ax1.set_ylabel("Número de registros")
    ax1.set_title("(a) Escala original", fontsize=12, color=NAVY, loc="left")
    ax2.hist(np.log1p(nu), bins=40, color=TEAL, ec="white", lw=0.5)
    ax2.set_xlabel(r"$\ln(1+\nu)$ (–)")
    ax2.set_ylabel("Número de registros")
    ax2.set_title("(b) Após a transformação logarítmica", fontsize=12, color=NAVY, loc="left")
    for ax in (ax1, ax2):
        ax.grid(True, ls=":", alpha=0.5, axis="y")
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_hs_09_distribuicao_alvo")


def fig_fluxo_preparacao() -> None:
    """Figura 10: fluxo de preparação dos dados, com o isolamento do conjunto de teste cego."""
    fig, ax = plt.subplots(figsize=(11.0, 7.4))
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 14.8)
    ax.axis("off")

    box(ax, (5.0, 12.6), 12.0, 1.8,
        r"Base de dados na malha regular" "\n" r"16 ensaios $\times$ 60 instantes = 960 registros ($C_{A0}$, $\eta$, $t$, $\nu$)",
        fc=LIGHTER, fs=10.5)
    box(ax, (5.0, 10.2), 12.0, 1.5, "Partição por ensaios inteiros", fc=LIGHT, fs=11, bold=True)
    arrow(ax, (11.0, 12.6), (11.0, 11.7))

    # Coluna do treino
    ax.add_patch(FancyBboxPatch((0.3, 0.3), 11.2, 9.2, boxstyle="round,pad=0.02,rounding_size=0.2",
                                fc="#F4F7FB", ec=BLUE, lw=1.3, ls="--", zorder=0))
    ax.text(5.9, 9.0, "Conjunto de treino", ha="center", fontsize=11.5, color=BLUE, fontweight="bold")
    box(ax, (0.9, 6.9), 10.0, 1.6, "13 ensaios | 780 registros\n(1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 15 e 16)", fc=LIGHT, fs=10.5)
    box(ax, (0.9, 4.4), 10.0, 1.8,
        r"Cálculo de $\mu_j$ e $\sigma_j$ e padronização das entradas" "\n" r"Transformação da saída: $y=\ln(1+\nu)$",
        fc=TEAL_LIGHT, ec=TEAL, fs=10.5)
    box(ax, (0.9, 2.0), 10.0, 1.7, "Validação cruzada por ensaio (4 dobras)\nescolha da configuração e treinamento da MLP",
        fc=ORANGE_LIGHT, ec=ORANGE, fs=10.5)
    box(ax, (3.4, 0.6), 5.0, 1.0, "Modelo treinado", fc=LIGHT, fs=10.5, bold=True)
    arrow(ax, (8.0, 10.2), (5.9, 9.55))
    arrow(ax, (5.9, 6.9), (5.9, 6.2))
    arrow(ax, (5.9, 4.4), (5.9, 3.7))
    arrow(ax, (5.9, 2.0), (5.9, 1.6))

    # Coluna do teste
    ax.add_patch(FancyBboxPatch((12.4, 0.3), 9.3, 9.2, boxstyle="round,pad=0.02,rounding_size=0.2",
                                fc="#FDF6EE", ec=ORANGE, lw=1.3, ls="--", zorder=0))
    ax.text(17.05, 9.0, "Conjunto de teste cego (isolado)", ha="center", fontsize=11.5, color=ORANGE,
            fontweight="bold")
    box(ax, (13.0, 6.9), 8.1, 1.6, "3 ensaios | 180 registros\n(7, 8 e 14)", fc=ORANGE_LIGHT, ec=ORANGE, fs=10.5)
    box(ax, (13.0, 4.4), 8.1, 1.8, "Padronização com $\\mu_j$ e $\\sigma_j$\ndo treino (sem recálculo)",
        fc="white", ec=ORANGE, fs=10.5)
    box(ax, (13.0, 0.6), 8.1, 1.7, "Avaliação final\n(uma única vez, após o treinamento)", fc="white", ec=ORANGE, fs=10.5)
    arrow(ax, (14.0, 10.2), (17.05, 9.55))
    arrow(ax, (17.05, 6.9), (17.05, 6.2))
    arrow(ax, (17.05, 4.4), (17.05, 2.3))
    # Passagem de parâmetros e do modelo
    arrow(ax, (10.9, 5.3), (13.0, 5.3), color=TEAL)
    ax.text(11.95, 5.55, "$\\mu_j$, $\\sigma_j$", ha="center", fontsize=9.5, color=TEAL)
    arrow(ax, (8.4, 1.1), (13.0, 1.1), color=NAVY)
    save(fig, "fig_hs_10_fluxo_preparacao")


def fig_arquitetura_mlp() -> None:
    """Figura 11: arquitetura da MLP (entrada em ln t, três blocos residuais e saída não negativa)."""
    fig, ax = plt.subplots(figsize=(13.5, 7.6))
    ax.set_xlim(0, 27)
    ax.set_ylim(0, 15)
    ax.axis("off")

    # Linha principal
    w, h, y0 = 3.2, 3.0, 10.6
    etapas = [
        ("Entradas\npadronizadas\n\n$\\tilde{C}_{A0}$, $\\tilde{\\eta}$, $\\tilde{t}$", LIGHTER, NAVY),
        ("Transformação\ntemporal\n\n$\\tilde{t}\\ \\rightarrow\\ \\tilde{\\tau}$\n(ln $t$ padronizado)", ORANGE_LIGHT, ORANGE),
        ("Bloco\nresidual 1\n\n3 → 90", LIGHT, BLUE),
        ("Bloco\nresidual 2\n\n90 → 45", LIGHT, BLUE),
        ("Bloco\nresidual 3\n\n45 → 22", LIGHT, BLUE),
        ("Camada de\nsaída\n\nlinear 22 → 1\n+ Softplus", TEAL_LIGHT, TEAL),
        ("Taxa de\nretração\n\n$\\hat{y}=\\ln(1+\\nu)$\n$\\nu=e^{\\hat{y}}-1$", TEAL_LIGHT, TEAL),
    ]
    xs = [0.3 + i * (w + 0.62) for i in range(len(etapas))]
    for x, (txt, fc, ec) in zip(xs, etapas):
        box(ax, (x, y0), w, h, txt, fc=fc, ec=ec, fs=10.2)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        arrow(ax, (x0 + w, y0 + h / 2), (x1, y0 + h / 2), lw=1.4, ms=12)
    yc = y0 + h + 0.3
    ax.plot([xs[2], xs[2], xs[4] + w, xs[4] + w], [yc - 0.15, yc, yc, yc - 0.15], color=BLUE, lw=1.2)
    ax.text(xs[3] + w / 2, yc + 0.3, "Camadas ocultas (ativação GELU, dropout de 0,125)",
            ha="center", fontsize=10.5, color=BLUE, fontweight="bold")

    # Detalhe de um bloco residual
    ax.add_patch(FancyBboxPatch((0.6, 0.5), 25.8, 7.6, boxstyle="round,pad=0.02,rounding_size=0.2",
                                fc="#F7F9FC", ec=BLUE, lw=1.3, ls="--", zorder=0))
    ax.text(1.0, 7.55, "Detalhe de um bloco residual", ha="left", fontsize=11, color=BLUE, fontweight="bold")
    for xb in (xs[2], xs[3], xs[4]):
        ax.plot([xb + w / 2, 13.5], [y0, 8.15], color=BLUE, lw=0.9, ls=":", zorder=0)

    yb, hb = 4.6, 1.6
    ax.text(1.4, yb + hb / 2, "$\\mathbf{h}_{l-1}$", ha="center", va="center", fontsize=13, color=NAVY)
    ramo = [("Linear\n$\\mathbf{W}_{l,1}$, $\\mathbf{b}_{l,1}$", 3.6), ("GELU", 2.9), ("Dropout", 3.1),
            ("Linear\n$\\mathbf{W}_{l,2}$, $\\mathbf{b}_{l,2}$", 3.6), ("× $\\alpha_l$", 2.5)]
    x = 2.6
    pos = []
    for txt, wb in ramo:
        box(ax, (x, yb), wb, hb, txt, fc="white", ec=BLUE, fs=10)
        pos.append((x, wb))
        x += wb + 0.9
    for (xa, wa), (xc, _) in zip(pos[:-1], pos[1:]):
        arrow(ax, (xa + wa, yb + hb / 2), (xc, yb + hb / 2), lw=1.2, ms=10)
    arrow(ax, (1.85, yb + hb / 2), (2.6, yb + hb / 2), lw=1.2, ms=10)
    xs_soma = x + 0.4
    ax.add_patch(Circle((xs_soma, yb + hb / 2), 0.42, fc="white", ec=NAVY, lw=1.4, zorder=2))
    ax.text(xs_soma, yb + hb / 2, "+", ha="center", va="center", fontsize=16, color=NAVY, zorder=3)
    xa, wa = pos[-1]
    arrow(ax, (xa + wa, yb + hb / 2), (xs_soma - 0.42, yb + hb / 2), lw=1.2, ms=10)
    arrow(ax, (xs_soma + 0.42, yb + hb / 2), (xs_soma + 1.6, yb + hb / 2), lw=1.2, ms=10)
    ax.text(xs_soma + 2.2, yb + hb / 2, "$\\mathbf{h}_{l}$", ha="center", va="center", fontsize=13, color=NAVY)
    ax.text((2.6 + pos[-1][0] + pos[-1][1]) / 2, yb + hb + 0.45, "ramo não linear, $\\mathbf{F}_l(\\mathbf{h}_{l-1})$",
            ha="center", fontsize=10.5, color=BLUE)

    # Atalho (projeção linear)
    yp = 1.4
    box(ax, (10.0, yp), 7.0, 1.5, "Projeção linear, sem viés: $\\mathbf{P}_l\\,\\mathbf{h}_{l-1}$",
        fc=ORANGE_LIGHT, ec=ORANGE, fs=10.2)
    ax.plot([1.95, 1.95], [yb + hb / 2 - 0.25, yp + 0.75], color=ORANGE, lw=1.3)
    arrow(ax, (1.95, yp + 0.75), (10.0, yp + 0.75), color=ORANGE, lw=1.3, ms=10)
    ax.plot([17.0, xs_soma], [yp + 0.75, yp + 0.75], color=ORANGE, lw=1.3)
    arrow(ax, (xs_soma, yp + 0.75), (xs_soma, yb + hb / 2 - 0.42), color=ORANGE, lw=1.3, ms=10)
    ax.text(6.0, yp + 1.05, "atalho (conexão residual)", ha="center", fontsize=10, color=ORANGE)
    save(fig, "fig_hs_11_arquitetura_mlp")


def fig_funcoes_rede() -> None:
    """Figura 12: (a) ativação GELU comparada à ReLU; (b) camada de saída Softplus e taxa resultante."""
    from math import erf, sqrt

    z = np.linspace(-4, 4, 400)
    phi = 0.5 * (1 + np.array([erf(v / sqrt(2)) for v in z]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.0, 4.6))
    a1.plot(z, np.maximum(z, 0), color=GRAY, lw=1.8, ls="--", label="ReLU, $\\max(0,z)$")
    a1.plot(z, z * phi, color=BLUE, lw=2.4, label="GELU, $z\\,\\Phi(z)$")
    a1.axhline(0, color="black", lw=0.6)
    a1.axvline(0, color="black", lw=0.6)
    a1.set_xlabel("Entrada do neurônio, $z$")
    a1.set_ylabel("Saída do neurônio")
    a1.set_title("(a) Função de ativação das camadas ocultas", fontsize=12, color=NAVY, loc="left")
    a1.grid(ls="--", alpha=0.5)
    a1.legend(loc="upper left")
    a1.annotate("curva suave,\nsem quina em $z=0$", xy=(-0.05, -0.02), xytext=(-3.6, 1.3), fontsize=10, color=NAVY,
                arrowprops={"arrowstyle": "->", "color": NAVY})

    zz = np.linspace(-6, 5, 400)
    y = np.log1p(np.exp(zz))
    a2.plot(zz, y, color=TEAL, lw=2.4, label="$\\hat{y}=\\ln(1+e^{z})$ (Softplus)")
    a2.plot(zz, np.maximum(zz, 0), color=GRAY, lw=1.2, ls=":")
    a2.set_xlabel("Saída da última camada linear, $z$")
    a2.set_ylabel("$\\hat{y}=\\ln(1+\\nu)$", color=TEAL)
    a2.set_ylim(0, 5.3)
    a2.grid(ls="--", alpha=0.5)
    a3 = a2.twinx()
    a3.plot(zz, np.expm1(y), color=ORANGE, lw=2.0, ls="--", label="$\\nu=e^{\\hat{y}}-1$")
    a3.set_yscale("log")
    a3.set_ylim(1e-3, 3e2)
    a3.set_ylabel("$\\nu$ (µm/min), escala log", color=ORANGE)
    a2.set_title("(b) Camada de saída e recuperação da taxa", fontsize=12, color=NAVY, loc="left")
    l1, n1 = a2.get_legend_handles_labels()
    l2, n2 = a3.get_legend_handles_labels()
    a2.legend(l1 + l2, n1 + n2, loc="upper left")
    fig.tight_layout()
    save(fig, "fig_hs_12_funcoes_rede")


def fig_treinamento_mlp() -> None:
    """Figura 13: (a) ciclo de treinamento por mini-lotes; (b) taxa de aprendizado ao longo das épocas."""
    fig = plt.figure(figsize=(13.5, 6.4))
    ax = fig.add_axes([0.0, 0.0, 0.56, 1.0])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 16)
    ax.axis("off")
    passos = [
        ("Início da época $e$: embaralhar os 780 registros de treino", LIGHTER, NAVY),
        ("Separar um lote de 16 registros", LIGHTER, NAVY),
        ("Propagação direta: $\\hat{y}_i$ para cada registro do lote", LIGHT, BLUE),
        ("Perda: $\\mathcal{L}=\\frac{1}{B}\\sum_i\\,(\\hat{y}_i-y_i)^2$", LIGHT, BLUE),
        ("Retropropagação: gradientes $\\partial\\mathcal{L}/\\partial\\boldsymbol{\\theta}$", LIGHT, BLUE),
        ("Atualização dos parâmetros pelo AdamW", TEAL_LIGHT, TEAL),
        ("Ajuste da taxa de aprendizado (cosseno)", ORANGE_LIGHT, ORANGE),
    ]
    bw, bh, x0 = 10.4, 1.35, 1.2
    ys = [14.2 - i * 2.05 for i in range(len(passos))]
    for y, (txt, fc, ec) in zip(ys, passos):
        box(ax, (x0, y), bw, bh, txt, fc=fc, ec=ec, fs=10.5)
    for ya, yc in zip(ys[:-1], ys[1:]):
        arrow(ax, (x0 + bw / 2, ya), (x0 + bw / 2, yc + bh), lw=1.3, ms=11)
    # Laço dos lotes (volta da atualização para "separar um lote")
    xr = x0 + bw + 0.55
    ax.plot([x0 + bw, xr], [ys[5] + bh / 2, ys[5] + bh / 2], color=TEAL, lw=1.3)
    ax.plot([xr, xr], [ys[5] + bh / 2, ys[1] + bh / 2], color=TEAL, lw=1.3)
    arrow(ax, (xr, ys[1] + bh / 2), (x0 + bw, ys[1] + bh / 2), color=TEAL, lw=1.3, ms=11)
    ax.text(xr + 0.15, (ys[1] + ys[5]) / 2 + bh / 2, "próximo lote\n(49 lotes\npor época)", fontsize=9.5,
            color=TEAL, va="center")
    # Laço das épocas (volta do ajuste da taxa para o início)
    xl = x0 - 0.55
    ax.plot([x0, xl], [ys[6] + bh / 2, ys[6] + bh / 2], color=ORANGE, lw=1.3)
    ax.plot([xl, xl], [ys[6] + bh / 2, ys[0] + bh / 2], color=ORANGE, lw=1.3)
    arrow(ax, (xl, ys[0] + bh / 2), (x0, ys[0] + bh / 2), color=ORANGE, lw=1.3, ms=11)
    ax.text(xl - 0.12, (ys[0] + ys[6]) / 2 + bh / 2, "próxima época\n(até 928)", fontsize=9.5, color=ORANGE,
            va="center", ha="right", rotation=90)
    ax.text(x0 + bw / 2, 0.25, "(a) Ciclo de treinamento por mini-lotes", ha="center", fontsize=12, color=NAVY)

    a2 = fig.add_axes([0.63, 0.14, 0.35, 0.74])
    E, lr0, lr_min = 928, 4.078e-3, 1e-5
    e = np.arange(0, E + 1)
    lr = lr_min + 0.5 * (lr0 - lr_min) * (1 + np.cos(np.pi * e / E))
    a2.plot(e, lr * 1e3, color=ORANGE, lw=2.2)
    a2.set_xlabel("Época, $e$")
    a2.set_ylabel("Taxa de aprendizado ($\\times 10^{-3}$)")
    a2.set_xlim(0, E)
    a2.set_ylim(0, 4.5)
    a2.grid(ls="--", alpha=0.5)
    a2.annotate(f"$\\gamma_0$ = {lr0 * 1e3:.2f}".replace(".", ",") + "$\\times 10^{-3}$", xy=(0, lr0 * 1e3),
                xytext=(180, 4.25), fontsize=10, color=NAVY, arrowprops={"arrowstyle": "->", "color": NAVY})
    a2.annotate("$\\gamma_{min}$ = $10^{-5}$", xy=(E, lr_min * 1e3), xytext=(640, 1.6), fontsize=10, color=NAVY,
                arrowprops={"arrowstyle": "->", "color": NAVY})
    a2.set_title("(b) Redução da taxa de aprendizado", fontsize=12, color=NAVY, loc="left")
    save(fig, "fig_hs_13_treinamento_mlp")


def fig_avaliacao_configuracao() -> None:
    """Figura 14: avaliação de uma configuração da rede pelo RMSE de X_Zn fora da dobra."""
    fig, ax = plt.subplots(figsize=(13.0, 7.4))
    ax.set_xlim(0, 26)
    ax.set_ylim(0, 15)
    ax.axis("off")
    box(ax, (0.3, 6.2), 3.6, 2.6, "Configuração\ncandidata\n(hiperparâmetros)", fc=LIGHTER, fs=10.5)
    # laço das sementes (externo) e das dobras (interno)
    ax.add_patch(FancyBboxPatch((4.7, 0.6), 15.6, 13.6, boxstyle="round,pad=0.02,rounding_size=0.2",
                                fc="#F7F9FC", ec=GRAY, lw=1.3, ls="--", zorder=0))
    ax.text(5.0, 13.6, "Para cada semente $s$ (3 na busca; 10 nos finalistas)", fontsize=10.5, color=GRAY,
            fontweight="bold")
    ax.add_patch(FancyBboxPatch((5.3, 1.2), 14.4, 11.8, boxstyle="round,pad=0.02,rounding_size=0.2",
                                fc="white", ec=BLUE, lw=1.3, ls="--", zorder=0))
    ax.text(5.6, 12.4, "Para cada dobra $k$ = 1, ..., 4", fontsize=10.5, color=BLUE, fontweight="bold")
    passos = [
        ("Treino com os ensaios de ajuste da dobra (9 ou 10 ensaios)\n"
         "(com parada antecipada, 2 deles ficam reservados para acompanhamento)", LIGHT, BLUE),
        ("Previsão de $\\hat{\\nu}(t)$ para os ensaios de validação da dobra", LIGHT, BLUE),
        ("Acoplamento ao modelo fenomenológico:\n$\\hat{\\nu}\\ \\rightarrow\\ \\delta\\ \\rightarrow\\ \\hat{X}_{Zn}$ "
         "nos 7 instantes experimentais", TEAL_LIGHT, TEAL),
        ("Armazenamento das previsões fora da dobra", LIGHTER, NAVY),
    ]
    ys = [9.7, 7.2, 4.3, 1.9]
    hs = [2.0, 1.5, 2.0, 1.3]
    for y, hh, (txt, fc, ec) in zip(ys, hs, passos):
        box(ax, (6.0, y), 13.0, hh, txt, fc=fc, ec=ec, fs=10.2)
    for (ya, _), (yc, hc) in zip(zip(ys[:-1], hs[:-1]), zip(ys[1:], hs[1:])):
        arrow(ax, (12.5, ya), (12.5, yc + hc), lw=1.3, ms=11)
    arrow(ax, (3.9, 7.5), (6.0, 10.7), lw=1.4)
    # saída
    box(ax, (21.0, 6.6), 4.7, 3.0, "RMSE de $X_{Zn}$\nnos 91 pontos\nfora da dobra,\npor semente", fc=ORANGE_LIGHT,
        ec=ORANGE, fs=10.3)
    box(ax, (21.0, 1.6), 4.7, 3.2, "Nota da\nconfiguração:\nmédia entre\nas sementes", fc=ORANGE_LIGHT, ec=ORANGE,
        fs=10.3, bold=True)
    ax.plot([19.0, 20.4, 20.4], [2.55, 2.55, 8.1], color=NAVY, lw=1.4)
    arrow(ax, (20.4, 8.1), (21.0, 8.1), lw=1.4)
    arrow(ax, (23.35, 6.6), (23.35, 4.8), lw=1.4)
    save(fig, "fig_hs_14_avaliacao_configuracao")


def fig_busca_hiperparametros() -> None:
    """Figura 15: (a) ciclo da busca bayesiana com TPE e poda; (b) sequência de seleção até o modelo final."""
    fig, ax = plt.subplots(figsize=(14.0, 7.6))
    ax.set_xlim(0, 28)
    ax.set_ylim(0, 15.5)
    ax.axis("off")
    ax.text(0.3, 14.9, "(a) Ciclo de uma busca", fontsize=12, color=NAVY)
    ciclo = [
        ((0.8, 11.6), "Histórico das tentativas\n(configuração e nota)", LIGHTER, NAVY),
        ((7.4, 11.6), "Divisão: melhores, $\\ell(\\mathbf{x})$,\ne demais, $g(\\mathbf{x})$", LIGHT, BLUE),
        ((7.4, 6.4), "Nova configuração:\nmaior razão $\\ell(\\mathbf{x})/g(\\mathbf{x})$", LIGHT, BLUE),
        ((0.8, 6.4), "Avaliação pelo protocolo\n(Figura 4.X.14)", TEAL_LIGHT, TEAL),
    ]
    for (x, y), txt, fc, ec in ciclo:
        box(ax, (x, y), 5.4, 2.3, txt, fc=fc, ec=ec, fs=10.2)
    arrow(ax, (6.2, 12.75), (7.4, 12.75), lw=1.3)
    arrow(ax, (10.1, 11.6), (10.1, 8.7), lw=1.3)
    arrow(ax, (7.4, 7.55), (6.2, 7.55), lw=1.3)
    arrow(ax, (3.5, 8.7), (3.5, 11.6), lw=1.3)
    box(ax, (0.8, 2.2), 5.4, 2.6, "Poda: interrompe a tentativa\nse, após a 2ª dobra, a nota\nparcial for pior que a mediana",
        fc=ORANGE_LIGHT, ec=ORANGE, fs=9.8)
    arrow(ax, (3.5, 6.4), (3.5, 4.8), color=ORANGE, lw=1.2, ls="--")
    ax.text(7.0, 3.5, "As primeiras tentativas\nsão sorteadas ao acaso\n(30 a 40 tentativas)", fontsize=9.8,
            color=GRAY, va="center")

    ax.plot([14.0, 14.0], [0.8, 14.8], color=GRAY, lw=0.8, ls=":")
    ax.text(14.6, 14.9, "(b) Sequência de seleção", fontsize=12, color=NAVY)
    seq = [
        ("Busca 1: 1 a 4 camadas; parada antecipada\nou épocas fixas (423 tentativas, 3 sementes)", LIGHT, BLUE),
        ("Busca 2: espaço ampliado nos limites da busca 1\n(até 8 camadas, ln t, blocos residuais; 523 tentativas)",
         LIGHT, BLUE),
        ("Finalistas reavaliados com 10 sementes\n(5 melhores de cada busca e a configuração de referência)",
         TEAL_LIGHT, TEAL),
        ("Regra de um erro-padrão e comparação pareada", TEAL_LIGHT, TEAL),
        ("Configuração final $\\rightarrow$ comitê de 10 redes\n$\\rightarrow$ teste cego, avaliado uma única vez",
         ORANGE_LIGHT, ORANGE),
    ]
    yy = [12.2, 9.6, 7.0, 4.75, 1.8]
    hh = [2.0, 2.0, 2.0, 1.4, 2.0]
    for y, h_, (txt, fc, ec) in zip(yy, hh, seq):
        box(ax, (14.8, y), 12.6, h_, txt, fc=fc, ec=ec, fs=10.2)
    for (ya, _), (yc, hc) in zip(zip(yy[:-1], hh[:-1]), zip(yy[1:], hh[1:])):
        arrow(ax, (21.1, ya), (21.1, yc + hc), lw=1.3, ms=11)
    save(fig, "fig_hs_15_busca_hiperparametros")


def fig_comite_redes() -> None:
    """Figura 16: comitê de 10 redes acoplado ao modelo fenomenológico, com a faixa de incerteza."""
    fig, ax = plt.subplots(figsize=(13.5, 6.2))
    ax.set_xlim(0, 27)
    ax.set_ylim(0, 12.4)
    ax.axis("off")
    box(ax, (0.3, 4.9), 3.4, 2.6, "$C_{A0}$, $\\eta$, $t$", fc=LIGHTER, fs=11)
    ys = [10.2, 8.0, 3.2, 1.0]
    rot = ["Rede 1 (semente 42)", "Rede 2 (semente 43)", "Rede 9 (semente 50)", "Rede 10 (semente 51)"]
    for y, r in zip(ys, rot):
        box(ax, (5.2, y), 4.6, 1.4, r, fc=LIGHT, ec=BLUE, fs=10)
        arrow(ax, (3.7, 6.2), (5.2, y + 0.7), lw=1.0, ms=9)
        arrow(ax, (9.8, y + 0.7), (12.2, 6.2), lw=1.0, ms=9)
        if y > 6:
            arrow(ax, (9.8, y + 0.7), (17.4, y + 0.7), color=GRAY, lw=0.9, ls="--", ms=8)
    ax.text(7.5, 6.05, "$\\vdots$", ha="center", va="center", fontsize=22, color=BLUE)
    box(ax, (12.2, 5.0), 3.8, 2.4, "Média das taxas\n$\\bar{\\nu}(t)$", fc=TEAL_LIGHT, ec=TEAL, fs=10.5)
    box(ax, (17.4, 5.0), 3.6, 2.4, "Acoplamento\n(Seção 4.X)", fc=LIGHT, ec=BLUE, fs=10.5)
    arrow(ax, (16.0, 6.2), (17.4, 6.2), lw=1.3)
    box(ax, (22.0, 5.0), 3.7, 2.4, "Previsão\n$\\hat{X}_{Zn}(t)$, $C_A(t)$", fc=ORANGE_LIGHT, ec=ORANGE, fs=10.5,
        bold=True)
    arrow(ax, (21.0, 6.2), (22.0, 6.2), lw=1.3)
    box(ax, (17.4, 8.0), 8.3, 3.6, "Cada rede acoplada separadamente:\n$\\hat{X}_{Zn,m}(t)$, $m=1,\\ldots,10$",
        fc="white", ec=GRAY, fs=10.2)
    box(ax, (17.4, 0.8), 8.3, 3.6, "Faixa de incerteza:\nmínimo e máximo de $\\hat{X}_{Zn,m}(t)$\nentre os membros",
        fc="white", ec=GRAY, fs=10.2)
    ax.plot([25.7, 26.4, 26.4], [9.8, 9.8, 2.6], color=GRAY, lw=1.1, ls="--")
    arrow(ax, (26.4, 2.6), (25.7, 2.6), color=GRAY, lw=1.1, ls="--", ms=9)
    save(fig, "fig_hs_16_comite_redes")


def fig_algoritmo_simulacao() -> None:
    """Figura 17: algoritmo de simulação do modelo híbrido serial para uma condição (C_A0, eta)."""
    passos = [
        ("Malha canônica", "$t_k=0{,}25\\,k$ min, $k=1,\\ldots,60$ (ou até o maior tempo solicitado)"),
        ("Taxa de retração", "rede neural (ou comitê) $\\rightarrow$ $\\hat{\\nu}(t_k)\\geq0$ em cada nó"),
        ("Retração acumulada", "$\\delta_1=\\hat{\\nu}(t_1)\\,t_1$ e regra do trapézio (Eq. 4.X.6)"),
        ("Conversão", "$X_{Zn}(\\delta_k)$ pela curva pré-calculada com interpolação PCHIP (Eq. 4.X.3)"),
        ("Restrições físicas", "conversão não decrescente e $X_{Zn}\\leq\\min(1,\\eta)$; $\\delta$ congelado se o ácido se esgota"),
        ("Ácido livre", "$C_A=C_{A0}\\,[1-X_{Zn}/\\eta]$ (Eq. 4.X.4)"),
        ("Saída", "condição inicial imposta em $t=0$ e interpolação nos tempos solicitados"),
    ]
    n = len(passos)
    row_h, gap = 1.0, 0.45
    total_h = n * row_h + (n - 1) * gap
    fig, ax = plt.subplots(figsize=(11.0, (total_h + 0.6) / 1.9))
    ax.set_xlim(0, 22)
    ax.set_ylim(-0.3, total_h + 0.3)
    ax.axis("off")
    cores = [(LIGHTER, NAVY), (TEAL_LIGHT, TEAL), (LIGHT, BLUE), (LIGHT, BLUE), (ORANGE_LIGHT, ORANGE),
             (LIGHT, BLUE), (LIGHTER, NAVY)]
    for i, ((titulo, desc), (fc, ec)) in enumerate(zip(passos, cores)):
        y = total_h - (i + 1) * row_h - i * gap
        box(ax, (1.6, y), 20.0, row_h, "", fc=fc, ec=ec)
        ax.add_patch(Circle((0.75, y + row_h / 2), 0.42, fc=NAVY, ec=NAVY, zorder=3))
        ax.text(0.75, y + row_h / 2, str(i + 1), ha="center", va="center", color="white", fontsize=12,
                fontweight="bold", zorder=4)
        ax.text(2.0, y + row_h / 2, titulo, ha="left", va="center", fontsize=11, color=NAVY, fontweight="bold",
                zorder=3)
        ax.text(6.6, y + row_h / 2, desc, ha="left", va="center", fontsize=10.3, color="#1F2937", zorder=3)
        if i < n - 1:
            arrow(ax, (0.75, y + row_h / 2 - 0.44), (0.75, y - gap - row_h / 2 + 0.44), lw=1.3, ms=10)
    save(fig, "fig_hs_17_algoritmo_simulacao")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for nome in sys.argv[1:]:
            globals()[nome]()
        sys.exit()
    fig_arquitetura_serial()
    fig_fluxograma_etapas()
    fig_retracao_uniforme()
    fig_curva_conversao_delta()
    fig_problema_inverso()
    fig_parametrizacao_biexponencial()
    fig_malhas_temporais()
    fig_particao_dobras()
    fig_distribuicao_alvo()
    fig_fluxo_preparacao()
    fig_arquitetura_mlp()
    fig_funcoes_rede()
    fig_treinamento_mlp()
    fig_avaliacao_configuracao()
    fig_busca_hiperparametros()
    fig_comite_redes()
    fig_algoritmo_simulacao()
    print("Figuras geradas em", FIG_DIR)
