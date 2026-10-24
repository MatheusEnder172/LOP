# Relatório de Validação Técnica — Subetapa 3.2.1: Multi-Layer Perceptron (MLP Protagonista — Opção 1 + Autograd)

## 1. Sumário Executivo
Nesta subetapa, o modelo neural **KineticsMLP** foi evoluído sob três diretrizes fundamentais:
1. **Exclusão de `t = 0` e Condição Inicial Hardcoded (`X_Zn(0) = 0, δ(0) = 0`)**: Elimina o salto impulsivo artificial na origem, permitindo que o MLP aprenda o decaimento suave em `t > 0` (`t ∈ [0,25; 15,00] min`).
2. **Vetor de Entrada 3D (`input_dim = 3`)**: Remoção da variável constante `temperatura_C` (`40,0 °C`), operando estritamente com `X = [CA0_mol_L, razao_molar_eta, t_min]`.
3. **Opção 1 + Análise Diferencial `Autograd`**: Comparação de topologias `C∞` (`GELU`, `SiLU/Swish` e blocos residuais `ResNet-MLP`), consolidação via **Destilação de Deep Ensemble (4-Fold Early Stopping)** com bandas de incerteza `±1,5σ` e extração de derivadas parciais analíticas (`∂|v|/∂C_A0`, `∂|v|/∂η`, `∂|v|/∂t`).

A arquitetura campeã **MLP-B (Padrão GELU)** alcançou **R² = 0.9926 (R²_log = 0.9990) no Treino** e **R² = 0.9231 (R²_log = 0.9453, RMSE = 2.37 µm/min, MAE = 0.89 µm/min) no Teste Cego**.

---

## 2. Comparação de Arquiteturas na Validação Cruzada (4 Dobras Disjuntas, t > 0)

| Arquitetura | Topologia | Ativação | Residual | R² Médio (CV) | R²_log Médio | RMSE Médio (µm/min) | MAE Médio (µm/min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MLP-B (Padrão GELU)** | `[64, 32]` | GELU | False | **0.8210** ± 0.1092 | 0.7696 | 3.25 | 1.06 |
| **MLP-A (Compacta GELU)** | `[32, 16]` | GELU | False | **0.8233** ± 0.0790 | 0.7298 | 3.47 | 1.08 |
| **MLP-C (Profunda SiLU)** | `[128, 64, 32]` | SiLU | False | **0.6800** ± 0.2166 | 0.7737 | 4.37 | 1.32 |
| **ResNet-MLP (Residual GELU)** | `[64, 32]` | GELU | True | **0.3849** ± 0.4720 | 0.7396 | 6.39 | 2.12 |

---

## 3. Avaliação Individual nos Ensaios de Teste Cego (t > 0)

| Ensaio | Regime Físico-Químico | C_A0 (mol/L) | η (-) | R² Individual | RMSE (µm/min) | MAE (µm/min) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **08** | Estequiométrico Neutro | 0.50 | 1.0 | **0.9343** | 1.41 | 0.24 |
| **14** | Leve Excesso Ácido | 1.00 | 1.5 | **0.9507** | 2.16 | 0.51 |
| **07** | Forte Excesso Ácido | 0.50 | 3.1 | **0.8650** | 3.19 | 1.91 |
