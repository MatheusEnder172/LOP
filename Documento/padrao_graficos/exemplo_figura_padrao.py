"""Figura-modelo do padrão LOP (estilo C): cinética + paridade + RMSE, quatro modelos, dados reais do projeto.

É a referência visual: quem for fazer uma figura de Resultados deve parecer com esta (fonte, cores, linhas,
legenda no topo, rótulos (a)(b)(c), vírgula decimal, 16 cm, 300 DPI). Só usa funções de padrao_graficos_lop.

Saída: exemplos/figura_padrao_exemplo.png e .pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import padrao_graficos_lop as pg  # noqa: E402
from exemplos_estilos import ENSAIO_EXEMPLO, ORDEM, dados  # noqa: E402  (só para carregar os dados reais)


def main() -> None:
    D = dados()
    fig, gs = pg.nova_figura(altura_cm=15.0, nlin=2, ncol=2, height_ratios=[1.15, 1], hspace=0.38)
    a, b, c = fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])

    # (a) cinética de um ensaio, com o zoom do primeiro minuto
    pg.linha_referencia(a, y=min(1.0, D["eta"]))
    ins = pg.inserto_zoom(a, xlim=(0, 1.6), ylim=(0, 1.0), retangulo=(0.42, 0.13, 0.50, 0.45))
    for ax in (a, ins):
        for k in ("fab", "novo", "hib"):
            pg.linha_modelo(ax, D["tf"], D["curvas"][k], k)
        pg.linha_modelo(ax, *D["puro"], "puro")
        pg.pontos_exp(ax, D["t9"], D["x9"])
    a.set_xlim(-0.3, 15.5)
    a.set_ylim(-0.02, 1.2)
    a.set_xlabel(pg.ROTULOS["t"])
    a.set_ylabel(pg.ROTULOS["XZn"])
    a.text(0.985, 0.97, f"Ensaio {ENSAIO_EXEMPLO}: $C_{{\\mathrm{{A0}}}}$ = {pg.num(D['ca0'])} mol/L, η = {pg.num(D['eta'], 0)}",
           transform=a.transAxes, ha="right", va="top", fontsize=9.5)

    # (b) paridade, 112 pontos
    pg.diagonal_paridade(b, 0.3, 1.05)
    for k in ORDEM:
        s = D["pts"][D["pts"]["modelo"] == k]
        pg.dispersao_modelo(b, s["x"], s["p"], k)
    b.set_xlabel(pg.ROTULOS["XZn_exp"])
    b.set_ylabel(pg.ROTULOS["XZn_mod"])

    # (c) RMSE por partição
    grupos = ["Treino", "Teste cego", "Global"]
    pg.barras_agrupadas(c, grupos, {k: [D["rmse"][g][k] * 100 for g in grupos] for k in ORDEM})
    c.set_ylabel(pg.ROTULOS["RMSE"])
    c.set_ylim(0, 14)

    pg.rotular_paineis([a, b, c])
    pg.legenda_topo(fig)
    for p in pg.salvar(fig, AQUI / "exemplos" / "figura_padrao_exemplo"):
        print("gravado:", p)


if __name__ == "__main__":
    main()
