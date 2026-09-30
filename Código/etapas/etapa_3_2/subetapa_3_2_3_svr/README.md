# Subetapa 3.2.3: Support Vector Regression (SVR com Kernel RBF)

Este diretório contém a implementação completa, testes unitários, rotina de validação cruzada por ensaios e treinamento da **Subetapa 3.2.3**, correspondente ao terceiro modelo de Machine Learning Black-Box (DDM puro) para a predição da taxa de retração interfacial $|v(t)| = dD/dt$ a partir das condições operacionais do reator de lixiviação de zinco ($T$, $C_{A0}$, $\eta$, $t$).

---

## 1. Estrutura do Diretório

```
subetapa_3_2_3_svr/
├── README.md                 # Este documento de referência e guia técnico
├── modelo_svr.py             # Classe KineticsSVR encapsulando SVR RBF do scikit-learn
├── treinar_avaliar_svr.py    # Pipeline de CV (GroupKFold), tuning, treino e diagnóstico
└── test_svr.py               # Suíte de 6 testes unitários automatizados
```

---

## 2. Fundamentação Teórica e Modelagem Física

### 2.1 Formulação do Target e Não-Negatividade Física Estrita
A taxa de dissolução $|v(t)|$ cobre mais de quatro ordens de magnitude. No SVR com perda $\epsilon$-insensível, operar em escala linear direta tornaria inviável a escolha de um tubo $\epsilon$ que atendesse simultaneamente ao pico ultra-rápido ($> 1000$ µm/min) e à cauda lenta ($< 0,1$ µm/min).

Para assegurar sensibilidade uniforme e estrita consistência termodinâmica:
$$y_{\text{log}} = \ln(1 + |v|)$$
$$\hat{v}(t) = \max\left(0,\ \exp(\hat{y}_{\text{log}}) - 1\right)$$

O modelo garante **0,00% de violações físicas** ($|v| \ge 0$ rigorosamente em todas as predições).

### 2.2 Padronização Obrigatória de Features (`StandardScaler`)
Como o kernel RBF é baseado na distância euclidiana $\|\mathbf{x}_i - \mathbf{x}_j\|^2$ no espaço de atributos, as quatro variáveis preditoras são rigorosamente padronizadas através do `StandardScaler` calibrado na Etapa 3.1.

---

## 3. Comparativo de Hiperparâmetros na Validação Cruzada (GroupKFold — 4 Dobras)

Foram investigadas cinco configurações de hiperparâmetros nas 4 dobras disjuntas por ensaio:

| Configuração | C | Epsilon ($\epsilon$) | Gamma ($\gamma$) | Target | R² Médio (CV) | RMSE Médio (µm/min) | MAE Médio (µm/min) | SVs Médios | Diagnóstico |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SVR-Baseline (Default)** | 1,0 | 0,10 | `scale` | `log1p` | 0,0151 ± 0,0326 | 89,73 | 13,84 | 203 | Sub-ajuste severo |
| **SVR-Regularizado (Largo)** | 10,0 | 0,20 | 0,10 | `log1p` | 0,0528 ± 0,0664 | 87,90 | 13,84 | 176 | Rigidez excessiva |
| **SVR-Acurado (C=25)** | 25,0 | 0,05 | `scale` | `log1p` | 0,0711 ± 0,0755 | 87,03 | 14,07 | 204 | Transição viés-variância |
| **SVR-Otimizado (Campeão)** | **100,0** | **0,10** | **0,50** | `log1p` | **0,0743 ± 0,0666** | **86,80** | **16,78** | **123** | **CAMPEÃ (Ótimo de Generalização)** |
| **SVR-LinearTarget** | 10,0 | 1,00 | `scale` | `linear` | 0,0098 ± 0,0182 | 90,02 | 14,30 | 129 | Perda total da fase lenta |

**Conclusão da Seleção**: A configuração **SVR-Otimizado ($C = 100{,}0$, $\epsilon = 0{,}10$, $\gamma = 0{,}50$)** venceu a validação cruzada, proporcionando a melhor flexibilidade para capturar os picos cinéticos sem degradar a estabilidade assintótica.

