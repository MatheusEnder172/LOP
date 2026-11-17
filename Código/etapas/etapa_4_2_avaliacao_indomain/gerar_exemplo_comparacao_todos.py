"""Exemplo de como fica a COMPARAÇÃO entre modelos no estilo novo (padrão C, cores fixas por modelo).

Usa só o que já tem resultado real: white-box do Fabrício, white-box novo, MLP pura (3.2.7) e híbrido serial (MLP v2).
PINN e híbrido paralelo ainda não existem; por isso a figura `ilustrativo_*` com as quatro modelagens do grupo usa curvas
FICTÍCIAS (derivadas do serial) e traz a marca "ILUSTRATIVO" desenhada na própria imagem. Ela só mostra o layout e as
cores; não é resultado. Só leitura de modelos congelados; nada é treinado.

Saída: Código/outputs/resultados_por_modelagem/exemplo_comparacao/
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "Documento" / "padrao_graficos"))
sys.path.insert(0, str(RAIZ / "Código"))
import padrao_graficos_lop as pg  # noqa: E402
import resultados_lop as rl  # noqa: E402
from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402
from src.physics.granulometry import RosinRammlerMassaAntiga  # noqa: E402
from src.physics.kinetics import LeachingKinetics  # noqa: E402
from src.physics.pbm_batch import BatchPBMSolver  # noqa: E402

SAIDA = RAIZ / "Código" / "outputs" / "resultados_por_modelagem" / "exemplo_comparacao"
PURO = RAIZ / "Código" / "outputs" / "etapa_3_2" / "subetapa_3_2_7_mlp_puro_xzn"


def curvas_mlp_pura(exp: pd.DataFrame) -> dict[int, rl.Curva]:
    """MLP pura: curva densa (a partir de 0,5 min, onde há dado) e previsões exatas nos pontos experimentais."""
    dens = pd.read_csv(PURO / "curvas_densas_mlp_puro.csv")
    pts = pd.read_csv(PURO / "predicoes_pontos_experimentais.csv").sort_values(["ensaio", "t_min"])
    out = {}
    for e in sorted(exp["ensaio"].unique()):
        d = dens[dens["ensaio"] == e].sort_values("t_min")
        out[int(e)] = rl.Curva(d["t_min"].to_numpy(), d["XZn_pred"].to_numpy(), pts.loc[pts["ensaio"] == e, "XZn_pred"].to_numpy())
    return out


def ilustrativo(serial: dict, exp: pd.DataFrame) -> dict:
    """Curvas FICTÍCIAS para PINN e paralelo (deslocamentos do serial), só para mostrar o layout com as 4 modelagens."""
    def deriva(fator, atraso):
        out = {}
        for e, c in serial.items():
            teto = min(1.0, float(exp.loc[exp["ensaio"] == e, "razao_molar_eta"].iloc[0]))
            f = lambda t, x: np.minimum(np.interp(t - atraso, c.t, c.x, left=0.0) * fator, teto)
            out[e] = rl.Curva(c.t, f(c.t, c.x), f(exp.loc[exp["ensaio"] == e, "t_min"].to_numpy(), c.x))
        return out
    return deriva(0.965, 0.10), deriva(1.03, 0.30)


def marca_ilustrativo(fig) -> None:
    fig.text(0.5, 0.5, "ILUSTRATIVO", rotation=28, fontsize=56, color="black", alpha=0.10, ha="center", va="center", zorder=100)
    fig.text(0.54, 0.885, "PINN e paralelo: curvas fictícias, só para mostrar layout e cores", ha="center", va="center", fontsize=8.5, style="italic")


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    exp = rl.carregar_experimentos()
    hib = SerialHybridModel(model_type="mlp_v2")
    fab = BatchPBMSolver(granulometry=RosinRammlerMassaAntiga(), kinetics=LeachingKinetics(alpha_nominal=5500.0), n_mesh_points=5000)
    reais = {
        "fab": rl.curvas_de_funcao(lambda ca0, eta, t: fab.simulate(ca0=ca0, eta=eta, t_eval=t)["XZn"], exp),
        "novo": rl.curvas_whitebox_novo(exp),
        "puro": curvas_mlp_pura(exp),
        "hib": rl.curvas_de_funcao(lambda ca0, eta, t: hib.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t)["XZn"], exp),
    }
    # 1) Comparação real, 4 modelos com resultado
    pg.salvar(rl.grafico_2x2([3, 9, 7, 14], exp, reais), SAIDA / "fig_comparacao_2x2_ensaios_03_09_07_14")
    pg.salvar(rl.grafico_4x4(exp, reais), SAIDA / "fig_comparacao_4x4_todos")
    por, res = rl.metricas(exp, reais)
    por.round(4).to_csv(SAIDA / "metricas_por_ensaio.csv", index=False)
    res.round(4).to_csv(SAIDA / "metricas_resumo.csv", index=False)
    print(res.round(2).to_string(index=False))

    # 2) Ilustração do layout final (4 modelagens do grupo; PINN e paralelo FICTÍCIOS)
    pinn_f, par_f = ilustrativo(reais["hib"], exp)
    grupo = {"novo": reais["novo"], "pinn": pinn_f, "par": par_f, "hib": reais["hib"]}
    fig = rl.grafico_2x2([3, 9, 7, 14], exp, grupo)
    marca_ilustrativo(fig)
    pg.salvar(fig, SAIDA / "ilustrativo_layout_4_modelagens_2x2")
    print("saída:", SAIDA)


if __name__ == "__main__":
    main()
