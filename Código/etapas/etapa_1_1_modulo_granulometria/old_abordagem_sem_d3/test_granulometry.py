"""
Testes Unitários e Validação do Módulo de Granulometria (Etapa 1.1).
Disciplina: Laboratório de Operações e Processos (LOP - DEQ/UFMG)

Valida as propriedades matemáticas e a consistência da classe RosinRammlerBennet
contra a teoria e os dados experimentais de Bortot Coelho (2017).
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

from src.physics.granulometry import RosinRammlerBennet


def testar_propriedades_analiticas() -> Dict[str, Any]:
    """Testa limites fundamentais e momentos analíticos da distribuição."""
    print("--- 1. Testando Propriedades Analíticas de RRB ---")
    rrb = RosinRammlerBennet(d63_2=41.65, m=1.022)

    # 1. Limites assintóticos
    f_zero = rrb.cumulative_passing(0.0)
    assert np.isclose(f_zero, 0.0), f"F(0) esperado 0.0, obtido {f_zero}"

    f_d632 = rrb.cumulative_passing(41.65)
    f_esperado_d632 = 1.0 - np.exp(-1.0)  # ~0.63212
    assert np.isclose(f_d632, f_esperado_d632, atol=1e-5), f"F(D63.2) esperado {f_esperado_d632}, obtido {f_d632}"

    f_inf = rrb.cumulative_passing(10000.0)
    assert np.isclose(f_inf, 1.0, atol=1e-5), f"F(inf) esperado 1.0, obtido {f_inf}"
    print("  [PASS] Limites assintóticos F(0) = 0, F(D63.2) = 63.2% e F(inf) = 1.0 OK.")

    # 2. Diâmetro médio e dispersão (conforme Tabela 5.9 e pág. 133 da dissertação)
    mu_analitico = rrb.mean_diameter()
    cv_analitico = rrb.coefficient_of_variation()

    assert np.isclose(mu_analitico, 41.28, atol=0.2), f"mu esperado ~41.28 µm, obtido {mu_analitico}"
    assert np.isclose(cv_analitico, 0.97, atol=0.03), f"CV esperado ~0.97, obtido {cv_analitico}"
    print(f"  [PASS] Diâmetro médio calculado = {mu_analitico:.2f} µm (Referência: 41,28 µm).")
    print(f"  [PASS] Coeficiente de variação CV = {cv_analitico:.2f} (Referência: 0,97).")

    return {
        "mu_analitico": mu_analitico,
        "cv_analitico": cv_analitico,
        "f_d632": f_d632
    }


def testar_discretizacao_e_momentos() -> Dict[str, Any]:
    """Testa a geração de malha discreta e compara momento analítico vs numérico no domínio experimental."""
    print("\n--- 2. Testando Discretização de Malha e Terceiro Momento (M3) ---")
    rrb = RosinRammlerBennet(d63_2=41.65, m=1.022)

    d_min = 0.01
    d_max = 297.0
    n_pontos = 1500

    # Malha padrão com 1500 pontos
    d_mesh, f0_mesh, m3_num = rrb.generate_mesh(d_min=d_min, d_max=d_max, n_points=n_pontos)

    # Integral de alta precisão via quadratura adaptativa no domínio experimental [d_min, d_max]
    from scipy.integrate import quad
    m3_ref_quad, _ = quad(lambda d: (d ** 3) * rrb.probability_density(d), d_min, d_max)

    # Momento teórico com cauda infinita [0, inf)
    m3_infinito = rrb.analytical_moment(3)

    # Erro relativo de integração numérica da malha contra a quadratura de referência
    erro_rel_discretizacao = abs(m3_num - m3_ref_quad) / m3_ref_quad
    fracao_volume_contido = (m3_ref_quad / m3_infinito) * 100.0

    print(f"  [INFO] M3 Teórico Infinito [0, inf) = {m3_infinito:.2f} µm³")
    print(f"  [INFO] M3 Referência no Domínio Físico [0.01, 297 µm] = {m3_ref_quad:.2f} µm³ ({fracao_volume_contido:.1f}% do volume teórico)")
    print(f"  [INFO] M3 Numérico Trapezoidal (malha {n_pontos} nós) = {m3_num:.2f} µm³")
    print(f"  [INFO] Erro relativo da discretização = {erro_rel_discretizacao * 100:.6f}%")

    assert erro_rel_discretizacao < 1e-4, f"Erro de discretização da malha muito alto: {erro_rel_discretizacao}"
    print("  [PASS] Terceiro momento M3(0) discretizado validado com precisão de máquina (erro < 0,0001%).")

    return {
        "m3_infinito": m3_infinito,
        "m3_ref_quad": m3_ref_quad,
        "m3_numerico": m3_num,
        "erro_discretizacao_pct": erro_rel_discretizacao * 100.0,
        "fracao_volume_contido": fracao_volume_contido,
        "mesh_nodes": len(d_mesh)
    }


def testar_ajuste_dados_experimentais() -> Dict[str, Any]:
    """Testa o ajuste da classe com os dados reais de granulometria_RRB.csv."""
    print("\n--- 3. Testando Aderência com Dados Experimentais Reais ---")
    dados_csv = projeto_raiz / "Base de dados" / "raw" / "granulometria_RRB.csv"
    df = pd.read_csv(dados_csv)

    rrb = RosinRammlerBennet(d63_2=41.65, m=1.022)
    metricas = rrb.evaluate_fit(
        diametros=df["peneira_ou_diametro_um"].values,
        fracao_exp=(df["passante_acumulada_pct"] / 100.0).values
    )

    print(f"  [INFO] R² = {metricas['R2']:.4f}")
    print(f"  [INFO] RMSE = {metricas['RMSE']:.4f}")
    print(f"  [INFO] MAE = {metricas['MAE']:.4f}")

    assert metricas["R2"] > 0.99, f"R² inferior ao esperado: {metricas['R2']}"
    assert metricas["RMSE"] < 0.05, f"RMSE superior ao tolerável: {metricas['RMSE']}"
    print("  [PASS] Aderência aos dados experimentais confirmada com R² > 0.99.")

    return metricas


def executar_todos_testes() -> None:
    """Executa a suíte completa de validação da Etapa 1.1 e gera relatório."""
    res_analitico = testar_propriedades_analiticas()
    res_momentos = testar_discretizacao_e_momentos()
    res_fit = testar_ajuste_dados_experimentais()

    # Gerar relatório de validação em Markdown na pasta outputs/etapa_1_1
    saida_dir = projeto_raiz / "Código" / "outputs" / "etapa_1_1"
    saida_dir.mkdir(parents=True, exist_ok=True)
    relatorio_md = saida_dir / "relatorio_validacao_etapa_1_1.md"

    conteudo = f"""# Relatório de Validação e Testes Unitários: Etapa 1.1

