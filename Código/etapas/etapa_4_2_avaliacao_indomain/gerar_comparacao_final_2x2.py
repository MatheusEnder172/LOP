"""Figura de COMPARAÇÃO dos Resultados: 2x2 por ensaio (4 figuras de 4 ensaios, cobrindo os 16). Decidido em 09/11/2026.

Cada quadro: pontos experimentais, limite estequiométrico min(1; η) e as curvas de cada modelo, nas cores fixas do padrão.
O white-box novo (RRB ÷ D³, α = 0) entra sempre. As modelagens do grupo entram sozinhas, à medida que cada integrante
entrega `Código/outputs/resultados_por_modelagem/<pinn|paralelo|serial>/curvas_<nome>.csv` (veja resultados_lop.py).

Uso:
    python gerar_comparacao_final_2x2.py                    # white-box novo + modelagens já entregues
    python gerar_comparacao_final_2x2.py --referencias      # + white-box do Fabrício e MLP pura (referências)

Saída: Código/outputs/resultados_por_modelagem/comparacao[_com_referencias]/
    fig_comparacao_2x2_ensaios_01_04 ... _13_16 (PNG + PDF), metricas_resumo.csv, metricas_por_ensaio.csv.
Só leitura de resultados congelados; nada é treinado.
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "Documento" / "padrao_graficos"))
sys.path.insert(0, str(RAIZ / "Código"))
import padrao_graficos_lop as pg  # noqa: E402
import resultados_lop as rl  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--referencias", action="store_true", help="inclui o white-box do Fabrício e a MLP pura")
    com_ref = ap.parse_args().referencias

    exp = rl.carregar_experimentos()
    modelagens = rl.modelagens_disponiveis()
    curvas = rl.juntar_curvas(chaves=modelagens, exp=exp)
    if com_ref:
        curvas = {"fab": rl.curvas_whitebox_fabricio(exp), "novo": curvas["novo"], "puro": rl.curvas_mlp_pura(exp),
                  **{k: v for k, v in curvas.items() if k != "novo"}}
    faltam = [k for k in ("pinn", "par", "hib") if k not in modelagens]
    print("modelos na figura:", [pg.estilo_de(k).nome for k in curvas])
    if faltam:
        print("ainda não entregaram:", [pg.estilo_de(k).nome for k in faltam])

    pasta = rl.PASTA_RESULTADOS / ("comparacao_com_referencias" if com_ref else "comparacao")
    for ini in (1, 5, 9, 13):
        pg.salvar(rl.grafico_2x2(range(ini, ini + 4), exp, curvas), pasta / f"fig_comparacao_2x2_ensaios_{ini:02d}_{ini + 3:02d}")
    por, res = rl.metricas(exp, curvas)
    por.round(4).to_csv(pasta / "metricas_por_ensaio.csv", index=False)
    res.round(4).to_csv(pasta / "metricas_resumo.csv", index=False)
    print(res.round(2).to_string(index=False))
    print("saída:", pasta)


if __name__ == "__main__":
    main()
