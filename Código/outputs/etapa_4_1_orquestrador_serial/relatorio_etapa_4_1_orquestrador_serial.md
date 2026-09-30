# Relatório Técnico Executivo — Subetapa 4.1: Concepção do Orquestrador Híbrido Serial

## 1. Sumário Executivo
Nesta subetapa, foi construída e validada a infraestrutura permanente de acoplamento do projeto LOP:
a classe `SerialHybridModel` em [`Código/src/hybrid/serial_hybrid.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/hybrid/serial_hybrid.py).

O orquestrador estabelece a ponte entre o modelo supervisionado orientado por dados (Data-Driven Model - DDM, utilizando por padrão o modelo campeão Random Forest) e o modelo mecanicista de Balanço Populacional em Batelada (`BatchPBMSolver`), garantindo a estrita preservação das leis de conservação de massa e termodinâmica.

---

## 2. Resultados Preliminares nos Três Ensaios de Teste Cego

Os três ensaios mantidos estritamente intocados durante toda a calibração da modelagem orientada a dados foram avaliados através da simulação híbrida completa:

| Ensaio | Regime Físico-Químico | C_A0 (mol/L) | η (-) | R² (X_Zn) | RMSE (X_Zn) | MAE (X_Zn) | X_Zn Final (Pred) | X_Zn Final (Exp) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **8** | Estequiométrico Neutro (CA0=0.5, eta=1.0) | 0.50 | 1.0 | **0.9628** | 0.0544 | 0.0493 | 0.913 | 0.870 |
| **14** | Leve Excesso Ácido (CA0=1.0, eta=1.5) | 1.00 | 1.5 | **0.9975** | 0.0157 | 0.0113 | 0.976 | 0.970 |
| **7** | Forte Excesso Ácido (CA0=0.5, eta=3.1) | 0.50 | 3.1 | **0.9972** | 0.0170 | 0.0123 | 0.990 | 1.010 |

* **R² Médio no Teste Cego**: **0.9859**
* **RMSE Médio no Teste Cego**: **0.0290** (desvio absoluto de apenas ~2.9 pontos percentuais de conversão)
* **Violação Física (X_Zn < 0 ou X_Zn > 1)**: **0,00%**
* **Violação Ácida (C_Af < 0)**: **0,00%**

---

## 3. Garantias Físicas e Refinamentos Numéricos Implementados

1. **Malha Interna Fina de Integração**:
   Para evitar a superestimação trapezoidal da retração inicial provocada pela alta taxa v(0) em malhas de tempo esparsas (como os 8 instantes experimentais), o orquestrador gera automaticamente uma malha temporal interna com passo sub-segundo (dt ≤ 0,03 min), integrando com alta fidelidade a integral diametral:
   δ(t) = ∫₀ᵗ |v(τ)| dτ
   e reamostrando exatamente nos instantes requisitados.
2. **Monotonicidade Rigorosa de Dissolução**:
   O vetor de conversão de zinco satisfaz d(X_Zn)/dt ≥ 0 em 100% dos passos temporais, refletindo a irreversibilidade da dissolução química em meio ácido.
3. **Consumo de Ácido Confinado**:
   A concentração residual C_Af(t) obedece estritamente às equações de Herbst, decrescendo monotonicamente a partir de C_A0 e nunca atingindo valores negativos.

---

## 4. Figuras e Entregas da Subetapa
* `fig_demonstrativa_hibrido_ensaio8.png` e `.pdf` (300 DPI): Painel quádruplo com trajetórias de taxa interfacial |v(t)|, retração acumulada δ(t), reconstituição da conversão X_Zn(t) e consumo ácido C_Af(t).
* `tabela_demonstracao_ensaios_teste.csv`: Métricas de aderência nos ensaios 8, 14 e 7.
* Suíte de testes `test_serial_hybrid.py` com 7/7 testes unitários aprovados.
