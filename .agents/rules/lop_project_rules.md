---
trigger: always_on
---

# Regras Operacionais do Projeto LOP - Modelagem Híbrida de Lixiviação de Zinco

Este documento estabelece as diretrizes de governança, padrões de código, documentação e critérios físicos que o agente deve seguir em todas as etapas de desenvolvimento do projeto.

---

## 1. Princípios de Engenharia de Software e Clean Code
- **Linguagem e Bibliotecas**: Python 3.10+ utilizando `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn` e `torch`.
- **Tipagem e Documentação**:
  - Todas as funções e classes públicas devem conter Type Hints explícitos.
  - Docstrings em formato Google ou NumPy descrevendo entradas, saídas, exceções e o significado físico-químico dos parâmetros.
- **Arquitetura Modular (SOLID)**:
  - `src/physics/`: Cálculos estritamente mecanicistas (leis de conservação, cinéticas, Balanço Populacional).
  - `src/ml/`: Modelos orientados por dados, pré-processamento, scalers e rotinas de treinamento supervisionado.
  - `src/hybrid/`: Acoplamento entre os modelos físicos e de dados (Serial, Paralelo, KAH).
  - `src/utils/`: Métricas estatísticas de avaliação e padronização estética de gráficos.
  - `experiments/`: Scripts de execução e testes.
  - `outputs/`: Diretório exclusivo para armazenamento de figuras, modelos salvos e relatórios tabulares.

---

## 2. Rastreabilidade, Versionamento e o "Notepad" Central (`DEVLOG.md`)
- **Atualização Obrigatória e Cumulativa do `DEVLOG.md`**:
  - O `DEVLOG.md` é o registro histórico vital do projeto. **É expressamente proibido apagar, truncar, resumir ou substituir registros de etapas anteriores**. Toda nova atividade deve ser adicionada preservando integralmente o histórico de tudo o que já foi realizado.
  - A cada nova tarefa, experimento, alteração relevante de código ou resolução de erro, o agente deve registrar no arquivo `DEVLOG.md`:
    1. **Data e Hora**.
    2. **Objetivo da Atividade**.
    3. **Hipótese / Decisão de Design** (ex: escolha do estimador de $\alpha$, tipo de função de ativação, tolerância do solver ODE).
    4. **O que Funcionou** (com métricas quantitativas: $R^2$, RMSE, MAE, tempo de convergência).
    5. **O que Falhou / Problemas Encontrados** (ex: instabilidade numérica na integração de partículas finas, overfitting do Random Forest na extrapolação, gradiente nulo).
    6. **Ações Corretivas e Próximos Passos**.
- **Versionamento de Modelos**:
  - Checkpoints de modelos devem ser salvos em `Código/outputs/models_saved/` com nomenclatura clara e versionada (ex: `serial_mlp_v1.joblib` ou `serial_mlp_v1.pt`).

---

## 3. Padrão Estético de Visualização Científica (300 DPI)
- Todos os gráficos gerados devem seguir um padrão visual unificado e limpo:
  - Resolução mínima de **300 DPI** em formato `.png` e cópia em `.pdf` (vetorial).
  - Fontes legíveis (tamanho de eixos 11-12 pt, título 13-14 pt, ticks 10 pt).
  - Paleta de cores científica acessível e com alto contraste (evitar esquemas de cores padrão sem contraste).
  - Dados experimentais sempre representados por marcadores discretos com barras de erro (intervalo de confiança ou desvio padrão da triplicata).
  - Curvas de modelos teóricos representadas por linhas contínuas ou tracejadas suaves.
  - Rótulos de eixos obrigatoriamente acompanhados de suas respectivas unidades no Sistema Internacional ou unidades usuais do processo (ex: $C_{Af}\ (\text{mol}\cdot\text{L}^{-1})$, $t\ (\text{min})$, $X_{\text{Zn}}\ (-)$).

---

## 4. Consistência Física e Restrições Inegociáveis
- **Conservação de Massa**: A conversão mássica de zinco ($X_{\text{Zn}}$) deve estar estritamente no intervalo $[0, 1]$ (ou $0$ a $100\%$). Predições fora desse intervalo violam princípios fundamentais da termodinâmica e devem ser barradas ou tratadas com *clipping* / funções de projeção física.
- **Concentrações de Solvente**: A concentração de ácido livre ($C_{Af}$) nunca pode ser negativa.
- **Significado Físico dos Parâmetros Estimados**: Parâmetros como $k_s$, $\alpha$ e $v(D)$ devem respeitar ordens de grandeza fisicamente plausíveis demonstradas na literatura experimental.

## 5. Política de Preservação e Depreciação de Arquivos (Subpasta `old/`)
- **Proibição de Exclusão Definitiva**:
  - Ao realizar novas análises, refatorações ou correção de erros, **nunca exclua permanentemente** arquivos gerados (gráficos, tabelas, imagens, relatórios, dados processados ou scripts).
- **Movimentação para a Subpasta `old/`**:
  - Caso qualquer arquivo precise ser substituído ou descartado, ele deve ser movido para uma subpasta denominada `old/` dentro do próprio diretório da etapa atual em execução (ex: `Código/etapas/etapa_X_Y/.../old/` ou no diretório de saídas da etapa).
- **Registro Obrigatório de Justificativa**:
  - Junto aos arquivos movidos para a pasta `old/`, deve constar a justificativa documentada do descarte/substituição (registrada em um arquivo de log/README dentro de `old/` ou devidamente detalhada no `DEVLOG.md`), contendo:
    1. Arquivo(s) depreciado(s).
    2. Data e motivo da descontinuação (ex.: erro de escala, inconsistência em dados, nova rotina aprimorada).
    3. Novo arquivo gerado em substituição (quando aplicável).

