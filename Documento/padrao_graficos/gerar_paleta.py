"""Folha de referência da paleta do grupo LOP: cores, tipo de linha, marcador, hachura e teste de daltonismo/P&B.

Saída: exemplos/paleta_lop.png e .pdf (usa o próprio padrao_graficos_lop).
Também imprime a luminância de cada cor e os pares que se confundem em tons de cinza (motivo da redundância).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Rectangle

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import padrao_graficos_lop as pg  # noqa: E402

# Matrizes de Machado et al. (2009), severidade 1,0, aplicadas em RGB linear.
DEUTAN = np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]])
PROTAN = np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]])


def _lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _gam(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def simular(h, M):
    return _gam(M @ _lin(hex2rgb(h)))


def cinza(h):
    y = float(np.array([0.2126, 0.7152, 0.0722]) @ _lin(hex2rgb(h)))
    g = float(_gam(y))
    return np.array([g, g, g]), y


def main() -> None:
    itens = [(e.nome, e) for e in pg.MODELOS.values()] + [(f"Extra {i + 1}", e) for i, e in enumerate(pg.EXTRAS)]
    nomes_cor = {v.lower(): k for k, v in pg.OKABE_ITO.items()}

    fig, gs = pg.nova_figura(altura_cm=11.5, nlin=2, ncol=1, legenda_no_topo=False, height_ratios=[1.25, 1], hspace=0.12, left=0.02, right=0.98, top=0.98, bottom=0.03)
    t = fig.add_subplot(gs[0])
    t.set_xlim(0, 10); t.set_ylim(0, len(itens) + 1); t.axis("off")
    cab = {0.15: "Série", 2.9: "Cor", 4.35: "Linha", 5.7: "Marcador", 6.95: "Hachura", 8.3: "Hex"}
    for x, s in cab.items():
        t.text(x, len(itens) + 0.55, s, fontweight="bold", va="center")
    t.plot([0.1, 9.9], [len(itens) + 0.15] * 2, color="black", lw=0.8)
    for i, (nome, e) in enumerate(itens):
        y = len(itens) - i - 0.35
        t.text(0.15, y, nome if nome else "–", va="center")
        t.add_patch(Rectangle((2.9, y - 0.3), 1.1, 0.6, facecolor=e.cor, edgecolor="black", lw=0.6))
        t.plot([4.35, 5.25], [y, y], color=e.cor, ls=e.ls, lw=e.lw + 0.4)
        t.plot([6.0], [y], marker=e.marcador, color=e.cor, ms=6, ls="none")
        t.add_patch(Rectangle((7.0, y - 0.3), 0.9, 0.6, facecolor=e.cor, edgecolor="black", hatch=e.hachura, lw=0.5, alpha=0.9))
        t.text(8.3, y, e.cor.upper(), va="center", family="monospace", fontsize=8.5)

    u = fig.add_subplot(gs[1])
    u.set_xlim(0, 10); u.set_ylim(0, 4.3); u.axis("off")
    visoes = [("Normal", lambda h: hex2rgb(h)), ("Preto e branco", lambda h: cinza(h)[0]),
              ("Deuteranopia", lambda h: simular(h, DEUTAN)), ("Protanopia", lambda h: simular(h, PROTAN))]
    n = len(itens)
    larg = 6.9 / n
    for j, (rot, f) in enumerate(visoes):
        y = 3.5 - j
        u.text(0.15, y + 0.2, rot, va="center")
        for i, (_, e) in enumerate(itens):
            u.add_patch(Rectangle((2.9 + i * larg, y - 0.05), larg * 0.9, 0.5, facecolor=f(e.cor), edgecolor="black", lw=0.5))
    pg.salvar(fig, AQUI / "exemplos" / "paleta_lop")

    print("Luminância relativa (0 = preto, 1 = branco) e cinza equivalente:")
    lum = {}
    for nome, e in itens:
        g, y = cinza(e.cor)
        lum[nome or e.cor] = y
        print(f"  {nome or e.cor:24s} {e.cor}  Y={y:.3f}  cinza={g[0]:.3f}  ({nomes_cor.get(e.cor.lower(), 'neutro')})")
    print("Pares com diferença de luminância < 0,08 (se confundem em P&B; salvos pela linha/marcador/hachura):")
    ks = list(lum)
    for a in range(len(ks)):
        for b in range(a + 1, len(ks)):
            d = abs(lum[ks[a]] - lum[ks[b]])
            if d < 0.08:
                print(f"  {ks[a]} x {ks[b]}: {d:.3f}")


if __name__ == "__main__":
    main()
