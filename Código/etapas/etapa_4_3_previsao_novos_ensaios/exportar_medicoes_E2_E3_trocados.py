"""Exporta as medições dos 4 ensaios novos em X_Zn com os rótulos E2 e E3 trocados em relação à planilha.

Hipótese adotada pelo grupo em 10/11/2026 (o laboratório ainda não confirmou): as concentrações de Zn registradas
como "E3" só são compatíveis com a massa de sólido do E2 (12,1 g), e as do "E2", com a do E3 (6,7 g). A conversão em
X_Zn é a de `analisar_medicoes_novos.py` (X = C_Zn V / (m w), w calibrado nos 16 ensaios originais, coluna da planilha
lida como g/L). A planilha e o CSV "como rotulado" não são alterados.

Saída: Base de dados/Experimentos novos/medicoes_XZn_ensaios_novos_E2_E3_trocados.csv (ensaio, t_min, XZn), usada por
`Documento/padrao_graficos/resultados_lop.py` (todas as modelagens leem o mesmo arquivo).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analisar_medicoes_novos as an  # noqa: E402

SAIDA = an.BASE / "Experimentos novos" / "medicoes_XZn_ensaios_novos_E2_E3_trocados.csv"

if __name__ == "__main__":
    w, w_dp = an.calibrar_teor_zn()
    conv = an.converter(an.ler_planilha(), w, troca=True)
    conv = conv[conv["t_min"] > 0].sort_values(["ensaio", "t_min"])
    assert len(conv) == 24 and sorted(conv["ensaio"].unique()) == ["E1", "E2", "E3", "E4"]
    assert conv["XZn_medido"].max() < 1.0, "com a troca, nenhuma conversão medida deveria passar de 1"
    conv.rename(columns={"XZn_medido": "XZn"})[["ensaio", "t_min", "XZn", "Zn_licor_g_L", "m_g"]].to_csv(SAIDA, index=False)
    print(f"w = {w:.4f} ± {w_dp:.4f} g Zn/g; gravado {SAIDA.name}")
    print(conv.pivot(index="t_min", columns="ensaio", values="XZn_medido").round(3).to_string())
