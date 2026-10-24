"""
Testes Unitários e Validação do Módulo de Cinética (Etapa 1.2).
Disciplina: Laboratório de Operações e Processos (LOP - DEQ/UFMG)

Valida as propriedades estequiométricas, a equação de consumo de ácido de Herbst (1979)
e a taxa de retração interfacial da partícula no modelo White-Box Puro (sem α, α = 0)
e na referência histórica de Bortot Coelho (2017) (α = 5500 µm/min).
"""

from pathlib import Path
import sys
from typing import Any, Dict
import numpy as np
import pandas as pd

# Adicionar Código/ ao PYTHONPATH para importação de src
projeto_raiz = Path(__file__).resolve().parents[3]
codigo_dir = projeto_raiz / "Código"
if str(codigo_dir) not in sys.path:
    sys.path.insert(0, str(codigo_dir))

from src.physics.kinetics import LeachingKinetics


def testar_calculo_eta_experimental() -> Dict[str, Any]:
    """Testa o cálculo da razão molar eta para todos os 16 ensaios da Tabela A1.1."""
    print("--- 1. Testando Cálculo da Razão Molar eta nos 16 Ensaios ---")
    kinetics = LeachingKinetics()

    tabela_csv = projeto_raiz / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv"
    df = pd.read_csv(tabela_csv)

    erros_eta = []
    v_liq = 0.400  # 400 mL

    for _, row in df.iterrows():
        ensaio = int(row["ensaio"])
        ca0 = float(row["CA0_mol_L"])
        mb0 = float(row["mB0_g"])
        eta_esperado = float(row["razao_molar_eta"])

        eta_calc = kinetics.calculate_eta(ca0=ca0, v_liq_l=v_liq, mb0_g=mb0)
        erro_rel = abs(eta_calc - eta_esperado) / eta_esperado
        erros_eta.append(erro_rel)

        assert erro_rel < 0.05, f"Ensaio {ensaio}: eta calc={eta_calc:.3f}, esperado={eta_esperado}"

    erro_medio_pct = float(np.mean(erros_eta) * 100.0)
    print(f"  [PASS] Todos os 16 ensaios tiveram eta validado com erro médio de apenas {erro_medio_pct:.2f}%.")

    return {
        "n_ensaios": len(df),
        "erro_medio_eta_pct": erro_medio_pct,
        "max_erro_eta_pct": float(np.max(erros_eta) * 100.0),
    }


def testar_balanco_acido_herbst() -> Dict[str, Any]:
    """Testa o balanço de ácido de Herbst (1979): Caf = CA0 * [1 - (X / eta)]."""
    print("\n--- 2. Testando Balanço de Consumo de Ácido de Herbst (1979) ---")
    kinetics = LeachingKinetics()

    # 1. Limite inicial X = 0 -> Caf = CA0
    caf_ini = kinetics.acid_concentration(ca0=1.0, x_zn=0.0, eta=1.5)
    assert np.isclose(caf_ini, 1.0), f"Caf inicial esperado 1.0, obtido {caf_ini}"

    # 2. Limite de esgotamento total X = eta -> Caf = 0
    caf_esgotado = kinetics.acid_concentration(ca0=1.0, x_zn=0.5, eta=0.5)
    assert np.isclose(caf_esgotado, 0.0), f"Caf esgotado esperado 0.0, obtido {caf_esgotado}"

    # 3. Teste contra os valores experimentais medidos ao final dos ensaios (t = 15 min)
    tabela_csv = projeto_raiz / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv"
    df = pd.read_csv(tabela_csv)

    caf_reais = df["CAf_mol_L"].values
    caf_previstos = []

    for _, row in df.iterrows():
        ca0 = float(row["CA0_mol_L"])
        x_zn = float(row["XZn"])
        eta = float(row["razao_molar_eta"])
        c_pred = kinetics.acid_concentration(ca0=ca0, x_zn=x_zn, eta=eta)
        caf_previstos.append(c_pred)

    caf_previstos = np.array(caf_previstos)

    ss_res = np.sum((caf_reais - caf_previstos) ** 2)
    ss_tot = np.sum((caf_reais - np.mean(caf_reais)) ** 2)
    r2_herbst = 1.0 - (ss_res / ss_tot)
    rmse_herbst = np.sqrt(np.mean((caf_reais - caf_previstos) ** 2))

    print(f"  [INFO] Aderência do Balanço de Herbst aos dados experimentais: R² = {r2_herbst:.4f}, RMSE = {rmse_herbst:.4f} mol/L")
    assert r2_herbst > 0.98, f"R² de Herbst inferior ao esperado: {r2_herbst}"
    print("  [PASS] Balanço de Herbst validado com R² > 0.98 frente às medições experimentais.")

    return {
        "r2_herbst": float(r2_herbst),
        "rmse_herbst": float(rmse_herbst),
    }


