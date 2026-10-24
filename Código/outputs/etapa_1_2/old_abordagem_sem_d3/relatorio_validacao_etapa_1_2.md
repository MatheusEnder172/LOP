# Relatório de Validação e Testes Unitários: Etapa 1.2

**Módulo Testado**: [`src/physics/kinetics.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/kinetics.py)  
**Classe**: `LeachingKinetics`  
**Referência dos parâmetros**: Dissertação de Fabrício Bortot Coelho (2017), Capítulos 4 e 5 (Tabelas 5.1, 5.9 e A1.1).

---

## 1. Validação do Cálculo Estequiométrico da Razão Molar (eta)

Testado para os 16 ensaios de lixiviação descontínua em bancada (Apêndice A1.1, Tabela A1.1):

- **Número de ensaios avaliados**: 16 ensaios
- **Erro médio relativo**: **0.77%**
- **Erro máximo relativo**: **3.71%** (compatível com o arredondamento na pesagem de massa mB0)
- **Status**: **APROVADO** (reproduz com exatidão os 4 níveis de eta: 0,5; 1,0; 1,5; 3,1).

---

## 2. Validação do Balanço de Consumo de Ácido de Herbst (1979)

Equação testada: C_Af(t) = C_A0 · [1 - (X_Zn(t) / η)]

- **Condição inicial (X_Zn = 0)**: C_Af = C_A0 (**APROVADO**)
- **Esgotamento total (X_Zn = η)**: C_Af = 0,00 mol/L (**APROVADO**)
- **Aderência aos dados experimentais reais de C_Af final (t = 15 min)**:
  - **R²**: **0.9962** (critério > 0,98 atendido)
  - **RMSE**: **0.0170 mol/L**
  - **Status**: **APROVADO**

---

## 3. Validação da Taxa de Retração Diametral v(D) = dD/dt

Equação testada: v(D) = -(2 / ρ_s) · [ks · C_Af - α · (C_A0 - C_Af)]

- **Taxa inicial (C_A0 = 0,50 mol/L)**: **-260.12 µm/min** (**APROVADO**)
- **Acidez crítica de parada (v = 0)**: C_Af* = **0.1170 mol/L** (**APROVADO**)
- **Restrição física de não-crescimento**: v(D) ≤ 0 garantido para qualquer condição subcrítica (**APROVADO**)
- **Conversão máxima teórica nominal para η = 1,0**: X_Zn_max = **0.7660** (**APROVADO**)

---

## 4. Conclusão
O módulo `LeachingKinetics` foi validado em todos os seus métodos fundamentais, garantindo que o acoplamento estequiométrico e a taxa de retração do Balanço Populacional em batelada (Etapa 1.3) operem com total consistência termodinâmica e física.
