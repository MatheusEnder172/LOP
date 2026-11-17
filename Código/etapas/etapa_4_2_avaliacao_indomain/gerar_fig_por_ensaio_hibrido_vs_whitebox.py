"""Uma figura por ensaio (16): pontos experimentais, curva do híbrido serial, curva do white-box e limite estequiométrico.

Padrão de gráficos do grupo (Documento/padrao_graficos/padrao_graficos_lop.py, estilo C): 16 cm, 300 DPI, PNG + PDF.
Cada figura tem 2 painéis: (a) cinética de 0 a 15 min; (b) ampliação do 1º minuto (0 a 2 min).

White-box: por padrão o NOVO (RRB ÷ D³, sem alpha). `--whitebox fab` troca pelo do Fabrício (RRB em massa, α = 5500 µm/min).
Híbrido: SerialHybridModel("mlp_v2"), comitê congelado. Só leitura de modelos congelados; nada é treinado.
Limite estequiométrico: X_Zn máximo = min(1, η).

Saídas em Código/outputs/etapa_4_2_avaliacao_indomain/por_ensaio_<whitebox>/:
  fig_ensaio_XX_hibrido_vs_whitebox_<whitebox>.png/.pdf e dados_plotados_por_ensaio.csv (pontos experimentais e previstos).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CODIGO = Path(__file__).resolve().parents[2]
RAIZ = CODIGO.parent
sys.path.insert(0, str(CODIGO))
sys.path.insert(0, str(RAIZ / "Documento" / "padrao_graficos"))
import padrao_graficos_lop as pg  # noqa: E402
from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402
from src.physics.granulometry import RosinRammlerBennet, RosinRammlerMassaAntiga  # noqa: E402
from src.physics.kinetics import LeachingKinetics  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

RAW = RAIZ / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
OUT = CODIGO / "outputs" / "etapa_4_2_avaliacao_indomain"
ENSAIOS_TESTE = [7, 8, 14]
NOME_WB = {"novo": "White-box (novo)", "fab": "White-box (Fabrício)"}


def solver_whitebox(qual: str) -> BatchPBMSolver:
    if qual == "fab":
        return BatchPBMSolver(granulometry=RosinRammlerMassaAntiga(), kinetics=LeachingKinetics(alpha_nominal=5500.0), n_mesh_points=5000)
    return BatchPBMSolver(granulometry=RosinRammlerBennet(use_number_density_d3=True), kinetics=LeachingKinetics(alpha_nominal=0.0), n_mesh_points=5000)


def rmse(a, b) -> float:
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def desenhar(e: int, d: pd.DataFrame, wb, hib, qual: str, pasta: Path) -> list[dict]:
    ca0, eta = float(d["CA0_mol_L"].iloc[0]), float(d["razao_molar_eta"].iloc[0])
    t, x = d["t_min"].values, d["XZn"].values
    teto = min(1.0, eta)
    tf = np.unique(np.concatenate([np.linspace(0, 2, 201), np.linspace(2, 15, 131)]))
    x_wb_f = np.asarray(wb.simulate(ca0=ca0, eta=eta, t_eval=tf)["XZn"])
    x_hib_f = np.asarray(hib.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=tf)["XZn"])
    x_wb = np.asarray(wb.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"])
    x_hib = np.asarray(hib.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t)["XZn"])

    fig, gs = pg.nova_figura(altura_cm=7.8, nlin=1, ncol=2, width_ratios=[1.7, 1], wspace=0.28, bottom=1.5 / 7.8)
    a, b = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    for ax in (a, b):
        pg.linha_referencia(ax, y=teto)
        pg.linha_modelo(ax, tf, x_wb_f, "novo" if qual == "novo" else "fab")
        pg.linha_modelo(ax, tf, x_hib_f, "hib")
        pg.pontos_exp(ax, t, x)
        ax.set_ylim(0, 1.2)
        ax.set_xlabel(pg.ROTULOS["t"])
    a.set_xlim(-0.3, 15.5)
    b.set_xlim(0, 2.1)
    a.set_ylabel(pg.ROTULOS["XZn"])

    part = "teste cego" if e in ENSAIOS_TESTE else "treino"
    a.text(0.965, 0.05, f"Ensaio {e} ({part}): $C_{{\\mathrm{{A0}}}}$ = {pg.num(ca0)} mol/L, η = {pg.num(eta)}\n"
           f"RMSE (p.p.): híbrido {pg.num(100 * rmse(x, x_hib), 1)}; white-box {pg.num(100 * rmse(x, x_wb), 1)}",
           transform=a.transAxes, ha="right", va="bottom", fontsize=8.5, linespacing=1.35)
    pg.rotular_paineis([a, b], y=0.975)
    lim = pg.Estilo("", pg.COR_REFERENCIA, pg.LS_REFERENCIA, "", "", pg.LW_REFERENCIA + 0.2)
    pg.legenda_topo(fig, chaves=["novo" if qual == "novo" else "fab", "hib"], extras=(("Limite estequiométrico, min(1; η)", lim),))
    nome = f"fig_ensaio_{e:02d}_hibrido_vs_whitebox_{qual}"
    pg.salvar(fig, pasta / nome)
    return [{"ensaio": e, "particao": part, "CA0_mol_L": ca0, "eta": eta, "limite_estequiometrico": teto, "t_min": ti,
             "XZn_exp": xi, "XZn_hibrido": hi, f"XZn_whitebox_{qual}": wi} for ti, xi, hi, wi in zip(t, x, x_hib, x_wb)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--whitebox", choices=["novo", "fab"], default="novo")
    qual = ap.parse_args().whitebox
    pasta = OUT / f"por_ensaio_{qual}"
    exp = pd.read_csv(RAW)
    pos = exp[exp["t_min"] > 0].sort_values(["ensaio", "t_min"])
    wb, hib = solver_whitebox(qual), SerialHybridModel(model_type="mlp_v2")
    linhas = []
    for e in sorted(pos["ensaio"].unique()):
        linhas += desenhar(int(e), pos[pos["ensaio"] == e], wb, hib, qual, pasta)
        print("ok ensaio", e)
    pd.DataFrame(linhas).to_csv(pasta / "dados_plotados_por_ensaio.csv", index=False)
    print("saída:", pasta)


if __name__ == "__main__":
    main()
