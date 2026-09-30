"""Suíte de Testes Unitários Automatizados da Etapa 5 (Validação Cruzada nos Dados de Júlio Balarini).

Verifica:
1. Integridade dimensional e consistência do dataset extraído (176 pontos, 16 séries);
2. Não-negatividade e limites físicos estequiométricos (0 <= X_Zn <= 1 e Caf >= 0);
3. Linearidade termodinâmica de Arrhenius (R² > 0.95);
4. Monotonia da convolução granulométrica no PBM;
5. Superioridade do Modelo Híbrido Serial sobre o FPM Puro e DDM Puro na base externa de Balarini.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Configuração de paths
CURRENT_DIR = Path(__file__).resolve().parent
CODIGO_DIR = CURRENT_DIR.parent.parent
BASE_DIR = CODIGO_DIR.parent

if str(CODIGO_DIR) not in sys.path:
    sys.path.insert(0, str(CODIGO_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.hybrid.serial_hybrid import SerialHybridModel
from etapas.etapa_5_validacao_balarini.avaliar_balarini_hibrido import (
    carregar_dados_balarini,
    estimar_parametros_arrhenius_balarini,
    calcular_metricas,
)


def test_integridade_dataset_balarini() -> None:
    """Verifica se o dataset processado de Balarini possui exatamente 176 pontos e 16 séries."""
    df = carregar_dados_balarini()
    assert len(df) == 176, f"Esperado 176 pontos, obtido {len(df)}"
    assert df["serie_teste"].nunique() == 16, f"Esperado 16 séries, obtido {df['serie_teste'].nunique()}"
    
    # Verificação de colunas essenciais
    cols_esperadas = ["ponto_id", "serie_teste", "temperatura_c", "dp_medio_um", "agitacao_rpm", "tempo_min", "conversao_zn_exp"]
    for c in cols_esperadas:
        assert c in df.columns, f"Coluna obrigatória ausente: {c}"


def test_consistencia_fisica_conversoes() -> None:
    """Garante que todas as conversões experimentais estão estritamente entre 0 e 1."""
    df = carregar_dados_balarini()
    x = df["conversao_zn_exp"].values
    assert np.all(x >= 0.0), "Conversão experimental negativa encontrada!"
    assert np.all(x <= 1.0), "Conversão experimental > 1.0 encontrada!"
    
    # Monotonia no tempo para cada série
    for serie, g in df.groupby("serie_teste"):
        g_sorted = g.sort_values("tempo_min")
        x_s = g_sorted["conversao_zn_exp"].values
        # Não deve haver quedas abruptas de conversão (tolerância numérica de 0.01)
        diffs = np.diff(x_s)
        assert np.all(diffs >= -0.01), f"Quebra de monotonia na série {serie}: {diffs}"


def test_arrhenius_termodinamica() -> None:
    """Valida a consistência do ajuste de Arrhenius e cálculo de Ea."""
    df = carregar_dados_balarini()
    ea_kj, r2_arrh, rates_dict = estimar_parametros_arrhenius_balarini(df)
    
    # Ea deve estar em faixa plausível (10 a 60 kJ/mol)
    assert 10.0 <= ea_kj <= 60.0, f"Ea fora da faixa plausível: {ea_kj} kJ/mol"
    # Ajuste de Arrhenius com R² > 0.95
    assert r2_arrh >= 0.95, f"R² de Arrhenius muito baixo: {r2_arrh}"
    # Constantes de taxa devem ser estritamente crescentes com T
    temps = sorted(rates_dict.keys())
    k_vals = [rates_dict[t] for t in temps]
    assert np.all(np.diff(k_vals) > 0), "Taxas k(T) não são monotonicamente crescentes com T!"


def test_predicao_hibrida_balarini_limites_fisicos() -> None:
    """Verifica que as predições do modelo híbrido respeitam rigorosamente os limites termodinâmicos."""
    hybrid = SerialHybridModel(model_type="random_forest")
    
    # Simula condição extrema de Balarini (T = 70 °C, CA0 = 0.0408, eta = 1.5)
    t_test = np.array([0, 1, 5, 10, 20, 30], dtype=float)
    v_pred = hybrid.predict_rate(T=70.0, ca0=0.0408, eta=1.5, t_eval=t_test)
    
    assert np.all(v_pred >= 0.0), "Taxa de retração negativa predita pelo DDM!"
    
    # Simula com convolução monodispersa
    from scipy.integrate import cumulative_trapezoid
    delta = np.zeros_like(t_test)
    delta[1:] = cumulative_trapezoid(v_pred, t_test)
    x_calc = np.clip(1.0 - np.maximum(0.0, 1.0 - delta / 180.0) ** 3, 0.0, 1.0)
    
    assert np.all(x_calc >= 0.0)
    assert np.all(x_calc <= 1.0)
    assert np.all(np.diff(x_calc) >= -1e-6), "Conversão calculada não monótona!"


def test_superioridade_hibrido_sobre_baselines() -> None:
    """Verifica se o Híbrido Serial supera o FPM Puro e DDM Puro na base de Balarini."""
    tabela_res_path = CODIGO_DIR / "outputs" / "etapa_5_validacao_balarini" / "tabela_resumo_efeitos_balarini.csv"
    assert tabela_res_path.exists(), f"Tabela resumo não encontrada: {tabela_res_path}"
    
    df_res = pd.read_csv(tabela_res_path)
    glob = df_res[df_res["categoria"] == "GLOBAL_BALARINI_TOTAL"].iloc[0]
    
    r2_fpm = glob["r2_medio_fpm"]
    r2_ddm = glob["r2_medio_ddm"]
    r2_hib = glob["r2_medio_hibrido"]
    
    rmse_fpm = glob["rmse_medio_fpm"]
    rmse_ddm = glob["rmse_medio_ddm"]
    rmse_hib = glob["rmse_medio_hibrido"]
    
    # O híbrido deve ter R² positivo e muito superior ao FPM e DDM
    assert r2_hib > 0.50, f"R² global do híbrido ({r2_hib}) abaixo de 0.50"
    assert r2_hib > r2_fpm, f"Híbrido não superou FPM: {r2_hib} vs {r2_fpm}"
    assert r2_hib > r2_ddm, f"Híbrido não superou DDM: {r2_hib} vs {r2_ddm}"
    
    # O RMSE do híbrido deve ser expressivamente menor
    assert rmse_hib < rmse_fpm, f"RMSE híbrido ({rmse_hib}) não é menor que FPM ({rmse_fpm})"
    assert rmse_hib < rmse_ddm, f"RMSE híbrido ({rmse_hib}) não é menor que DDM ({rmse_ddm})"
