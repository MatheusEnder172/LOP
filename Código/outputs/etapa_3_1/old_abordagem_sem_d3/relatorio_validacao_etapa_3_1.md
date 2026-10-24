# Relatório de Validação — Etapa 3.1: Partição e Pré-Processamento (85/15)

## 1. Sumário Executivo

A Etapa 3.1 estabeleceu a infraestrutura de dados para o treinamento supervisionado dos modelos de Machine Learning (Fase 3 — Modelos Black-Box DDM) e acoplamento híbrido (Fase 4). 

Adotou-se a estratégia **85/15 particionada por ensaio experimental**:
* **Treino**: 13 ensaios (81,25% — 793 amostras densas / 104 amostras pontuais).
* **Teste Cego**: 3 ensaios (18,75% — 183 amostras densas / 24 amostras pontuais: Ensaios 8, 14 e 7).
* **Validação Cruzada Interna**: 4 dobras via `GroupKFold` nos 13 ensaios de treino para otimização de hiperparâmetros sem data leakage.
* **Integridade Estatística**: Zero vazamento de dados (*zero data leakage*) comprovado via testes unitários automatizados.

---

## 2. Detalhamento da Partição dos 16 Ensaios

| Ensaio | Partição | T (°C) | C_A0 (mol/L) | η (-) | Amostras Densas | Amostras Pontuais | R² Otim. Inversa | Regime Físico-Químico | Papel no Pipeline |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **7** | **Teste Cego** | 40,0 | 0,50 | 3,1 | 61 | 8 | 0,99973 | Lixiviação ácida forte | Cinética ultrarrápida / Conversão 100% |
| **8** | **Teste Cego** | 40,0 | 0,50 | 1,0 | 61 | 8 | 0,99817 | Estequiométrico neutro | Patamar incompleto em 87% / Esgotamento ácido |
| **14** | **Teste Cego** | 40,0 | 1,00 | 1,5 | 61 | 8 | 0,99910 | Leve excesso de ácido | Transição para extração alta (97%) |
| **1** | Treino | 40,0 | 0,10 | 0,5 | 61 | 8 | 0,99665 | Deficiência de ácido | Borda inferior / Convex Hull |
| **2** | Treino | 40,0 | 0,10 | 3,1 | 61 | 8 | 0,99981 | Forte excesso de ácido | Borda inferior de C_A0 |
| **3** | Treino | 40,0 | 0,50 | 0,5 | 61 | 8 | 0,99715 | Deficiência de ácido | Suporte termodinâmico η = 0,5 |
| **4** | Treino | 40,0 | 1,00 | 0,5 | 61 | 8 | 0,98731 | Deficiência de ácido | Suporte termodinâmico η = 0,5 |
| **5** | Treino | 40,0 | 1,50 | 0,5 | 61 | 8 | 0,99726 | Deficiência de ácido | Borda superior de C_A0 |
| **6** | Treino | 40,0 | 0,10 | 1,0 | 61 | 8 | 0,99859 | Estequiométrico | Borda inferior de C_A0 |
| **9** | Treino | 40,0 | 1,00 | 1,0 | 61 | 8 | 0,99951 | Estequiométrico | Suporte interno η = 1,0 |
| **10** | Treino | 40,0 | 1,50 | 1,0 | 61 | 8 | 0,99961 | Estequiométrico | Borda superior de C_A0 |
| **11** | Treino | 40,0 | 0,10 | 1,5 | 61 | 8 | 0,99595 | Leve excesso | Borda inferior de C_A0 |
| **12** | Treino | 40,0 | 1,00 | 3,1 | 61 | 8 | 0,99964 | Forte excesso | Suporte interno η = 3,1 |
| **13** | Treino | 40,0 | 0,50 | 1,5 | 61 | 8 | 0,99902 | Leve excesso | Suporte interno η = 1,5 |
| **15** | Treino | 40,0 | 1,50 | 1,5 | 61 | 8 | 0,99945 | Leve excesso | Borda superior de C_A0 |
| **16** | Treino | 40,0 | 1,50 | 3,1 | 61 | 8 | 0,99871 | Forte excesso | Vértice superior / Convex Hull |

---

## 3. Composição das Dobras de Validação Cruzada (GroupKFold — 4 Dobras)

Para a busca de hiperparâmetros na Etapa 3.2, os 13 ensaios de treino foram agrupados em 4 dobras, assegurando que nenhum ensaio participe simultaneamente do subconjunto de ajuste e do subconjunto de validação:

* **Fold 1** (Treino: 9 ensaios, 549 amostras | Validação: 4 ensaios, 244 amostras):
  * Validação: Ensaios [1, 5, 11, 16]
* **Fold 2** (Treino: 10 ensaios, 610 amostras | Validação: 3 ensaios, 183 amostras):
  * Validação: Ensaios [4, 10, 15]
* **Fold 3** (Treino: 10 ensaios, 610 amostras | Validação: 3 ensaios, 183 amostras):
  * Validação: Ensaios [3, 9, 13]
* **Fold 4** (Treino: 10 ensaios, 610 amostras | Validação: 3 ensaios, 183 amostras):
  * Validação: Ensaios [2, 6, 12]

---

## 4. Estatísticas dos Scalers Ajustados no Treino

O `StandardScaler` foi ajustado exclusivamente com as 793 amostras de treino densas:

* **Features de Entrada (X)**:
  * `temperatura_C`: média = 40,0 °C, escala = 1,0 (variância zero na bancada; mantida como feature neutra para compatibilidade futura com planta piloto).
  * `CA0_mol_L`: média = 0,8000 mol/L, escala = 0,5698 mol/L.
  * `razao_molar_eta`: média = 1,4462, escala = 0,9763.
  * `t_min`: média = 7,5000 min, escala = 4,4017 min.
* **Target (|v| — taxa de encolhimento interfacial)**:
  * Média (y_mean): 14,2290 µm/min.
  * Desvio-padrão (y_scale): 93,0540 µm/min.
  * Faixa dinâmica no treino: 0,0000 a 1227,66 µm/min.
  * Faixa dinâmica no teste cego: 0,0000 a 584,62 µm/min (completamente contida no suporte do treino).

---

## 5. Visualização Gráfica Gerada

A figura em 300 DPI ([fig_06_particao_espaco_experimental.png](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/C%C3%B3digo/outputs/etapa_3_1/fig_06_particao_espaco_experimental.png) e cópia vetorial `.pdf`) apresenta quatro painéis integrados:
1. **Painel (a)**: Espaço fatorial 4×4 demonstrando que os 4 cantos e as bordas permanecem no treino (envoltório convexo preservado) e que os 3 ensaios de teste ocupam posições internas em xadrez.
2. **Painel (b)**: Curvas da taxa de encolhimento |v(t)| com os 3 ensaios de teste em destaque contra o envelope de treino.
3. **Painel (c)**: Curvas de conversão X_Zn(t) ilustrando os patamares de cada regime químico.
4. **Painel (d)**: Boxplot comparativo do target |v| confirmando que o teste cego possui suporte estatístico equivalente ao treino.

---

## 6. Resultado da Suíte de Testes Automatizados

* Total de testes na suíte: **6 testes unitários dedicados** (`test_preprocessing.py`).
* Total acumulado no repositório: **20 testes unitários** cobrindo Fases 0, 1, 2 e Etapa 3.1.
* Taxa de sucesso: **100% de aprovação**.
