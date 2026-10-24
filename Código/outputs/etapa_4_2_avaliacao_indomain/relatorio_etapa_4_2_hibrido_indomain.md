# Relatório Técnico — Subetapa 4.2: Simulação Completa In-Domain e Benchmark dos 4 Modelos Híbridos (t > 0, RRB ÷ D³, 3 Inputs)

**Projeto**: Modelagem Híbrida de Lixiviação de Concentrado de Zinco (LOP / DEQ / UFMG)  
**Etapa**: 4.2 — Avaliação In-Domain nos 16 Ensaios de Bancada (Bortot Coelho, 2017) estritamente sobre t > 0 (N = 112 pontos ativos)  

---

## 1. Resumo Executivo e Principais Resultados (t > 0)

Esta etapa consolidou a avaliação de ponta a ponta do acoplamento híbrido serial (DDM → PBM com distribuição numérica ponderada por volume RRB ÷ D³ e condição inicial física hardcodada em t = 0: X_Zn(0) = 0, δ(0) = 0, C_Af(0) = C_A0), avaliando todos os **4 modelos Black-Box (`MLP Campeão`, `Random Forest`, `XGBoost`, `SVR`)** estritamente sobre os **112 pontos experimentais ativos (t > 0)** com apenas as **3 variáveis cinéticas ativas [C_A0, η, t]**.

### Tabela-Resumo: Benchmark Consolidado (t > 0)
| Modelo | Escopo (t > 0) | R² (-) | RMSE (-) | MAE (-) | Erro Máximo (-) | Redução do Erro vs. White-Box |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **White-Box Puro (RRB ÷ D³, Sem α)** | Global (16 ensaios, N=112) | 0.8709 | 0.0702 | 0.0516 | 0.1634 | — |
| **DDM Puro (MLP sem Herbst)** | Global (16 ensaios, N=112) | 0.9827 | 0.0257 | 0.0188 | 0.0822 | Viola teto estequiométrico |
| **Híbrido Serial Campeão (MLP → PBM)** | **Global (16 ensaios, N=112)** | **0.9827** | **0.0257** | **0.0188** | **0.0822** | **+63.4%** |
| White-Box Puro (RRB ÷ D³, Sem α) | Teste Cego (3 ensaios, N=21) | -0.6747 | 0.0780 | 0.0637 | 0.1255 | — |
| **Híbrido Serial Campeão (MLP → PBM)** | **Teste Cego (3 ensaios, N=21)** | **0.6570** | **0.0353** | **0.0269** | **0.0822** | **+54.7%** |

---

## 2. Comparativo Completo dos 4 Modelos Híbridos Acoplados ao PBM (t > 0)

```
                              Particao                       Modelo        R2     RMSE      MAE  MaxError
  Global (16 ensaios - 112 pts, t > 0)   FPM Puro (RRB ÷ D³, Sem α)  0.870943 0.070170 0.051571  0.163418
  Global (16 ensaios - 112 pts, t > 0)    DDM Puro (MLP sem Herbst)  0.982672 0.025712 0.018756  0.082177
  Global (16 ensaios - 112 pts, t > 0) Híbrido Serial (MLP Campeão)  0.982672 0.025712 0.018756  0.082177
  Global (16 ensaios - 112 pts, t > 0)          Híbrido Serial (RF)  0.987685 0.021676 0.015365  0.086589
  Global (16 ensaios - 112 pts, t > 0)     Híbrido Serial (XGBoost)  0.993019 0.016320 0.011698  0.060173
  Global (16 ensaios - 112 pts, t > 0)         Híbrido Serial (SVR)  0.681255 0.110277 0.078184  0.307775
   Treino (13 ensaios - 91 pts, t > 0)   FPM Puro (RRB ÷ D³, Sem α)  0.890015 0.068232 0.048763  0.163418
   Treino (13 ensaios - 91 pts, t > 0)    DDM Puro (MLP sem Herbst)  0.987575 0.022934 0.016888  0.063610
   Treino (13 ensaios - 91 pts, t > 0) Híbrido Serial (MLP Campeão)  0.987575 0.022934 0.016888  0.063610
   Treino (13 ensaios - 91 pts, t > 0)          Híbrido Serial (RF)  0.992615 0.017681 0.013175  0.053980
   Treino (13 ensaios - 91 pts, t > 0)     Híbrido Serial (XGBoost)  0.995145 0.014335 0.010316  0.037618
   Treino (13 ensaios - 91 pts, t > 0)         Híbrido Serial (SVR)  0.663072 0.119423 0.087605  0.307775
Teste Cego (3 ensaios - 21 pts, t > 0)   FPM Puro (RRB ÷ D³, Sem α) -0.674701 0.078017 0.063739  0.125524
Teste Cego (3 ensaios - 21 pts, t > 0)    DDM Puro (MLP sem Herbst)  0.656951 0.035310 0.026851  0.082177
Teste Cego (3 ensaios - 21 pts, t > 0) Híbrido Serial (MLP Campeão)  0.656951 0.035310 0.026851  0.082177
Teste Cego (3 ensaios - 21 pts, t > 0)          Híbrido Serial (RF)  0.683227 0.033931 0.024853  0.086589
Teste Cego (3 ensaios - 21 pts, t > 0)     Híbrido Serial (XGBoost)  0.854175 0.023022 0.017686  0.060173
Teste Cego (3 ensaios - 21 pts, t > 0)         Híbrido Serial (SVR)  0.158817 0.055292 0.037362  0.149694
```
