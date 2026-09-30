"""Suíte de Testes Automatizados para a Subetapa 4.1: Orquestrador Híbrido Serial.

Valida a classe `SerialHybridModel`, assegurando interoperabilidade com todos os modelos DDM,
conservação estrita de massa, monotonicidade da conversão de zinco X_Zn(t), não-negatividade
do ácido residual C_Af(t) e aderência em simulações individuais e em lote.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Inclusão do diretório Código no sys.path
CODIGO_DIR = Path(__file__).resolve().parents[2]
if str(CODIGO_DIR) not in sys.path:
    sys.path.insert(0, str(CODIGO_DIR))

from src.hybrid.serial_hybrid import SerialHybridModel


def test_instanciacao_padrao_modelo_campeao() -> None:
    """Verifica se a instanciação sem parâmetros carrega automaticamente o modelo campeão."""
    hibrido = SerialHybridModel()
    assert hibrido.model_type == "random_forest"
    assert "Random Forest" in hibrido.model_name
    assert hibrido.model is not None
    assert hibrido.solver is not None


def test_interoperabilidade_todos_modelos() -> None:
    """Verifica se o orquestrador funciona de forma intercambiável com os 4 modelos DDM."""
    modelos = ["champion", "random_forest", "mlp", "xgboost", "svr"]
    t_eval = np.linspace(0.0, 15.0, 31)

    for m_type in modelos:
        hibrido = SerialHybridModel(model_type=m_type)
        res = hibrido.simulate(T=40.0, ca0=0.50, eta=1.0, t_eval=t_eval)

        # Verificação de estrutura das saídas
        assert "t" in res
        assert "delta" in res
        assert "XZn" in res
        assert "CAf" in res
        assert "abs_v" in res
        assert "v" in res

        # Verificação dimensional
        assert len(res["t"]) == len(t_eval)
        assert len(res["XZn"]) == len(t_eval)
        assert len(res["CAf"]) == len(t_eval)

        # Restrição física básica
        assert 0.0 <= res["XZn"][-1] <= 1.0
        assert res["CAf"][-1] >= 0.0


def test_restricao_fisica_conservacao_massa() -> None:
    """Garante conservação estrita de massa sob diversas condições operacionais e limites."""
    hibrido = SerialHybridModel()
    t_eval = np.linspace(0.0, 15.0, 41)

    condicoes = [
        {"T": 40.0, "ca0": 0.10, "eta": 0.50},  # Diluído e limitante
        {"T": 40.0, "ca0": 1.50, "eta": 0.50},  # Concentrado e limitante
        {"T": 40.0, "ca0": 0.50, "eta": 1.00},  # Estequiométrico neutro
        {"T": 40.0, "ca0": 1.00, "eta": 1.50},  # Leve excesso
        {"T": 40.0, "ca0": 0.10, "eta": 3.10},  # Forte excesso diluído
        {"T": 40.0, "ca0": 1.50, "eta": 3.10},  # Forte excesso concentrado
        {"T": 50.0, "ca0": 0.80, "eta": 2.00},  # Condição arbitrária
    ]

    for c in condicoes:
        res = hibrido.simulate(T=c["T"], ca0=c["ca0"], eta=c["eta"], t_eval=t_eval)

        # 1. Conversão de zinco estritamente em [0, 1]
        assert np.all(res["XZn"] >= 0.0), f"Conversão negativa em {c}"
        assert np.all(res["XZn"] <= 1.0), f"Conversão superior a 1 em {c}"
        assert res["XZn"][0] == 0.0, "Conversão inicial deve ser nula"

        # 2. Ácido livre estritamente não-negativo
        assert np.all(res["CAf"] >= 0.0), f"Ácido negativo em {c}"
        assert np.isclose(res["CAf"][0], c["ca0"], atol=1e-6), "Ácido inicial deve ser CA0"

        # 3. Taxa de retração não-negativa
        assert np.all(res["abs_v"] >= 0.0), f"Taxa de retração negativa em {c}"
        assert np.all(res["v"] <= 0.0), f"Taxa diametral positiva em {c}"

        # 4. Deslocamento acumulado estritamente não-negativo
        assert np.all(res["delta"] >= 0.0)
        assert res["delta"][0] == 0.0


def test_monotonicidade_conversao_e_retracao() -> None:
    """Verifica que a conversão X_Zn e a retração delta são monotonicamente não-decrescentes."""
    hibrido = SerialHybridModel()
    t_eval = np.linspace(0.0, 15.0, 61)

    for ca0 in [0.20, 0.50, 1.20]:
        for eta in [0.50, 1.00, 3.10]:
            res = hibrido.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t_eval)

            diff_xzn = np.diff(res["XZn"])
            diff_delta = np.diff(res["delta"])
            diff_caf = np.diff(res["CAf"])

            # Conversão não pode diminuir ao longo do tempo (dissolução irreversível)
            assert np.all(diff_xzn >= -1e-9), f"Quebra de monotonicidade em XZn (ca0={ca0}, eta={eta})"
            # Retração acumulada não pode diminuir
            assert np.all(diff_delta >= -1e-9), f"Quebra de monotonicidade em delta (ca0={ca0}, eta={eta})"
            # Ácido livre não pode aumentar (sem geração de ácido)
            assert np.all(diff_caf <= 1e-9), f"Ácido aumentou espontaneamente (ca0={ca0}, eta={eta})"


def test_simulacao_ensaio_real_e_residuos() -> None:
    """Verifica a simulação direta dos ensaios de teste cego (8, 14 e 7) e calcula métricas."""
    hibrido = SerialHybridModel()

    for ens in [8, 14, 7]:
        res = hibrido.simulate_experiment(ensaio_id=ens, use_experimental_timepoints_only=True)

        assert res["ensaio"] == ens
        assert len(res["t"]) == 8
        assert len(res["XZn_exp"]) == 8
        assert "residuos_XZn" in res

        residuos = res["residuos_XZn"]
        y_true = res["XZn_exp"]
        ss_res = np.sum(residuos ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot)
        rmse = np.sqrt(np.mean(residuos ** 2))

        # O modelo híbrido deve apresentar excelente acurácia nos ensaios intocados
        assert r2 >= 0.90, f"R² insatisfatório no Ensaio {ens}: {r2:.4f}"
        assert rmse <= 0.06, f"RMSE insatisfatório no Ensaio {ens}: {rmse:.4f}"


def test_simulacao_lote_dataframe() -> None:
    """Verifica a execução de simulação em lote para múltiplos ensaios."""
    hibrido = SerialHybridModel()
    ensaios = [1, 8, 14]
    df_batch = hibrido.simulate_batch(ensaios_list=ensaios, use_experimental_timepoints_only=True)

    assert isinstance(df_batch, pd.DataFrame)
    assert len(df_batch) == len(ensaios) * 8  # 3 ensaios × 8 instantes

    colunas_esperadas = [
        "ensaio",
        "t_min",
        "XZn_pred",
        "CAf_pred",
        "abs_v_pred",
        "delta_pred",
        "CA0_mol_L",
        "razao_molar_eta",
        "temperatura_C",
        "modelo",
        "XZn_exp",
        "residuo_XZn",
    ]
    for col in colunas_esperadas:
        assert col in df_batch.columns, f"Coluna obrigatória ausente: {col}"

    # Sem NaNs ou infinitos
    assert not df_batch.isnull().values.any()


def test_erros_de_entrada_invalidos() -> None:
    """Verifica o tratamento de erros para entradas fisicamente inválidas."""
    hibrido = SerialHybridModel()

    with pytest.raises(ValueError, match="CA0 deve ser estritamente positivo"):
        hibrido.simulate(ca0=-0.1, eta=1.0)

    with pytest.raises(ValueError, match="eta deve ser estritamente positivo"):
        hibrido.simulate(ca0=0.5, eta=0.0)

    with pytest.raises(ValueError, match="monotonicamente crescente"):
        hibrido.simulate(ca0=0.5, eta=1.0, t_eval=[5.0, 2.0, 10.0])
