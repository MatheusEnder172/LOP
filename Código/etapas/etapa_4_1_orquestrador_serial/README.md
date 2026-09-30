# Subetapa 4.1: Orquestrador Híbrido Serial Permanente (DDM → PBM)

Este diretório contém a concepção, implementação, testes unitários e rotina de validação/demonstração da **Subetapa 4.1**, referente ao acoplamento híbrido serial permanente entre o modelo cinético orientado por dados (DDM Black-Box) e o modelo mecanicista de Balanço Populacional (PBM White-Box).

---

## 1. Estrutura do Diretório

```
etapa_4_1_orquestrador_serial/
├── README.md                          # Este documento de referência técnica
├── test_serial_hybrid.py              # Suíte com 7 testes unitários automatizados (100% aprovados)
└── executar_demonstracao_hibrido.py   # Script de simulação, validação em teste cego e geração de artefatos
```

---

## 2. Arquitetura do Modelo Híbrido Serial (`SerialHybridModel`)

O modelo permanente foi implementado em [`Código/src/hybrid/serial_hybrid.py`](../../src/hybrid/serial_hybrid.py), encapsulado na classe `SerialHybridModel`.

### 2.1 Fluxo de Informação e Acoplamento
1. **Entrada Operacional**: Condições de alimentação da lixiviação: Temperatura (T em °C), Concentração inicial de H₂SO₄ (C_A0 em mol/L) e Razão molar estequiométrica (η = mol H₂SO₄ / mol ZnS).
2. **Preditor Cinético DDM**: O modelo DDM (por padrão, o Campeão Random Forest selecionado na Etapa 3.2.5) infere a trajetória contínua da taxa de dissolução diametral |v(t)| em µm/min.
3. **Mecanismo de Integração Fina**: A taxa |v(t)| é integrada temporalmente gerando o perfil de retração interfacial cumulativa δ(t) = ∫ |v(τ)| dτ.
4. **Solver PBM Polidisperso**: O perfil δ(t) alimenta o solver analítico-numérico do PBM (`BatchPBMSolver`), que realiza a convolução granulométrica sobre a distribuição contínua de Rosin-Rammler-Bennett (RRB) para calcular a conversão global de zinco X_Zn(t) e a concentração residual de ácido livre C_Af(t).

### 2.2 Descoberta Numérica: Resolução da Malha de Integração Sub-Segundo
- **Problema Identificado**: Na malha temporal experimental esparsa (8 pontos: 0, 0,5, 1, 2, 3, 6, 10, 15 min), a aplicação direta da regra dos trapézios com Δt = 0,5 min superestima a retração inicial δ em quase 5×, pois |v(t)| decai bruscamente de ~600 µm/min para < 30 µm/min nos primeiros 3 segundos (t < 0,05 min).
- **Solução Implementada**: O orquestrador constrói internamente uma malha contínua ultra-fina (Δt ≤ 0,03 min, N ≥ 500 nós) para a integração cumulativa de δ(t), interpolando os resultados de volta aos tempos desejados de amostragem. Isso garantiu precisão matemática rigorosa e estabilidade absoluta.

### 2.3 Garantias e Restrições Físicas Estritas
- **Não-negatividade de velocidade**: |v(t)| ≥ 0 em qualquer ponto temporal.
- **Monotonicidade de retração**: dδ/dt ≥ 0, assegurando que o raio das partículas nunca cresça durante a dissolução.
- **Conservação de Massa**: A conversão de zinco X_Zn(t) é estritamente limitada ao intervalo físico [0, 1] e ao teto estequiométrico máximo (X_Zn ≤ η).
- **Concentração de Reagente**: C_Af(t) = max(0, C_A0 · (1 - X_Zn(t)/η)) ≥ 0 mol/L.

---

## 3. Interoperabilidade e Carregamento Automático

O `SerialHybridModel` possui suporte nativo plug-and-play a todos os modelos desenvolvidos na Etapa 3.2:
- `random_forest` (Campeão Geral da Etapa 3.2.5);
- `mlp` (Multi-Layer Perceptron PyTorch);
- `xgboost` (XGBoost Regressor);
- `svr` (Support Vector Regression RBF).

Caso instanciado sem argumentos (`SerialHybridModel()`), o orquestrador consulta o arquivo de metadados [`Código/outputs/models_saved/modelo_campeao_info.json`](../../outputs/models_saved/modelo_campeao_info.json) e carrega automaticamente o modelo campeão com seus respectivos artefatos de normalização.

---

## 4. Resultados da Demonstração nos Ensaios de Teste Cego

O modelo híbrido serial campeão (Random Forest acoplado ao PBM) foi testado nos 3 ensaios mantidos 100% intocados durante toda a fase de calibração:

| Ensaio | Regime Operacional | R² (Conversão X_Zn) | RMSE (-) | MAE (-) | X_Zn Final (Pred) | X_Zn Final (Exp) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ensaio 8** | Estequiométrico Neutro (η = 1,0; 70 °C) | **0,9628** | 0,0544 | 0,0493 | 0,913 | 0,870 |
| **Ensaio 14** | Leve Excesso Ácido (η = 1,5; 70 °C) | **0,9975** | 0,0157 | 0,0113 | 0,976 | 0,970 |
| **Ensaio 7** | Forte Excesso Ácido (η = 3,1; 70 °C) | **0,9972** | 0,0170 | 0,0123 | 0,990 | 1,010 |

**Média no Teste Cego**: **R² > 0,985** e **RMSE < 0,029**, demonstrando alta capacidade de generalização e fidelidade física em condições não vistas no treinamento.

---

## 5. Artefatos Produzidos

Os artefatos visuais e tabulares gerados por esta subetapa encontram-se em [`Código/outputs/etapa_4_1_orquestrador_serial/`](../../outputs/etapa_4_1_orquestrador_serial/):
- `fig_demonstrativa_hibrido_ensaio8.png` e `.pdf` (Painel quadruplo em 300 DPI: cinética |v(t)|, recuo δ(t), conversão X_Zn(t) comparada com FPM Puro e Experimento, e consumo de ácido C_Af(t));
- `tabela_demonstracao_ensaios_teste.csv` (Métricas consolidadas para os ensaios de teste);
- `relatorio_etapa_4_1_orquestrador_serial.md` (Sumário técnico executivo).
