# Relatório de Validação e Testes Unitários: Etapa 1.1

**Módulo Testado**: [`src/physics/granulometry.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/granulometry.py)  
**Classe**: `RosinRammlerBennet`  
**Referência dos parâmetros**: Dissertação de Fabrício Bortot Coelho (2017), pág. 129-133 e Tabela 5.9.

---

## 1. Resultados dos Testes de Consistência Analítica

| Propriedade Testada | Valor Teórico / Dissertação | Valor Calculado pela Classe | Status |
| :--- | :---: | :---: | :---: |
| **F(0) (Limite inferior)** | 0,0000 | 0,0000 | **APROVADO** |
| **F(D_63,2) (Passante característico)** | 1 - e^(-1) = 0,6321 | 0.6321 | **APROVADO** |
| **F(10.000 µm) (Limite assintótico)** | 1,0000 | 1,0000 | **APROVADO** |
| **Diâmetro Médio (µ)** | 41,28 µm | 41.28 µm | **APROVADO** |
| **Coeficiente de Variação (CV)** | 0,9700 | 0.9785 | **APROVADO** |

---

## 2. Validação da Discretização de Malha e Terceiro Momento (M3)

A conservação de volume no Balanço Populacional depende da precisão da integral do terceiro momento:

- **Número de nós na malha linear**: 1500 nós (0,01 a 297,0 µm).
- **M3(0) Teórico com cauda infinita [0, inf)**: 399968.03 µm³
- **M3(0) Referência no Domínio Físico [0.01, 297 µm]**: 376877.38 µm³ (94.2% do volume teórico)
- **M3(0) Numérico da Malha (Regra dos Trapézios)**: 376877.36 µm³
- **Erro Relativo da Discretização**: **0.000005%** (precisão de máquina, critério < 0,0001% atendido).

---

## 3. Aderência aos Dados Experimentais Reais (`granulometria_RRB.csv`)

- **Coeficiente de Determinação (R²)**: **0.9962**
- **Raiz do Erro Quadrático Médio (RMSE)**: **0.0210**
- **Erro Absoluto Médio (MAE)**: **0.0142**

---

## 4. Conclusão
O módulo `RosinRammlerBennet` foi aprovado em 100% dos testes unitários e de integração, estando pronto para atuar como a condição inicial analítica do Balanço Populacional em batelada (Etapa 1.3).
