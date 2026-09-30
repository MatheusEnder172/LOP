# Etapa 3.1: Partição dos Dados e Pré-Processamento (Estratégia 85/15)

## 1. Visão Geral

Esta etapa prepara os dados cinéticos de bancada gerados na [Etapa 2.1](../etapa_2_1_otimizacao_alvos_v/README.md) para treinamento supervisionado de algoritmos de Machine Learning (Fase 3 — Modelos Black-Box DDM).

A partição dos dados foi estruturada sob o paradigma **85/15** aprovado pelo usuário:
- **Treino (81,25%)**: 13 ensaios com Validação Cruzada por Ensaio (`GroupKFold`, 4 dobras) para seleção e otimização de hiperparâmetros.
- **Teste Cego (18,75%)**: 3 ensaios estritamente intocados durante toda a modelagem para avaliação imparcial final.

---

## 2. Critérios Físico-Químicos e Estatísticos de Seleção

### 2.1 Ensaios de Teste Cego: Ensaios 8, 14 e 7
1. **Preservação do Envoltório Convexo (*Convex Hull*)**:
   - Os 4 cantos da matriz fatorial ($C_{A0} \in \{0,10; 1,50\}$ mol/L e $\eta \in \{0,5; 3,1\}$) e todas as bordas externas permanecem 100% no conjunto de treino.
   - Isso garante que os ensaios de teste representem **interpolação pura**: o modelo é avaliado no que deve dominar com perfeição antes de ser levado a cenários de extrapolação na Fase 5.
2. **Alternância de Concentrações Intermediárias**:
   - Ensaio 8: $C_{A0} = 0,50$ mol/L ($\eta = 1,0$).
   - Ensaio 14: $C_{A0} = 1,00$ mol/L ($\eta = 1,5$).
   - Ensaio 7: $C_{A0} = 0,50$ mol/L ($\eta = 3,1$).
   - Evita viés em uma única faixa de concentração de solvente ácido.
3. **Representatividade dos Regimes Cinéticos**:
   - **Ensaio 8**: Lixiviação neutra estequiométrica (patamar em $87\%$, esgotamento gradual de $C_{Af}$).
   - **Ensaio 14**: Lixiviação ácida branda (leve superávit, conversão em $97\%$).
   - **Ensaio 7**: Lixiviação ácida forte (conversão $100\%$, cinética ultrarrápida).
4. **Proteção da Restrição de Esgotamento ($\eta = 0,5$)**:
   - Todos os 4 ensaios de deficiência de ácido permanecem no treino para garantir que o corte assintótico ($X_{\text{Zn}} \approx 0,50$) seja plenamente assimilado pelos regressores.

---

## 3. Estrutura dos Arquivos Gerados

* `Base de dados/processed/splits/`:
  * `train_dense.csv`: 793 amostras (13 ensaios × 61 nós de tempo).
  * `test_dense.csv`: 183 amostras (3 ensaios × 61 nós de tempo).
  * `train_exp.csv`: 104 amostras (13 ensaios × 8 tempos medidos).
  * `test_exp.csv`: 24 amostras (3 ensaios × 8 tempos medidos).
  * `scalers.joblib`: Transformadores `StandardScaler` ajustados exclusivamente no treino.
  * `cv_folds_info.json`: Mapeamento das 4 dobras de validação cruzada do `GroupKFold`.
* `Código/outputs/etapa_3_1/`:
  * `fig_06_particao_espaco_experimental.png` / `.pdf` (300 DPI).
  * `tabela_particao_splits.csv`.
  * `relatorio_validacao_etapa_3_1.md`.

---

## 4. Instruções de Execução e Testes

```powershell
# Executar a partição e gerar saídas
python Código/etapas/etapa_3_1_preprocessing/executar_particao.py

# Executar a suíte de testes unitários da etapa
pytest Código/etapas/etapa_3_1_preprocessing/test_preprocessing.py -v
```