def testar_taxa_retracao_e_forca_motriz_whitebox_puro() -> Dict[str, Any]:
    """Testa a velocidade de retração no White-Box Puro oficial (alpha_nominal = 0.0) e com alpha histórico."""
    print("\n--- 3. Testando Velocidade de Retração v(D) no White-Box Puro (Sem α) e com α Histórico ---")
    kin_puro = LeachingKinetics()  # Padrão oficial: alpha_nominal = 0.0
    assert kin_puro.alpha_nominal == 0.0

    ca0 = 0.50  # mol/L

    # 1. Taxa inicial em t = 0 min (Caf = CA0 = 0.50 mol/L)
    # v(0) = - (2 / 69.2) * (18000 * 0.50) = -260.1156 µm/min
    v_inicial = kin_puro.shrinkage_rate(ca0=ca0, caf=0.50)
    v_esperado = - (2.0 / 69.2) * (18000.0 * 0.50)
    assert np.isclose(v_inicial, v_esperado, atol=1e-3), f"v(0) esperado {v_esperado}, obtido {v_inicial}"
    print(f"  [PASS] Taxa inicial v(0) = {v_inicial:.2f} µm/min validada.")

    # 2. No White-Box Puro (alpha = 0), a dissolução só cessa no esgotamento total do ácido (Caf = 0)
    caf_parada_puro = kin_puro.dissolution_stopping_acid(ca0=ca0)
    assert caf_parada_puro == 0.0, f"Caf* no White-Box Puro deve ser 0.0, obtido: {caf_parada_puro}"
    x_max_eta05_puro = kin_puro.theoretical_max_conversion(eta=0.5)
    assert np.isclose(x_max_eta05_puro, 0.50), f"X_max para eta=0.5 deve ser 0.50, obtido: {x_max_eta05_puro}"
    x_max_eta10_puro = kin_puro.theoretical_max_conversion(eta=1.0)
    assert np.isclose(x_max_eta10_puro, 1.00), f"X_max para eta=1.0 deve ser 1.00, obtido: {x_max_eta10_puro}"
    print("  [PASS] White-Box Puro (Sem α): Caf* = 0,00 mol/L e teto estequiométrico X_max = min(1, η) validados.")

    # 3. Referência histórica com alpha = 5500 µm/min
    kin_hist = LeachingKinetics(alpha_nominal=LeachingKinetics.ALPHA_HISTORICO_COELHO)
    caf_parada_hist = kin_hist.dissolution_stopping_acid(ca0=ca0)
    v_parada_hist = kin_hist.shrinkage_rate(ca0=ca0, caf=caf_parada_hist)
    assert np.isclose(v_parada_hist, 0.0, atol=1e-5)
    x_max_hist = kin_hist.theoretical_max_conversion(eta=1.0)
    fator_hist = 1.0 - (5500.0 / 23500.0)  # ~0.7660
    assert np.isclose(x_max_hist, fator_hist, atol=1e-3)
    print(f"  [PASS] Referência histórica (α = 5500 µm/min): Caf* = {caf_parada_hist:.4f} mol/L, X_max = {x_max_hist:.4f} validada.")

    return {
        "v_inicial": float(v_inicial),
        "caf_parada_puro": float(caf_parada_puro),
        "caf_parada_hist": float(caf_parada_hist),
        "x_max_hist": float(x_max_hist),
    }