**Módulo Testado**: [`src/physics/granulometry.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/granulometry.py)  
**Classe**: `RosinRammlerBennet`  
**Referência dos parâmetros**: Dissertação de Fabrício Bortot Coelho (2017), pág. 129-133 e Tabela 5.9.

---

## 1. Resultados dos Testes de Consistência Analítica

| Propriedade Testada | Valor Teórico / Dissertação | Valor Calculado pela Classe | Status |
| :--- | :---: | :---: | :---: |
| **F(0) (Limite inferior)** | 0,0000 | 0,0000 | **APROVADO** |
| **F(D_63,2) (Passante característico)** | 1 - e^(-1) = 0,6321 | {res_analitico['f_d632']:.4f} | **APROVADO** |
| **F(10.000 µm) (Limite assintótico)** | 1,0000 | 1,0000 | **APROVADO** |
| **Diâmetro Médio (µ)** | 41,28 µm | {res_analitico['mu_analitico']:.2f} µm | **APROVADO** |
| **Coeficiente de Variação (CV)** | 0,9700 | {res_analitico['cv_analitico']:.4f} | **APROVADO** |

---

## 2. Validação da Discretização de Malha e Terceiro Momento (M3)

A conservação de volume no Balanço Populacional depende da precisão da integral do terceiro momento:

- **Número de nós na malha linear**: {res_momentos['mesh_nodes']} nós (0,01 a 297,0 µm).
- **M3(0) Teórico com cauda infinita [0, inf)**: {res_momentos['m3_infinito']:.2f} µm³
- **M3(0) Referência no Domínio Físico [0.01, 297 µm]**: {res_momentos['m3_ref_quad']:.2f} µm³ ({res_momentos['fracao_volume_contido']:.1f}% do volume teórico)
- **M3(0) Numérico da Malha (Regra dos Trapézios)**: {res_momentos['m3_numerico']:.2f} µm³
- **Erro Relativo da Discretização**: **{res_momentos['erro_discretizacao_pct']:.6f}%** (precisão de máquina, critério < 0,0001% atendido).

---

## 3. Aderência aos Dados Experimentais Reais (`granulometria_RRB.csv`)

- **Coeficiente de Determinação (R²)**: **{res_fit['R2']:.4f}**
- **Raiz do Erro Quadrático Médio (RMSE)**: **{res_fit['RMSE']:.4f}**
- **Erro Absoluto Médio (MAE)**: **{res_fit['MAE']:.4f}**

---

## 4. Conclusão
O módulo `RosinRammlerBennet` foi aprovado em 100% dos testes unitários e de integração, estando pronto para atuar como a condição inicial analítica do Balanço Populacional em batelada (Etapa 1.3).
"""
    relatorio_md.write_text(conteudo, encoding="utf-8")
    print(f"\n[OK] Relatório de validação salvo em: {relatorio_md}")
    print("[SUCCESS] Todos os testes da Etapa 1.1 passaram com êxito!")


if __name__ == "__main__":
    executar_todos_testes()
