"""Segunda figura-modelo: painel único (sem rótulo (a)), barras de RMSE por ensaio, 4 modelos, 16 ensaios, 8 cm de altura.

Mostra: altura baixa, eixo de categorias (pg.ROTULOS["ensaio"]), asterisco nos ensaios de teste cego (pg.rotulos_ensaio),
eixo y começando em zero e legenda no topo sem o item "Experimental".
Saída: exemplos/figura_painel_unico_exemplo.png e .pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import padrao_graficos_lop as pg  # noqa: E402

CSV = AQUI.parents[1] / "Código" / "outputs" / "etapa_4_2_avaliacao_indomain" / "tabela_comparativo_4_modelos_por_ensaio.csv"


def main() -> None:
    df = pd.read_csv(CSV).sort_values("ensaio")
    cegos = df.loc[df["particao"].str.contains("cego", case=False), "ensaio"].tolist()
    fig, gs = pg.nova_figura(altura_cm=8.0)
    ax = fig.add_subplot(gs[0, 0])
    pg.barras_agrupadas(ax, pg.rotulos_ensaio(df["ensaio"], cegos), {k: (df[f"RMSE_{k}"] * 100).tolist() for k in pg.ORDEM_LEGENDA_PADRAO})
    ax.set_xlabel(pg.ROTULOS["ensaio"])
    ax.set_ylabel(pg.ROTULOS["RMSE"])
    ax.set_ylim(0, None)
    pg.legenda_topo(fig, experimental=False, barras=True)
    for p in pg.salvar(fig, AQUI / "exemplos" / "figura_painel_unico_exemplo"):
        print("gravado:", p)
    print("teste cego:", cegos, "| na legenda do Word:", pg.NOTA_TESTE_CEGO)


if __name__ == "__main__":
    main()
