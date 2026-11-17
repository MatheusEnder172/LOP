"""Figuras esquemáticas do modelo black-box (MLP pura), no mesmo visual das figuras da modelagem híbrida serial.

- fig_mlp_01_generica_fluxo: perceptron multicamadas genérico e ciclo de treinamento (Revisão, Seção 3.2.2).
  A perda é calculada só com dados; uma nota marca a diferença para a PINN, que soma os resíduos das equações.
- fig_mlp_02_arquitetura_mlp_pura: a rede usada no trabalho (Métodos, Seção 4.3): entradas, padronização,
  três camadas ocultas (90, 45 e 22 neurônios, GELU), saída linear, treinamento e comitê de dez redes.
  Os valores vêm de `Código/outputs/models_saved/mlp_puro_xzn/mlp_puro_config.json` (conferidos na execução).

Uso: python gerar_figuras_mlp_pura.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

FIG_DIR = Path(__file__).resolve().parent
CONFIG = FIG_DIR.parents[1] / "Código" / "outputs" / "models_saved" / "mlp_puro_xzn" / "mlp_puro_config.json"

# mesma paleta de gerar_figuras_hibrido_serial.py
NAVY, BLUE, LIGHT, LIGHTER = "#1F3A5F", "#2E6DA4", "#DCE8F4", "#EEF4FA"
TEAL, TEAL_LIGHT, ORANGE, ORANGE_LIGHT, GRAY = "#2A9D8F", "#D7EFEC", "#D9822B", "#FBE9D7", "#6B7280"

plt.rcParams.update({"font.family": "Arial", "font.size": 11, "mathtext.fontset": "dejavusans", "savefig.dpi": 300})


def save(fig, name: str) -> None:
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def box(ax, xy, w, h, text, fc=LIGHT, ec=NAVY, fs=11, bold=False, lw=1.4, color=NAVY, ls="-"):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=lw,
                                ls=ls, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color,
            fontweight="bold" if bold else "normal", zorder=3, linespacing=1.35)


def arrow(ax, p0, p1, color=NAVY, lw=1.6, ls="-", ms=16):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=ms, color=color, lw=lw, linestyle=ls,
                                 zorder=1))


def rede(ax, xs, camadas, yc, dy, r=0.27, cor_saida=TEAL_LIGHT, reticencias=()):
    """Desenha os neurônios e as ligações; devolve as coordenadas por camada."""
    coords = []
    for n, x in zip(camadas, xs):
        ys = yc + dy * (np.arange(n) - (n - 1) / 2)
        coords.append([(x, float(y)) for y in ys])
    for a, b in zip(coords[:-1], coords[1:]):
        for p in a:
            for q in b:
                ax.plot([p[0], q[0]], [p[1], q[1]], color=GRAY, lw=0.5, alpha=0.6, zorder=1)
    for i, camada in enumerate(coords):
        for x, y in camada:
            ax.add_patch(Circle((x, y), r, fc=cor_saida if i == len(coords) - 1 else "white", ec=NAVY, lw=1.1, zorder=2))
    for i in reticencias:   # camada com mais neurônios do que os desenhados
        x = xs[i]
        ax.text(x, yc, "⋮", ha="center", va="center", fontsize=13, color=NAVY, zorder=4,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))
    return coords


def fig_generica() -> None:
    """Perceptron multicamadas genérico: alimentação direta, perda calculada com os dados e retropropagação."""
    fig, ax = plt.subplots(figsize=(12.5, 6.2))
    ax.set_xlim(0, 25)
    ax.set_ylim(0.9, 12.4)
    ax.axis("off")
    yc = 6.9

    box(ax, (0.2, yc - 1.95), 3.3, 3.4, "Variáveis de\nentrada\n\n$x_1,\\ x_2,\\ \\ldots,\\ x_n$", fc=LIGHTER)

    ax.add_patch(FancyBboxPatch((4.5, 3.7), 9.0, 6.6, boxstyle="round,pad=0.02,rounding_size=0.2", fc=ORANGE_LIGHT,
                                ec=ORANGE, lw=1.4, ls="--", zorder=0))
    ax.text(9.0, 11.75, "Perceptron multicamadas (MLP)", ha="center", fontsize=11.5, color=ORANGE, fontweight="bold")
    ax.text(9.0, 11.05, "alimentação direta (da entrada para a saída)", ha="center", fontsize=10, color=NAVY)
    arrow(ax, (4.9, 10.7), (13.1, 10.7), lw=1.2, ms=12)
    xs = [5.6, 7.9, 10.2, 12.4]
    rede(ax, xs, [3, 4, 4, 1], yc - 0.25, 1.15)
    for x, txt in zip((xs[0], (xs[1] + xs[2]) / 2, xs[3]), ("Camada de\nentrada", "Camadas ocultas", "Camada de\nsaída")):
        ax.text(x, 4.3, txt, ha="center", va="center", fontsize=9.6, color=NAVY, linespacing=1.2)
    # o que cada neurônio calcula
    ax.text(9.0, 9.6, r"cada neurônio:  $a_j=\sigma\,(\sum_i w_{ji}\,x_i+b_j)$", ha="center", va="center",
            fontsize=10, color=NAVY)

    ym = yc - 0.25
    box(ax, (14.6, ym - 1.1), 2.9, 2.2, "Saída\nprevista\n$\\hat{y}$", fc=TEAL_LIGHT, ec=TEAL)
    box(ax, (18.7, ym - 1.7), 6.0, 3.4,
        "Função de perda\n\n$L=\\frac{1}{N}\\sum_k(\\hat{y}_k-y_k)^2$\n\ncalculada apenas com os dados",
        fc=LIGHT, fs=10.6)
    box(ax, (19.6, 10.3), 4.2, 1.5, "Dados medidos, $y$", fc=LIGHTER, fs=10.6)
    arrow(ax, (21.7, 10.3), (21.7, ym + 1.75))
    arrow(ax, (3.55, ym), (5.15, ym))
    arrow(ax, (12.75, ym), (14.6, ym))
    arrow(ax, (17.55, ym), (18.7, ym))

    # retorno: retropropagação
    yr = 2.0
    ax.plot([21.7, 21.7], [ym - 1.75, yr], color=BLUE, lw=1.5, ls="--")
    ax.plot([21.7, 9.0], [yr, yr], color=BLUE, lw=1.5, ls="--")
    arrow(ax, (9.0, yr), (9.0, 3.65), color=BLUE, lw=1.5, ls="--")
    ax.text(15.3, yr + 0.3, "retropropagação do erro: gradiente de $L$ em relação a $w$ e $b$", ha="center", fontsize=10, color=BLUE)
    ax.text(15.3, yr - 0.6, "o otimizador atualiza os pesos e os vieses; o ciclo se repete a cada época", ha="center",
            fontsize=10, color=BLUE)
    save(fig, "fig_mlp_01_generica_fluxo")


def fig_arquitetura() -> None:
    """A MLP pura do trabalho: do ensaio à conversão prevista, com o treinamento e o comitê."""
    conf = json.loads(CONFIG.read_text(encoding="utf-8"))
    c = conf["config"]
    assert (c["hidden_dims"], c["lr"], c["weight_decay"], c["batch_size"], c["dropout"], c["epocas_finais"]) == \
        ([90, 45, 22], 0.01, 0.0001, 16, 0.0, 900), c
    assert conf["features"] == ["CA0_mol_L", "razao_molar_eta", "ln_t_min"] and conf["sementes"] == list(range(42, 52))
    dims = [3, *c["hidden_dims"], 1]
    n_par = sum(a * b + b for a, b in zip(dims[:-1], dims[1:]))
    assert n_par == 5490
    lotes = math.ceil(91 / c["batch_size"])

    fig, ax = plt.subplots(figsize=(13.5, 8.3))
    ax.set_xlim(0, 27)
    ax.set_ylim(0, 16.4)
    ax.axis("off")

    w, h, y0 = 3.2, 3.2, 11.7
    etapas = [
        ("Entradas\n\n$C_{A0}$, $\\eta$, $t$\n($t>0$)", LIGHTER, NAVY),
        ("Padronização\n(escore Z)\n\n$\\tilde{C}_{A0}$, $\\tilde{\\eta}$\ne ln $t$ padronizado", ORANGE_LIGHT, ORANGE),
        (f"Camada\noculta 1\n\nlinear {dims[0]} → {dims[1]}\n+ GELU", LIGHT, BLUE),
        (f"Camada\noculta 2\n\nlinear {dims[1]} → {dims[2]}\n+ GELU", LIGHT, BLUE),
        (f"Camada\noculta 3\n\nlinear {dims[2]} → {dims[3]}\n+ GELU", LIGHT, BLUE),
        (f"Camada de\nsaída\n\nlinear {dims[3]} → 1\nsem ativação", TEAL_LIGHT, TEAL),
        ("Conversão\nprevista\n\n$\\hat{X}_{Zn}$\nsem restrições", TEAL_LIGHT, TEAL),
    ]
    xs = [0.3 + i * (w + 0.62) for i in range(len(etapas))]
    for x, (txt, fc, ec) in zip(xs, etapas):
        box(ax, (x, y0), w, h, txt, fc=fc, ec=ec, fs=10.2)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        arrow(ax, (x0 + w, y0 + h / 2), (x1, y0 + h / 2), lw=1.4, ms=12)
    yc = y0 + h + 0.3
    ax.plot([xs[2], xs[2], xs[4] + w, xs[4] + w], [yc - 0.15, yc, yc, yc - 0.15], color=BLUE, lw=1.2)
    ax.text(xs[3] + w / 2, yc + 0.3, "Camadas ocultas (ativação GELU, sem blocos residuais e sem dropout)",
            ha="center", fontsize=10.5, color=BLUE, fontweight="bold")
    ax.text(xs[1] + w / 2, y0 - 0.45, "média e desvio-padrão\nsó dos pontos de treino", ha="center", va="top",
            fontsize=9.2, color=ORANGE, linespacing=1.2)
    ax.text(xs[3] + w / 2, y0 - 0.45, f"{n_par:,} parâmetros (pesos e vieses)".replace(",", "."), ha="center", va="top",
            fontsize=9.6, color=BLUE)
    ax.text(xs[6] + w / 2, y0 - 0.45, "não se impõem $X(0)=0$,\n$dX/dt\\geq 0$ nem $X\\leq\\min(1,\\eta)$", ha="center",
            va="top", fontsize=9.2, color=TEAL, linespacing=1.2)

    # treinamento de cada rede
    ax.add_patch(FancyBboxPatch((0.6, 0.5), 25.8, 8.6, boxstyle="round,pad=0.02,rounding_size=0.2", fc="#F7F9FC",
                                ec=BLUE, lw=1.3, ls="--", zorder=0))
    ax.text(1.0, 8.5, "Treinamento de cada rede e modelo final", ha="left", fontsize=11, color=BLUE, fontweight="bold")
    yb, hb = 5.2, 2.2
    passos = [
        ("Dados de treino\n13 ensaios, 91 pontos\n($t>0$)", 4.3, LIGHTER, NAVY),
        (f"Mini-lotes de\n{c['batch_size']} pontos\n({lotes} por época)", 3.5, "white", BLUE),
        ("Perda: erro quadrático\nmédio entre $\\hat{X}_{Zn}$\ne $X_{Zn}$ medido", 4.5, "white", BLUE),
        ("Retropropagação\n(gradiente da perda)", 4.0, "white", BLUE),
        ("AdamW\ntaxa de aprendizado $10^{-2}$\npenalização dos pesos $10^{-4}$", 5.3, "white", BLUE),
    ]
    x, pos = 1.2, []
    for txt, wb, fc, ec in passos:
        box(ax, (x, yb), wb, hb, txt, fc=fc, ec=ec, fs=9.8)
        pos.append((x, wb))
        x += wb + 0.75
    for (xa, wa), (xc, _) in zip(pos[:-1], pos[1:]):
        arrow(ax, (xa + wa, yb + hb / 2), (xc, yb + hb / 2), lw=1.2, ms=10)
    # laço das épocas: do otimizador de volta aos mini-lotes
    xo = pos[-1][0] + pos[-1][1] / 2
    xl = pos[1][0] + pos[1][1] / 2
    yl = yb - 0.75
    ax.plot([xo, xo, xl], [yb, yl, yl], color=ORANGE, lw=1.3)
    arrow(ax, (xl, yl), (xl, yb), color=ORANGE, lw=1.3, ms=10)
    ax.text((xo + xl) / 2, yl + 0.22, f"pesos e vieses atualizados; {c['epocas_finais']} épocas fixas, sem parada antecipada",
            ha="center", fontsize=9.8, color=ORANGE)

    # seleção e comitê
    box(ax, (1.2, 1.0), 11.6, 2.3,
        "Escolha da configuração: validação cruzada por ensaio\n(4 dobras), 32 combinações de arquitetura, taxa de aprendizado,\n"
        "penalização dos pesos e número de épocas", fc=ORANGE_LIGHT, ec=ORANGE, fs=9.8)
    box(ax, (14.0, 1.0), 11.8, 2.3,
        "Modelo final: comitê de 10 redes com a mesma configuração\n(sementes 42 a 51); a conversão prevista é a média\n"
        "das dez saídas", fc=TEAL_LIGHT, ec=TEAL, fs=9.8)
    arrow(ax, (12.85, 2.15), (14.0, 2.15), lw=1.2, ms=10)
    save(fig, "fig_mlp_02_arquitetura_mlp_pura")


if __name__ == "__main__":
    fig_generica()
    fig_arquitetura()
    print("figuras gravadas em", FIG_DIR)
