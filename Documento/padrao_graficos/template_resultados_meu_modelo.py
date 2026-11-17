"""TEMPLATE: gráficos da MINHA parte de Resultados (16 ensaios: 13 de treino + 3 de teste cego) contra o white-box novo.

Como usar:
  1. Copie este arquivo para a pasta da sua etapa em Código/etapas/ e renomeie (ex.: gerar_resultados_pinn.py).
  2. Troque CHAVE pela sua modelagem: "pinn", "paralelo" ou "serial". A cor, a linha e o marcador já são os do padrão.
  3. Preencha as duas funções marcadas com EDITE (carregar o seu modelo congelado e prever X_Zn). Mais nada.
  4. Rode. Saída: Código/outputs/resultados_por_modelagem/<chave>/ com 16 gráficos individuais, 4 gráficos 2x2, o 4x4,
     tabelas de métricas (treino / teste cego / global) e curvas_<chave>.csv (para a comparação final do grupo).

Não retreine nada aqui: use o modelo já treinado e congelado. O teste cego (ensaios 7, 8, 14) já foi visto; relate os
números como estão, sem escolher nada novo com base neles.

Se o seu modelo roda fora do Python (ex.: MATLAB), gere um CSV de curvas densas com colunas  ensaio, t_min, XZn
(16 ensaios, grade de resultados_lop.T_DENSO) e use CSV_DAS_CURVAS em vez de prever().
"""

import sys
from pathlib import Path


def _achar_padrao() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "Documento" / "padrao_graficos" / "resultados_lop.py").exists():
            return p
    raise FileNotFoundError("Não achei Documento/padrao_graficos/resultados_lop.py acima deste arquivo.")


RAIZ = _achar_padrao()
sys.path.insert(0, str(RAIZ / "Documento" / "padrao_graficos"))
sys.path.insert(0, str(RAIZ / "Código"))
import resultados_lop as rl  # noqa: E402

CHAVE = "pinn"          # "pinn" | "paralelo" | "serial"
CSV_DAS_CURVAS = None   # ex.: r"C:\...\minhas_curvas.csv" (só se NÃO usar prever)
T_INICIO = 0.0          # suba para 0.5 só se o seu modelo não aceita t = 0 (a curva começa nesse tempo)


def carregar_meu_modelo():
    """EDITE: carregue UMA vez o seu modelo treinado e congelado e devolva o objeto."""
    raise NotImplementedError("Preencha carregar_meu_modelo() com o seu modelo.")


def prever(modelo, ca0: float, eta: float, t):
    """EDITE: devolva X_Zn (array do MESMO tamanho de t) para C_A0 [mol/L], η [adimensional] e t [min]; T = 40 °C.

    Regras: t é um array crescente que começa em 0 (ou em T_INICIO); X_Zn em fração (0 a 1), não em %.
    """
    raise NotImplementedError("Preencha prever() com a chamada do seu modelo.")


if __name__ == "__main__":
    if CSV_DAS_CURVAS:
        rl.gerar_do_modelo(CHAVE, csv=CSV_DAS_CURVAS)
    else:
        meu = carregar_meu_modelo()
        rl.gerar_do_modelo(CHAVE, prever=lambda ca0, eta, t: prever(meu, ca0, eta, t), t_inicio=T_INICIO)