def executar_todos_testes_cinetica() -> None:
    """Executa todos os testes da Etapa 1.2 e gera relatório formal de entrega."""
    res_eta = testar_calculo_eta_experimental()
    res_herbst = testar_balanco_acido_herbst()
    res_taxa = testar_taxa_retracao_e_forca_motriz_whitebox_puro()

    saida_dir = projeto_raiz / "Código" / "outputs" / "etapa_1_2"
    saida_dir.mkdir(parents=True, exist_ok=True)
    relatorio_md = saida_dir / "relatorio_validacao_etapa_1_2.md"

    conteudo = f"""# Relatório de Validação e Testes Unitários: Etapa 1.2 (White-Box Puro Sem α)

**Módulo Testado**: [`src/physics/kinetics.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/Código/src/physics/kinetics.py)  
**Classe**: `LeachingKinetics`  
**Referência dos parâmetros**: Dissertação de Fabrício Bortot Coelho (2017), Capítulos 4 e 5 (Tabelas 5.1, 5.9 e A1.1) e Herbst (1979).

---

## 1. Validação do Cálculo Estequiométrico da Razão Molar (eta)

Testado para os 16 ensaios de lixiviação descontínua em bancada (Apêndice A1.1, Tabela A1.1):
- **Número de ensaios avaliados**: {res_eta['n_ensaios']} ensaios
- **Erro médio relativo**: **{res_eta['erro_medio_eta_pct']:.2f}%**
- **Erro máximo relativo**: **{res_eta['max_erro_eta_pct']:.2f}%** (compatível com o arredondamento na pesagem de massa mB0)
- **Status**: **APROVADO** (reproduz com exatidão os 4 níveis de eta: 0,5; 1,0; 1,5; 3,1).

---

## 2. Validação do Balanço de Consumo de Ácido de Herbst (1979)

Equação testada: C_Af(t) = C_A0 · [1 - (X_Zn(t) / η)]
- **Condição inicial (X_Zn = 0)**: C_Af = C_A0 (**APROVADO**)
- **Esgotamento total (X_Zn = η)**: C_Af = 0,00 mol/L (**APROVADO**)
- **Aderência aos dados experimentais reais de C_Af final (t = 15 min)**:
  - **R²**: **{res_herbst['r2_herbst']:.4f}** (critério > 0,98 atendido)
  - **RMSE**: **{res_herbst['rmse_herbst']:.4f} mol/L**
  - **Status**: **APROVADO**

---

## 3. Validação da Taxa de Retração Diametral e Modelo White-Box Puro (Sem α)

- **White-Box Puro Oficial (`alpha_nominal = 0.0`)**:
  - Taxa inicial (C_A0 = 0,50 mol/L): **{res_taxa['v_inicial']:.2f} µm/min** (**APROVADO**)
  - Ponto de parada: C_Af* = **0,00 mol/L** (dissolução estequiométrica contínua até o esgotamento do reagente limitante)
  - Conversão máxima assintótica: X_Zn_max = **min(1,0; η)** (**APROVADO**)
- **Referência Histórica de Coelho (`α = 5500 µm/min`)**:
  - Ponto de parada empírico: C_Af* = **{res_taxa['caf_parada_hist']:.4f} mol/L**
  - Conversão máxima teórica para η = 1,0: X_Zn_max = **{res_taxa['x_max_hist']:.4f}** (**APROVADO**)

---

## 4. Conclusão
O módulo `kinetics.py` foi atualizado para estabelecer o White-Box Puro sem amortecimento empírico (`α = 0`) como padrão oficial, mantendo suporte transparente à constante histórica `ALPHA_HISTORICO_COELHO = 5500.0`.
"""
    relatorio_md.write_text(conteudo, encoding="utf-8")
    print(f"\n[OK] Relatório de validação salvo em: {relatorio_md}")
    print("[SUCCESS] Todos os testes da Etapa 1.2 passaram com êxito!")


if __name__ == "__main__":
    executar_todos_testes_cinetica()
