# Relatório de Validação e Testes Unitários: Etapa 1.2 (White-Box Puro Sem α)

**Módulo Testado**: [`src/physics/kinetics.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v4/Código/src/physics/kinetics.py)  
**Classe**: `LeachingKinetics`  
**Referência dos parâmetros**: Dissertação de Fabrício Bortot Coelho (2017), Capítulos 4 e 5 (Tabelas 5.1, 5.9 e A1.1) e Herbst (1979).

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

## 3. Validação da Taxa de Retração Diametral e Modelo White-Box Puro (Sem α)

- **White-Box Puro Oficial (`alpha_nominal = 0.0`)**:
  - Taxa inicial (C_A0 = 0,50 mol/L): **-260.12 µm/min** (**APROVADO**)
  - Ponto de parada: C_Af* = **0,00 mol/L** (dissolução estequiométrica contínua até o esgotamento do reagente limitante)
  - Conversão máxima assintótica: X_Zn_max = **min(1,0; η)** (**APROVADO**)
- **Referência Histórica de Coelho (`α = 5500 µm/min`)**:
  - Ponto de parada empírico: C_Af* = **0.1170 mol/L**
  - Conversão máxima teórica para η = 1,0: X_Zn_max = **0.7660** (**APROVADO**)

---

## 4. Conclusão
O módulo `kinetics.py` foi atualizado para estabelecer o White-Box Puro sem amortecimento empírico (`α = 0`) como padrão oficial, mantendo suporte transparente à constante histórica `ALPHA_HISTORICO_COELHO = 5500.0`.
