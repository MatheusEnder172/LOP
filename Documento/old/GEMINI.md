# Regras do Workspace: Relatório e Projeto LOP/TCC - Modelagem Híbrida de Lixiviação de Zinco

Este documento reúne todas as diretrizes de governança, padrões operacionais, critérios físicos e regras de redação técnica aplicáveis a este workspace e integradas ao projeto desenvolvido em `Codigo_v3`.

---

# PARTE 1: Regras Operacionais e de Governança do Projeto (Herdadas de Codigo_v3)

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
- **Atualização Obrigatória do `DEVLOG.md`**:
  - A cada nova tarefa, experimento, alteração relevante de código ou resolução de erro, deve-se registrar no arquivo `DEVLOG.md`:
    1. **Data e Hora**.
    2. **Objetivo da Atividade**.
    3. **Hipótese / Decisão de Design** (ex: escolha do estimador de α, tipo de função de ativação, tolerância do solver ODE).
    4. **O que Funcionou** (com métricas quantitativas: r², RMSE, MAE, tempo de convergência).
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
  - Rótulos de eixos obrigatoriamente acompanhados de suas respectivas unidades no Sistema Internacional ou unidades usuais do processo (ex: C_Af (mol/L), t (min), X_Zn (-)).

---

## 4. Consistência Física e Restrições Inegociáveis
- **Conservação de Massa**: A conversão mássica de zinco (X_Zn) deve estar estritamente no intervalo [0, 1] (ou 0 a 100%). Predições fora desse intervalo violam princípios fundamentais da termodinâmica e devem ser barradas ou tratadas com *clipping* / funções de projeção física.
- **Concentrações de Solvente**: A concentração de ácido livre (C_Af) nunca pode ser negativa.
- **Significado Físico dos Parâmetros Estimados**: Parâmetros como k_s, α e v(D) devem respeitar ordens de grandeza fisicamente plausíveis demonstradas na literatura experimental.

---

## 5. Política de Preservação e Depreciação de Arquivos (Subpasta `old/`)
- **Proibição de Exclusão Definitiva**:
  - Ao realizar novas análises, refatorações ou correção de erros, **nunca exclua permanentemente** arquivos gerados (gráficos, tabelas, imagens, relatórios, dados processados ou scripts).
- **Movimentação para a Subpasta `old/`**:
  - Caso qualquer arquivo precise ser substituído ou descartado, ele deve ser movido para uma subpasta denominada `old/` dentro do próprio diretório da etapa atual em execução (ex: `Código/etapas/etapa_X_Y/.../old/` ou no diretório de saídas da etapa).
- **Registro Obrigatório de Justificativa**:
  - Documentar no `DEVLOG.md` ou README da pasta `old/`: arquivo depreciado, motivo da descontinuação e arquivo substituto.

---

# PARTE 2: Regras de Redação Técnica e Metodologia do Relatório

## 6. Padrão de Escrita Acadêmica
- **Linguagem**: Português formal, na terceira pessoa do singular passiva ou impessoal ("realizou-se", "procedeu-se", "os dados foram", "verificou-se").
- **Tempo verbal**: Pretérito perfeito para procedimentos experimentais e computacionais realizados; presente do indicativo para leis constitutivas permanentes.
- **Nível técnico**: Nível de Engenharia Química (UFMG), com formalismo matemático, hidrometalúrgico e de machine learning.
- **Citações**: Formato ABNT (Autor, Ano) no corpo do texto; referências completas ao final.

---

## 7. Consistência com o Relatório Parcial Existente
- **Documento de referência**: `RELATÓRIO PARCIAL LOP - Revisão.docx.pdf`.
- **Continuidade vocabular**: Adotar termos padronizados já definidos na revisão bibliográfica (razão molar η, conversão fracionária X_Zn, concentrado ustulado, calcina, lixiviação neutra, Herbst, balanço populacional).
- **Notação Matemática no Markdown**: Utilizar caracteres Unicode limpos (η, α, μm, ², ³, ≈, ≤, ≥, →, ±), evitando comandos crus de LaTeX.

---

## 8. Rastreabilidade e Precisão Numérica
- Toda menção a dados empíricos deve citar a fonte primária (Bortot Coelho, 2017: capítulo, tabela, página) e os arquivos CSV rastreados em `RASTREABILIDADE_DADOS.md`.
- Especificar rigorosamente as variáveis operacionais: temperatura (80 °C), velocidade de agitação (400 rpm), volume do reator (1,0 L), granulometria da calcina e estequiometria.

---

## 9. Política de Geração Iterativa
- Cada subseção da Seção 4 (Materiais e Métodos) é redigida em arquivo `.md` independente na pasta `metodologia/`.
- Cada subseção passa por revisão e validação do usuário antes do avanço para a seguinte.
