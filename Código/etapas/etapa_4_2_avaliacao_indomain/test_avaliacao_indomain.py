"""Suíte de Testes Automatizados para a Subetapa 4.2 (Avaliação In-Domain).

Verifica a integridade dos dados, reprodução do baseline FPM puro, superioridade
estatística do Híbrido Serial, limites termodinâmicos estritos e geração dos artefatos.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

CODIGO_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = CODIGO_DIR.parent
if str(CODIGO_DIR) not in sys.path:
    sys.path.insert(0, str(CODIGO_DIR))

from src.hybrid.serial_hybrid import SerialHybridModel
from src.physics.pbm_batch import BatchPBMSolver


@pytest.fixture(scope="module")
def dataset_and_models():
    """Carrega dados experimentais e instancia resolvedores para os testes."""
    raw_meta_path = BASE_DIR / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv"
    raw_series_path = BASE_DIR / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"
    
    assert raw_meta_path.exists(), "Arquivo bancada_batelada_A1_1.csv não encontrado."
    assert raw_series_path.exists(), "Arquivo cinetica_batelada_A1_4.csv não encontrado."
    
    df_meta = pd.read_csv(raw_meta_path)
    df_series = pd.read_csv(raw_series_path)
    
    solver = BatchPBMSolver()
    hibrido = SerialHybridModel(model_type="champion")
    
    return {
        "df_meta": df_meta,
        "df_series": df_series,
        "solver": solver,
        "hibrido": hibrido,
    }


def test_experimental_data_integrity(dataset_and_models):
    """Testa se a base experimental contém 16 ensaios e 112 pontos ativos em t > 0."""
    df_meta = dataset_and_models["df_meta"]
    df_series = dataset_and_models["df_series"]
    
    assert len(df_meta) == 16, f"Esperado 16 ensaios nos metadados, obtido {len(df_meta)}"
    df_pos = df_series[df_series["t_min"] > 0.0]
    assert len(df_pos) == 112, f"Esperado 112 observações ativas (t > 0), obtido {len(df_pos)}"
    
    ensaios_presentes = set(df_pos["ensaio"].unique())
    assert ensaios_presentes == set(range(1, 17)), "Faltam ensaios na base experimental."
    
    assert df_pos["t_min"].min() == 0.5
    assert df_pos["t_min"].max() == 15.0
    assert df_pos["XZn"].min() > 0.0
    assert df_pos["XZn"].max() <= 1.05


def test_fpm_baseline_reproduction(dataset_and_models):
    """Testa se o White-Box Puro (RRB ÷ D³, Sem α) reproduz o baseline da Etapa 1.3 em t > 0 (R² ~ 0.8709, RMSE ~ 0.0702)."""
    df_meta = dataset_and_models["df_meta"]
    df_series = dataset_and_models["df_series"]
    solver = dataset_and_models["solver"]
    
    y_true = []
    y_pred_fpm = []
    
    for ens_id in range(1, 17):
        sub_meta = df_meta[df_meta["ensaio"] == ens_id].iloc[0]
        sub_series = df_series[(df_series["ensaio"] == ens_id) & (df_series["t_min"] > 0.0)].sort_values("t_min")
        
        ca0 = float(sub_meta["CA0_mol_L"])
        eta = float(sub_meta["razao_molar_eta"])
        t_exp = sub_series["t_min"].values
        x_exp = sub_series["XZn"].values
        
        res_fpm = solver.simulate(ca0=ca0, eta=eta, t_eval=t_exp, alpha=0.0)
        y_true.extend(x_exp)
        y_pred_fpm.extend(res_fpm["XZn"])
        
    y_true = np.array(y_true)
    y_pred_fpm = np.array(y_pred_fpm)
    
    r2_fpm = 1.0 - np.sum((y_true - y_pred_fpm) ** 2) / np.sum((y_true - np.mean(y_true)) ** 2)
    rmse_fpm = np.sqrt(np.mean((y_true - y_pred_fpm) ** 2))
    
    assert abs(r2_fpm - 0.8709) < 0.010, f"R² do FPM (t > 0) divergiu: {r2_fpm:.4f} vs 0.8709"
    assert abs(rmse_fpm - 0.0702) < 0.010, f"RMSE do FPM (t > 0) divergiu: {rmse_fpm:.4f} vs 0.0702"


def test_hybrid_serial_superiority_over_fpm(dataset_and_models):
    """Testa se o Híbrido Serial (MLP Campeão) supera o White-Box Puro em t > 0 (N = 112 pontos)."""
    df_meta = dataset_and_models["df_meta"]
    df_series = dataset_and_models["df_series"]
    hibrido = dataset_and_models["hibrido"]
    
    y_true = []
    y_pred_hib = []
    
    for ens_id in range(1, 17):
        sub_meta = df_meta[df_meta["ensaio"] == ens_id].iloc[0]
        sub_series = df_series[(df_series["ensaio"] == ens_id) & (df_series["t_min"] > 0.0)].sort_values("t_min")
        
        ca0 = float(sub_meta["CA0_mol_L"])
        eta = float(sub_meta["razao_molar_eta"])
        t_exp = sub_series["t_min"].values
        x_exp = sub_series["XZn"].values
        
        res_hib = hibrido.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t_exp)
        y_true.extend(x_exp)
        y_pred_hib.extend(res_hib["XZn"])
        
    y_true = np.array(y_true)
    y_pred_hib = np.array(y_pred_hib)
    
    r2_hib = 1.0 - np.sum((y_true - y_pred_hib) ** 2) / np.sum((y_true - np.mean(y_true)) ** 2)
    rmse_hib = np.sqrt(np.mean((y_true - y_pred_hib) ** 2))
    
    assert r2_hib >= 0.940, f"R² Híbrido (t > 0) abaixo de 0.940: {r2_hib:.4f}"
    assert rmse_hib <= 0.050, f"RMSE Híbrido (t > 0) acima de 0.050: {rmse_hib:.4f}"
    
    # Redução de erro relativa sobre o White-Box Puro (RMSE = 0.0702)
    rmse_fpm = 0.0702
    reduc_pct = ((rmse_fpm - rmse_hib) / rmse_fpm) * 100.0
    assert reduc_pct >= 25.0, f"Redução de erro foi de apenas {reduc_pct:.1f}%"


def test_blind_test_performance(dataset_and_models):
    """Testa se o desempenho nos ensaios de teste cego (7, 8, 14) em t > 0 (N = 21 pts) atinge alta acurácia."""
    df_meta = dataset_and_models["df_meta"]
    df_series = dataset_and_models["df_series"]
    hibrido = dataset_and_models["hibrido"]
    test_ensaios = [7, 8, 14]
    
    y_true_te = []
    y_pred_te = []
    
    for ens_id in test_ensaios:
        sub_meta = df_meta[df_meta["ensaio"] == ens_id].iloc[0]
        sub_series = df_series[(df_series["ensaio"] == ens_id) & (df_series["t_min"] > 0.0)].sort_values("t_min")
        
        ca0 = float(sub_meta["CA0_mol_L"])
        eta = float(sub_meta["razao_molar_eta"])
        t_exp = sub_series["t_min"].values
        x_exp = sub_series["XZn"].values
        
        res_hib = hibrido.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t_exp)
        y_true_te.extend(x_exp)
        y_pred_te.extend(res_hib["XZn"])
        
    y_true_te = np.array(y_true_te)
    y_pred_te = np.array(y_pred_te)
    
    r2_te = 1.0 - np.sum((y_true_te - y_pred_te) ** 2) / np.sum((y_true_te - np.mean(y_true_te)) ** 2)
    rmse_te = np.sqrt(np.mean((y_true_te - y_pred_te) ** 2))
    
    # Em t > 0 (sem t=0), os 3 ensaios de teste [7, 8, 14] possuem X_Zn ∈ [0.81, 1.00] (std = 0.060);
    # O FPM Puro obtém R² = -0.6747 e RMSE = 0.0780, enquanto o Híbrido reduz o RMSE para <= 0.045 e R² >= 0.50
    assert r2_te >= 0.50, f"R² de Teste Cego (t > 0) abaixo de 0.50: {r2_te:.4f}"
    assert rmse_te <= 0.045, f"RMSE de Teste Cego (t > 0) acima de 0.045: {rmse_te:.4f}"


def test_physical_constraints_all_assays(dataset_and_models):
    """Testa a conformidade física em todos os 16 ensaios: 0 <= X_Zn <= min(1, eta) e CAf >= 0."""
    df_meta = dataset_and_models["df_meta"]
    hibrido = dataset_and_models["hibrido"]
    t_eval = np.linspace(0.0, 15.0, 100)
    
    for ens_id in range(1, 17):
        sub_meta = df_meta[df_meta["ensaio"] == ens_id].iloc[0]
        ca0 = float(sub_meta["CA0_mol_L"])
        eta = float(sub_meta["razao_molar_eta"])
        
        sim = hibrido.simulate(T=40.0, ca0=ca0, eta=eta, t_eval=t_eval)
        
        xzn = sim["XZn"]
        caf = sim["CAf"]
        delta = sim["delta"]
        
        assert np.all(xzn >= 0.0), f"Ensaio {ens_id}: conversão negativa detectada."
        assert np.all(xzn <= 1.0 + 1e-7), f"Ensaio {ens_id}: conversão acima de 1.0."
        assert np.all(xzn <= min(1.0, eta) + 1e-6), f"Ensaio {ens_id}: conversão excedeu teto estequiométrico eta={eta}."
        assert np.all(caf >= 0.0), f"Ensaio {ens_id}: concentração de ácido negativa detectada."
        assert np.all(np.diff(delta) >= -1e-6), f"Ensaio {ens_id}: delta não-monotônico."


def test_output_artifacts_exist():
    """Testa se todos os 5 pares de figuras (PNG + PDF), 3 tabelas CSV e relatórios foram gerados."""
    out_dir = CODIGO_DIR / "outputs" / "etapa_4_2_avaliacao_indomain"
    assert out_dir.exists(), "Diretório de outputs da etapa 4.2 não existe."
    
    expected_figures = [
        "fig_12a_reconstrucao_XZn_hibrido_16_ensaios",
        "fig_12a_reconstrucao_XZn_hibrido_16_ensaios_log",
        "fig_12b_paridade_XZn_3modelos",
        "fig_12c_comparativo_global_XZn_barras",
        "fig_12d_heatmap_ganho_relativo_hibrido",
    ]
    
    for fig_stem in expected_figures:
        png_file = out_dir / f"{fig_stem}.png"
        pdf_file = out_dir / f"{fig_stem}.pdf"
        assert png_file.exists() and png_file.stat().st_size > 1000, f"Figura PNG inválida: {png_file.name}"
        assert pdf_file.exists() and pdf_file.stat().st_size > 1000, f"Figura PDF inválida: {pdf_file.name}"
        
    expected_tables = [
        "tabela_predicoes_detalhadas_16_ensaios.csv",
        "tabela_metricas_indomain_hibrido_vs_fpm.csv",
        "tabela_comparativo_quatro_hibridos_XZn.csv",
    ]
    for tab_file in expected_tables:
        f = out_dir / tab_file
        assert f.exists() and f.stat().st_size > 100, f"Tabela CSV inválida: {tab_file}"
        
    assert (out_dir / "relatorio_etapa_4_2_hibrido_indomain.md").exists()
    assert (out_dir / "fundamentacao_acoplamento_hibrido_LOP.md").exists()
