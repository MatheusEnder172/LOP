# Etapa 2.1 — Otimização Inversa Parametrizada e Geração de Alvos v(t)

Esta pasta contém o script de otimização inversa, testes e especificações para a determinação das trajetórias reais de retração interfacial v(t) que servirão como alvos de treinamento supervisionado para os modelos de Machine Learning (Fase 3).

---

## 1. Contexto e Motivação no Fluxo Híbrido

Na arquitetura **Serial Híbrida (DDM → FPM)**, o modelo caixa-preta (Machine Learning) não prevê a conversão final X_Zn diretamente; ele estima a propriedade fenomenológica intermediária **v(t) = dD/dt** (taxa linear de retração de diâmetro de partícula). O resolvedor mecanicista (FPM via PBM Batelada) recebe v(t) e calcula a conversão X_Zn(t) e a concentração de ácido residual C_Af(t).

Como v(t) não é mensurável diretamente em ensaios industriais ou de bancada, foi implementada a **Opção B (Otimização Inversa por Ensaio)**, aprovada pelo orientador/usuário:
- Cada curva experimental real de lixiviação X_Zn(t) foi invertida através do Balanço Populacional pré-computado X_Zn(δ).
- A velocidade foi parametrizada por uma função contínua bi-exponencial regularizada:
  |v(t)| = a₁ · exp(-b₁ · t) + a₂ · exp(-b₂ · t) + c ≥ 0
  v(t) = -|v(t)| ≤ 0
- O deslocamento diametral acumulado δ(t) possui solução analítica fechada:
  δ(t) = (a₁ / b₁) · [1 - exp(-b₁ · t)] + (a₂ / b₂) · [1 - exp(-b₂ · t)] + c · t
- Isso permitiu uma otimização L-BFGS-B instantânea e ultra-estável, alcançando R² global de 0,99896.

---

## 2. Estrutura de Arquivos da Etapa

```text
Código/etapas/etapa_2_1_otimizacao_alvos_v/
├── README.md                     # Este documento explicativo
├── otimizar_alvos_v.py           # Script principal de otimização inversa e exportação
└── test_otimizacao_inversa.py    # Suíte de testes unitários com pytest
```

---

## 3. Entregas Produzidas

### Datasets Gerados (`Base de dados/processed/`)
- `alvos_v_treinamento.csv` (128 registros):
  Valores exatos de v(t), δ(t) e X_Zn nos 8 instantes experimentais de cada um dos 16 ensaios (t = 0, 0.5, 1, 2, 3, 5, 7, 15 min).
- `alvos_v_treinamento_denso.csv` (976 registros):
  Malha temporal fina regular com passo de 0,25 min (61 pontos por ensaio) para treinamento denso e interpolação de redes neurais e modelos baseados em árvores.
- `parametros_otimizacao_inversa.csv` (16 registros):
  Tabela contendo os 5 parâmetros ótimos (a₁, b₁, a₂, b₂, c) e as métricas de qualidade (R², RMSE, MAE, v₀, v_final, δ_final) de cada ensaio.

### Figuras Científicas (`Código/outputs/etapa_2_1/`)
- `fig_04_reconstrucao_XZn_vs_experimento.png` (300 DPI) e `.pdf` (vetorial):
  Painel de 4 subplots por razão molar η (0,5; 1,0; 1,5; 3,1) comprovando reconstrução quase perfeita dos dados experimentais (R² = 0,99896).
- `fig_05_curvas_v_otimizadas.png` (300 DPI) e `.pdf` (vetorial):
  Painel de 4 subplots exibindo os perfis contínuos de velocidade de retração v(t) em µm/min, evidenciando o pico inicial e a atenuação assintótica suave.

---

## 4. Instruções de Execução e Testes

Para executar o pipeline de otimização e gerar os gráficos:
```bash
python Código/etapas/etapa_2_1_otimizacao_alvos_v/otimizar_alvos_v.py
```

Para rodar a suíte de testes unitários:
```bash
python -m pytest "Código/etapas/etapa_2_1_otimizacao_alvos_v/test_otimizacao_inversa.py" -v
```
