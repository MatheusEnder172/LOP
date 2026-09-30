# Guia Metodológico e Técnico de Implementação — Etapa 3.2: Modelagem Black-Box (DDM Puro)

**Projeto**: Modelagem Híbrida de Lixiviação de Zinco (DEQ/UFMG)  
**Etapa**: 3.2 — Treinamento, Otimização e Seleção de Modelos Supervisionados  
**Data**: 26 de Setembro de 2026  
**Finalidade**: Estabelecer a arquitetura modular, o protocolo de validação sem vazamento, os critérios de avaliação e o roteiro passo a passo para a implementação e teste individual dos quatro regressores supervisionados (MLP, Random Forest, SVR e XGBoost).

---

## 1. Visão Geral e Propósito no Pipeline Híbrido

O objetivo central da **Etapa 3.2** é construir modelos puramente orientados por dados (*Data-Driven Models* — DDM) capazes de mapear as condições operacionais do reator na taxa linear de retração interfacial da partícula sólida:

$$|v(t)| = f_{\text{ML}}\left( T,\ C_{A0},\ \eta,\ t \right)$$

Onde:
* **Entradas (4 features)**:
  * $T$: Temperatura de reação ($40{,}0\ ^\circ\text{C}$ na bancada; variável mantida para transferibilidade com a planta piloto);
  * $C_{A0}$: Concentração inicial de ácido sulfúrico livre ($0{,}10$ a $1{,}50\text{ mol/L}$);
  * $\eta$: Razão molar estequiométrica reagente/limitante ($0{,}5$ a $3{,}1$);
  * $t$: Tempo de reação transcorrido ($0{,}0$ a $15{,}0\text{ min}$).
* **Saída (1 target)**:
  * $|v(t)|$: Módulo da velocidade de redução diametral ($dD/dt = -|v(t)|$), expressa em $\mu\text{m/min}$.

