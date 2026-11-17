"""Gráficos da parte de Resultados do HÍBRIDO SERIAL (comitê MLP v2 -> PBM) contra o white-box novo.

Preenchimento do template `Documento/padrao_graficos/template_resultados_meu_modelo.py` para a modelagem serial:
16 individuais, 4 gráficos 2x2, 1 gráfico 4x4, métricas e curvas. Só leitura do comitê congelado; nada é treinado.
Saída: Código/outputs/resultados_por_modelagem/serial/
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "Documento" / "padrao_graficos"))
sys.path.insert(0, str(RAIZ / "Código"))
import resultados_lop as rl  # noqa: E402
from src.hybrid.serial_hybrid import SerialHybridModel  # noqa: E402

modelo = SerialHybridModel(model_type="mlp_v2")


def prever(ca0, eta, t):
    return modelo.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t)["XZn"]


if __name__ == "__main__":
    rl.gerar_do_modelo("serial", prever=prever)
    # 4 ensaios novos: mesmo comitê congelado, sem novo ajuste; confere com a previsão a priori registrada em 08/11
    import pandas as pd
    pasta = rl.gerar_ensaios_novos("serial", prever=prever)
    novos = pd.read_csv(pasta / "dados_plotados_ensaios_novos.csv")
    priori = pd.read_csv(RAIZ / "Código" / "outputs" / "etapa_4_3_previsao_novos_ensaios" / "previsao_a_priori_instantes_amostrados.csv")
    junto = novos.merge(priori[["ensaio", "t_min", "XZn_v2_comite"]], on=["ensaio", "t_min"], validate="one_to_one")
    assert len(junto) == len(novos) == 24 and (junto["XZn_serial"] - junto["XZn_v2_comite"]).abs().max() < 1e-6,         "a previsão dos ensaios novos deixou de coincidir com a previsão a priori"
    print(pd.read_csv(pasta / "metricas_ensaios_novos.csv").to_string(index=False))
