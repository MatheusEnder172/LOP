"""Suíte de Testes Automatizados para a Subetapa 3.2.5 (Comparação e Seleção do Campeão).

Verifica a integridade das tabelas consolidadas, a validade do ranking multicritério MCDA,
a geração das 5 figuras em 300 DPI (PNG e PDF) e a correta persistência dos metadados
do modelo campeão para acoplamento na Etapa 4.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

# Definição de caminhos
SCRIPT_DIR = Path(__file__).resolve().parent
ETAPA_3_2_DIR = SCRIPT_DIR.parent
ETAPAS_DIR = ETAPA_3_2_DIR.parent
CODIGO_DIR = ETAPAS_DIR.parent
OUTPUTS_DIR = CODIGO_DIR / "outputs" / "etapa_3_2" / "subetapa_3_2_5_comparacao_campeao"
MODELS_DIR = CODIGO_DIR / "outputs" / "models_saved"


def test_arquivos_saida_existem() -> None:
    """Verifica se todos os artefatos obrigatórios foram gerados na pasta de saídas."""
    arquivos_esperados = [
        # Tabelas
        "tabela_consolidada_modelos_blackbox.csv",
        "tabela_comparativa_ensaios_teste.csv",
        "tabela_todos_16_ensaios_4_modelos.csv",
        "tabela_ranking_multicriterio_mcda.csv",
        # Relatórios
        "relatorio_consolidado_modelos_blackbox.md",
        "fundamentacao_comparacao_e_selecao_campeao_LOP.md",
        # Figuras PNG
        "fig_11a_comparativo_global_metricas.png",
        "fig_11b_paridade_consolidada_4_modelos.png",
        "fig_11b_paridade_consolidada_4_modelos_log.png",
        "fig_11c_trajetorias_comparativas_teste.png",
        "fig_11c_trajetorias_comparativas_teste_log.png",
        "fig_11d_distribuicao_residuos_boxplots.png",
        "fig_11e_radar_selecao_campeao.png",
        # Figuras PDF
        "fig_11a_comparativo_global_metricas.pdf",
        "fig_11b_paridade_consolidada_4_modelos.pdf",
        "fig_11b_paridade_consolidada_4_modelos_log.pdf",
        "fig_11c_trajetorias_comparativas_teste.pdf",
        "fig_11c_trajetorias_comparativas_teste_log.pdf",
        "fig_11d_distribuicao_residuos_boxplots.pdf",
        "fig_11e_radar_selecao_campeao.pdf",
    ]

    for arq in arquivos_esperados:
        p = OUTPUTS_DIR / arq
        assert p.exists(), f"Arquivo de saída obrigatório não encontrado: {p}"
        assert p.stat().st_size > 0, f"Arquivo de saída está vazio: {p}"


def test_modelo_campeao_info_json() -> None:
    """Verifica a integridade e consistência dos metadados do modelo campeão."""
    info_path = MODELS_DIR / "modelo_campeao_info.json"
    assert info_path.exists(), f"Arquivo não encontrado: {info_path}"

    with open(info_path, "r", encoding="utf-8") as f:
        info = json.load(f)

    assert "modelo_campeao" in info
    assert info["modelo_campeao"] == "Random Forest"
    assert info["score_mcda"] >= 75.0

    crit = info["criterios_chave"]
    assert crit["R2_teste_cego"] >= 0.90
    assert crit["RMSE_teste_um_min"] <= 20.0
    assert crit["violacao_fisica_pct"] == 0.0

    # Verificar que o arquivo de checkpoint apontado existe no disco
    ckpt_rel = info["arquivos_acoplamento_etapa_4"]["checkpoint_relativo"]
    ckpt_full = MODELS_DIR / ckpt_rel
    assert ckpt_full.exists(), f"Checkpoint do campeão apontado não existe: {ckpt_full}"


def test_consistencia_tabela_mcda() -> None:
    """Valida as propriedades estatísticas e de ordenação da tabela MCDA."""
    df_mcda = pd.read_csv(OUTPUTS_DIR / "tabela_ranking_multicriterio_mcda.csv")

    assert len(df_mcda) == 4
    modelos_presentes = set(df_mcda["modelo"])
    assert modelos_presentes == {"MLP", "Random Forest", "SVR", "XGBoost"}

    # Scores devem estar em ordem decrescente
    scores = df_mcda["score_total_mcda"].tolist()
    assert scores == sorted(scores, reverse=True)

    # Todos os scores devem estar no intervalo [0, 100]
    for s in scores:
        assert 0.0 <= s <= 100.0

    # O campeão deve ser Random Forest
    assert df_mcda.iloc[0]["modelo"] == "Random Forest"
    assert df_mcda.iloc[0]["posicao_ranking"] == 1


def test_consistencia_metricas_consolidadas() -> None:
    """Valida as métricas da tabela consolidada global."""
    df_cons = pd.read_csv(OUTPUTS_DIR / "tabela_consolidada_modelos_blackbox.csv")
    assert len(df_cons) == 4

    for _, row in df_cons.iterrows():
        # Restrição inegociável de conservação de massa
        assert row["violacao_fisica_pct"] == 0.0, f"Modelo {row['modelo']} violou restrição física!"

        # Verificação de coerência de R²
        assert row["R2_treino"] > 0.10
        assert row["R2_teste_cego"] > 0.50
        assert row["RMSE_teste_um_min"] > 0.0
        assert row["MAE_teste_um_min"] > 0.0

    # Checagens específicas dos desempenhos de teste
    r2_rf = df_cons.loc[df_cons["modelo"] == "Random Forest", "R2_teste_cego"].values[0]
    r2_mlp = df_cons.loc[df_cons["modelo"] == "MLP", "R2_teste_cego"].values[0]
    r2_xgb = df_cons.loc[df_cons["modelo"] == "XGBoost", "R2_teste_cego"].values[0]
    r2_svr = df_cons.loc[df_cons["modelo"] == "SVR", "R2_teste_cego"].values[0]

    assert r2_rf >= 0.90
    assert r2_mlp >= 0.82
    assert r2_xgb >= 0.80
    assert r2_svr >= 0.60


def test_consistencia_ensaios_teste() -> None:
    """Verifica a desagregação das métricas nos 3 ensaios de teste cego (8, 14 e 7)."""
    df_ens = pd.read_csv(OUTPUTS_DIR / "tabela_comparativa_ensaios_teste.csv")
    assert len(df_ens) == 12  # 3 ensaios × 4 modelos

    ensaios_presentes = set(df_ens["ensaio"])
    assert ensaios_presentes == {8, 14, 7}

    # No Ensaio 8, XGBoost é recordista com R² > 0.97
    sub_8 = df_ens[df_ens["ensaio"] == 8]
    r2_xgb_8 = sub_8.loc[sub_8["modelo"] == "XGBoost", "R2"].values[0]
    assert r2_xgb_8 > 0.97

    # No Ensaio 14, SVR e MLP atingem R² > 0.96
    sub_14 = df_ens[df_ens["ensaio"] == 14]
    r2_svr_14 = sub_14.loc[sub_14["modelo"] == "SVR", "R2"].values[0]
    r2_mlp_14 = sub_14.loc[sub_14["modelo"] == "MLP", "R2"].values[0]
    assert r2_svr_14 > 0.96
    assert r2_mlp_14 > 0.96

    # No Ensaio 7, Random Forest lidera com R² > 0.87
    sub_7 = df_ens[df_ens["ensaio"] == 7]
    r2_rf_7 = sub_7.loc[sub_7["modelo"] == "Random Forest", "R2"].values[0]
    assert r2_rf_7 > 0.87