O regressor que apresentar o melhor equilíbrio entre generalização na Validação Cruzada, acurácia no Teste Cego e suavidade física será coroado **Modelo Campeão** e acoplado ao resolvedor de Balanço Populacional ([`BatchPBMSolver`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/pbm_batch.py#L22)) na **Fase 4 (Acoplamento Híbrido Serial DDM → PBM)**.

---

## 2. Estrutura Modular das Subpastas da Etapa 3.2

Para assegurar total rastreabilidade, isolamento de dependências e facilidade de depuração, a Etapa 3.2 é dividida em **cinco subfases independentes**:

```
Código/etapas/etapa_3_2/
├── GUIA_IMPLEMENTACAO_ETAPA_3_2.md         (Este documento)
├── README.md                               (Visão geral e status das subetapas)
├── subetapa_3_2_1_mlp/                     (Multi-Layer Perceptron em PyTorch)
│   ├── modelo_mlp.py                       (Classe PyTorch e wrapper scikit-learn)
│   ├── treinar_avaliar_mlp.py              (Pipeline de CV, treino final e teste cego)
│   ├── test_mlp.py                         (Testes unitários automatizados)
│   └── README.md                           (Documentação técnica do MLP)
├── subetapa_3_2_2_random_forest/           (Random Forest Regressor)
│   ├── modelo_rf.py
│   ├── treinar_avaliar_rf.py
│   ├── test_rf.py
│   └── README.md
├── subetapa_3_2_3_svr/                     (Support Vector Regression RBF)
│   ├── modelo_svr.py
│   ├── treinar_avaliar_svr.py
│   ├── test_svr.py
│   └── README.md
├── subetapa_3_2_4_xgboost/                 (XGBoost Gradient Boosting)
│   ├── modelo_xgb.py
│   ├── treinar_avaliar_xgb.py
│   ├── test_xgb.py
│   └── README.md
└── subetapa_3_2_5_comparacao_campeao/      (Consolidação Geral e Eleição do Campeão)
    ├── comparar_modelos.py                 (Tabela cruzada, paridade unificada e ranking)
    ├── test_comparativo.py
    └── README.md
```

### Estrutura de Saídas (`Código/outputs/`)
* `Código/outputs/etapa_3_2/subetapa_3_2_1_mlp/`: Curvas de aprendizado, predições cinéticas, paridade, resíduos e relatório técnico do MLP.
* `Código/outputs/etapa_3_2/subetapa_3_2_2_random_forest/`: Importância de features, paridade e relatório do Random Forest.
* `Código/outputs/etapa_3_2/subetapa_3_2_3_svr/`: Diagnóstico de vetores de suporte, paridade e relatório do SVR.
* `Código/outputs/etapa_3_2/subetapa_3_2_4_xgboost/`: Histórico de boosting, importância de atributos e relatório do XGBoost.
* `Código/outputs/etapa_3_2/subetapa_3_2_5_comparacao_campeao/`: Tabela geral de métricas, gráfico consolidado de paridade e relatório final de seleção.
* `Código/outputs/models_saved/`:
  * `mlp/mlp_kinetics_v1.pt` e `mlp_config.json`
  * `random_forest/rf_kinetics_v1.joblib`
  * `svr/svr_kinetics_v1.joblib`
  * `xgboost/xgb_kinetics_v1.json`

---

## 3. Dados Particionados e Protocolo de Validação Rigoroso

Todos os quatro regressores serão submetidos **estritamente à mesma partição 85/15** homologada na [Etapa 3.1](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/etapas/etapa_3_1_preprocessing/README.md):

### 3.1. Arquivos de Entrada (`Base de dados/processed/splits/`)
* [`train_dense.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Base%20de%20dados/processed/splits/train_dense.csv): **13 ensaios de Treino (793 amostras)** — `[1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 15, 16]`.
  * Preservam o envoltório convexo (*convex hull*) do espaço experimental ($C_{A0} \in \{0,10; 1,50\}\text{ mol/L}$ e $\eta \in \{0,5; 3,1\}$).
* [`test_dense.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Base%20de%20dados/processed/splits/test_dense.csv): **3 ensaios de Teste Cego (183 amostras)** — **Ensaio 8**, **Ensaio 14** e **Ensaio 7**.
  * Intocados durante a busca de hiperparâmetros; avaliam capacidade de interpolação pura nos 3 regimes cinéticos cruciais.
* [`scalers.joblib`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Base%20de%20dados/processed/splits/scalers.joblib): Transformadores `StandardScaler` ajustados exclusivamente no treino.
* [`cv_folds_info.json`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Base%20de%20dados/processed/splits/cv_folds_info.json): Mapeamento das 4 dobras disjuntas por ensaio (`GroupKFold`).

### 3.2. Protocolo de Validação Cruzada (GroupKFold de 4 Dobras)
A otimização de hiperparâmetros de cada algoritmo será conduzida exclusivamente com os dados de treino rotacionados nas 4 dobras:
* **Fold 1**: Validação nos Ensaios `[1, 5, 11, 16]` (4 ensaios, 244 amostras) | Treino nos 9 restantes.
* **Fold 2**: Validação nos Ensaios `[4, 10, 15]` (3 ensaios, 183 amostras) | Treino nos 10 restantes.
* **Fold 3**: Validação nos Ensaios `[3, 9, 13]` (3 ensaios, 183 amostras) | Treino nos 10 restantes.
* **Fold 4**: Validação nos Ensaios `[2, 6, 12]` (3 ensaios, 183 amostras) | Treino nos 10 restantes.

---

## 4. Detalhamento da Subfase 3.2.1: Multi-Layer Perceptron (MLP)

### 4.1. Fundamentação e Desafios Físicos
A taxa de retração interfacial $|v(t)|$ apresenta uma dinâmica com **duas escalas temporais acentuadas**:
1. *Primeiros instantes ($t < 1\text{ min}$)*: Alta velocidade inicial ($v_0 \approx 200 - 1200\ \mu\text{m/min}$) governada pelo contato inicial e elevada força motriz ácida.
2. *Cauda assintótica ($t > 3\text{ min}$)*: Decaimento exponencial rápido para valores residuais ($v \to 0 - 0{,}1\ \mu\text{m/min}$).

Modelos neurais ingênuos sofrem de dois problemas comuns nesse cenário:
* Instabilidade ou saturação na cauda assintótica (oscilações espúrias que produzem taxas negativas);
* Descontinuidades nas derivadas se usarem funções do tipo ReLU (*dead neurons*).

### 4.2. Decisões de Arquitetura do MLP
1. **Framework e Dispositivo**:
   * PyTorch 2.5 executado em **CPU** (com otimização de threads MKL/OpenMP).
   * Justificativa: Para matrizes tabulares de $N = 793$ amostras e $D = 4$ features, a execução em CPU é quase instantânea ($< 5\text{ ms}$ por época) e evita qualquer incompatibilidade de arquitetura da GPU.
2. **Topologia de Camadas**:
   * Entrada: 4 neurônios normalizados $[T_{\text{norm}}, C_{A0,\text{norm}}, \eta_{\text{norm}}, t_{\text{norm}}]$.
   * Ocultas: Arquiteturas exploradas na grade:
     * Arquitetura A: `[64, 32]` (leve, baixo risco de overfitting);
     * Arquitetura B: `[128, 64, 32]` (maior expressividade para capturar acoplamento não-linear $C_{A0} \times \eta$).
3. **Funções de Ativação**:
   * **GELU (*Gaussian Error Linear Unit*)** ou **SiLU/Swish**:
     $$\text{GELU}(x) = x \cdot \Phi(x) \approx 0{,}5 x \left[ 1 + \tanh\left(\sqrt{\frac{2}{\pi}} \left(x + 0{,}044715 x^3\right)\right) \right]$$
     Garante curvatura suave e derivada contínua em todo o domínio, ideal para integração posterior no PBM.
4. **Camada de Saída com Projeção Física**:
   * Camada linear que projeta para 1 neurônio.
   * Aplicação da função **Softplus**:
     $$\text{Softplus}(x) = \ln\left(1 + e^x\right) \ge 0$$
     Assegura que a taxa predita seja **estritamente não-negativa** ($|v| \ge 0$), impedindo a violação da segunda lei da termodinâmica (crescimento artificial de partícula em meio lixiviante).
5. **Função de Perda (Loss)**:
   * **Huber Loss (Smooth L1 Loss)** com $\beta = 1{,}0$:
     $$L_\beta(y, \hat{y}) = \begin{cases} 0{,}5 (y - \hat{y})^2, & \text{se } |y - \hat{y}| < \beta \\ \beta \left( |y - \hat{y}| - 0{,}5 \beta \right), & \text{caso contrário} \end{cases}$$
     Confere robustez frente a ordens de magnitude discrepantes entre o pico inicial e a cauda lenta.
6. **Otimizador e Regularização**:
   * `AdamW` com taxa de aprendizado inicial $\eta_0 \in [10^{-3}, 3 \times 10^{-4}]$.
   * *Weight Decay* ($L_2$): $10^{-4}$ a $10^{-3}$.
   * *Dropout*: $5\%$ a $10\%$ nas camadas intermediárias.
   * *Early Stopping*: Interrupção caso a loss de validação não melhore por 25 épocas consecutivas.

---

## 5. Roteiro Passo a Passo de Execução da Subfase 3.2.1 (MLP)

1. **Criação do Módulo Neural**:
   * Implementar `Código/etapas/etapa_3_2/subetapa_3_2_1_mlp/modelo_mlp.py`.
   * Definir a classe `KineticsMLP(nn.Module)` e a classe auxiliar `MLPRegressorWrapper` (compatível com `fit`, `predict`, `score`).
2. **Suíte de Testes Unitários Automatizados**:
   * Implementar `test_mlp.py` cobrindo:
     * Dimensões corretas de tensores (batch_size, 4) $\to$ (batch_size, 1);
     * Restrição física $|v| \ge 0$ para entradas arbitrárias (inclusive extremas);
     * Convergência da descida de gradiente em mini-batch dummy;
     * Determinismo e reproducibilidade via semente (`torch.manual_seed(42)`);
     * Serialização e recarga de pesos (`torch.save` / `torch.load`).
3. **Execução da Validação Cruzada e Treinamento**:
   * Implementar `treinar_avaliar_mlp.py`:
     * Itera sobre os 4 folds do `GroupKFold`;
     * Registra métricas de validação em cada dobra;
     * Treina a rede final consolidada em todos os 13 ensaios de treino;
     * Realiza inferência puramente cega nos 3 ensaios de teste (`test_dense.csv`);
     * Salva o checkpoint em `outputs/models_saved/mlp/mlp_kinetics_v1.pt`.
4. **Geração de Gráficos em 300 DPI (PNG + PDF)**:
   * `fig_07a_curvas_aprendizado_mlp.png`: Evolução das perdas de treino e validação por época;
   * `fig_07b_predicoes_v_mlp.png`: Trajetórias temporais $|v(t)|$ preditas vs. reais para os 16 ensaios;
   * `fig_07c_paridade_e_residuos_mlp.png`: Gráfico de paridade ($|v|_{\text{pred}}$ vs $|v|_{\text{alvo}}$) e histograma de resíduos.
5. **Relatório Técnico e Tabela de Métricas**:
   * `tabela_metricas_mlp.csv`: $R^2$, RMSE, MAE e Max Error individuais e consolidados;
   * `relatorio_etapa_3_2_1_mlp.md`: Análise de desempenho físico e convergência.
6. **Atualização Cumulativa do `DEVLOG.md`**:
   * Registro completo da etapa com as 6 seções obrigatórias.

---

## 6. Critérios Quantitativos de Aprovação para o MLP

| Métrica | Critério Mínimo | Meta Desejada | Significado Físico-Estatístico |
| :--- | :---: | :---: | :--- |
| **$R^2$ Global (Treino)** | $\ge 0{,}9800$ | $\ge 0{,}9900$ | Boa reprodução das cinéticas dos 13 ensaios de ajuste. |
| **$R^2$ Médio (CV - 4 Folds)** | $\ge 0{,}9400$ | $\ge 0{,}9650$ | Capacidade de generalização sem memorização de ensaios. |
| **$R^2$ Global (Teste Cego)** | $\ge 0{,}9300$ | $\ge 0{,}9600$ | Predição cega fidedigna nos Ensaios 8, 14 e 7. |
| **Violação Física ($|v| < 0$)** | **$0{,}00\%$** | **$0{,}00\%$** | Restrição inegociável de conservação de massa e termodinâmica. |
| **Tempo de Inferência** | $< 10\text{ ms}$ | $< 2\text{ ms}$ | Viabilidade para acoplamento numérico no solver PBM. |