---

## 4. Desempenho do Modelo Campeão Consolidado

O modelo campeão foi retreinado com todos os 13 ensaios de treino e avaliado no conjunto de **Teste Cego (183 amostras intocadas: Ensaios 8, 14 e 7)**:

### 4.1 Métricas Globais
* **Conjunto de Treino (13 ensaios — 793 amostras)**:
  * R²: **0,1473** | RMSE: **85,93 µm/min** | MAE: **9,59 µm/min**
* **Conjunto de Teste Cego (3 ensaios — 183 amostras)**:
  * R²: **0,6031** | RMSE: **41,04 µm/min** | MAE: **8,16 µm/min**
  * **Violação Física ($|v| < 0$): 0,00%** (100% fisicamente consistente)
* **Esparsidade dos Vetores de Suporte**:
  * Vetores de Suporte Ativos: **165 de 793 (20,8%)**
  * Esparsidade: **79,2% das amostras de treino situam-se dentro do tubo $\epsilon$** e não participam da inferência.

### 4.2 Desempenho por Ensaio de Teste Cego
* **Ensaio 14 ($\eta = 1,5$; $C_{A0} = 1,00$ mol/L — Leve Excesso Ácido)**: R² = **0,9692** | RMSE = **10,12 µm/min** | MAE = **2,26 µm/min** (precisão excepcional)
* **Ensaio 7 ($\eta = 3,1$; $C_{A0} = 0,50$ mol/L — Forte Excesso Ácido)**: R² = **0,5287** | RMSE = **51,16 µm/min** | MAE = **15,37 µm/min**
* **Ensaio 8 ($\eta = 1,0$; $C_{A0} = 0,50$ mol/L — Estequiométrico Neutro)**: R² = **0,3843** | RMSE = **48,31 µm/min** | MAE = **6,85 µm/min**

---

## 5. Checkpoints e Artefatos Gerados

* **Modelo Serializado**: `Código/outputs/models_saved/svr/svr_kinetics_v1.joblib`
* **Metadados e Hiperparâmetros**: `Código/outputs/models_saved/svr/svr_config.json`
* **Guia Didático e Teórico**: [`fundamentacao_e_aplicacao_svr_LOP.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_3_2/subetapa_3_2_3_svr/fundamentacao_e_aplicacao_svr_LOP.md)
* **Relatório Técnico Completo**: `Código/outputs/etapa_3_2/subetapa_3_2_3_svr/relatorio_etapa_3_2_3_svr.md`
* **Tabelas de Resultados**:
  * `Código/outputs/etapa_3_2/subetapa_3_2_3_svr/tabela_metricas_svr.csv`
  * `Código/outputs/etapa_3_2/subetapa_3_2_3_svr/tabela_comparativo_hiperparametros_svr.csv`
* **Figuras Científicas em 300 DPI e PDF Vetorial**:
  * `fig_09a_vetores_suporte_e_sensibilidade_svr.png` / `.pdf`: Localização temporal e distribuição por $\eta$ dos vetores de suporte.
  * `fig_09b_predicoes_v_svr.png` / `.pdf`: Trajetórias temporais de $|v(t)|$ preditas vs. observadas nos 16 ensaios.
  * `fig_09c_paridade_e_residuos_svr.png` / `.pdf`: Diagramas de paridade 1:1 e distribuição de resíduos.
  * `fig_09d_comparativo_hiperparametros_svr.png` / `.pdf`: Comparativo quantitativo de R² e RMSE entre as configurações avaliadas.

---

## 6. Como Executar

### 6.1 Testes Unitários Automatizados
```bash
pytest Código/etapas/etapa_3_2/subetapa_3_2_3_svr/test_svr.py -v
```

### 6.2 Execução do Treinamento e Avaliação
```bash
python Código/etapas/etapa_3_2/subetapa_3_2_3_svr/treinar_avaliar_svr.py
```
