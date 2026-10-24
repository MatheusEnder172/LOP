---
trigger: always_on
description: Regras de Redação Técnica e Governança do Relatório LOP/TCC
---

# Regras de Redação Técnica: Relatório LOP/TCC - Modelagem Híbrida de Lixiviação de Zinco

Este documento estabelece as diretrizes de estilo, estrutura e qualidade para a redação do relatório técnico da disciplina Laboratório de Operações e Processos (LOP/DEQ/UFMG).

---

## 1. Padrão de Escrita Acadêmica

- **Linguagem**: Português formal, na terceira pessoa do singular passiva ou impessoal ("realizou-se", "procedeu-se", "os dados foram", "verificou-se").
- **Tempo verbal**: Pretérito perfeito para ações concluídas e descrição de procedimentos experimentais; presente do indicativo para afirmações teóricas e relações constitutivas permanentes.
- **Nível técnico**: Compatível com monografia de graduação em Engenharia Química (UFMG), pressupondo familiaridade do leitor com cinética heterogênea, hidrometalurgia e conceitos básicos de ML.
- **Citações**: Formato ABNT (Autor, Ano) no corpo do texto; lista de referências em ordem alfabética.

---

## 2. Consistência com o Relatório Parcial Existente

- **Modelo de referência**: O documento `RELATÓRIO PARCIAL LOP - Revisão.docx.pdf` define o estilo, tom, profundidade e estrutura a serem seguidos.
- **Seções existentes**: Introdução (Seção 1), Objetivos (Seção 2), Revisão Bibliográfica (Seção 3), Materiais e Métodos (Seção 4 – a ser preenchida), Resultados e Discussão (Seção 5), Conclusões (Seção 6), Referências (Seção 7).
- **Continuidade de vocabulário**: Usar exatamente os mesmos termos e definições já introduzidos na revisão bibliográfica (ex: "razão molar η", "conversão fracionária X_Zn", "concentrado ustulado", "calcina", "lixiviação neutra", etc.).
- **Figuras e tabelas**: Numeração sequencial conforme o documento (Figura XX, Tabela XX), com fonte citada.

---

## 3. Rastreabilidade e Precisão Técnica

- **Todos os dados experimentais** citados na metodologia devem referenciar a fonte exata: documento, capítulo, seção, tabela e página.
- **Equações e parâmetros**: Quando houver equações, citar o número da equação no documento-fonte e fornecer o significado físico de cada variável.
- **Condições experimentais**: Especificar sempre as condições com precisão (temperatura, agitação, volume, concentrações, massa de sólido, razão molar).
- **Consistência numérica**: Usar os mesmos valores reportados na dissertação-fonte (Bortot Coelho, 2017) e nos CSVs rastreados em `RASTREABILIDADE_DADOS.md`.

---

## 4. Estrutura da Seção 4 (Materiais e Métodos)

A seção de Materiais e Métodos deve conter, no mínimo:

### 4.1. Procedimentos Experimentais
- Descrição do sistema experimental (matéria-prima, reagentes, condições operacionais).
- Origem e rastreabilidade dos dados experimentais (dissertação-fonte).

### 4.2. Análise Exploratória dos Dados (EDA)
- Etapa 0.1: Visualização e análise dos dados cinéticos de bancada.
- Etapa 0.2: Visualização e validação da distribuição granulométrica.

### 4.3. Implementação Computacional
- Linguagem, bibliotecas e ferramentas utilizadas.
- Estrutura modular do código.
- Critérios de qualidade (métricas estatísticas).

### 4.4. Modelo Fenomenológico de Primeiros Princípios (FPM)
- Equações governantes do balanço populacional.
- Cinética de dissolução e relação de Herbst.

### 4.5. Modelos Orientados por Dados (DDM)
- Algoritmos avaliados, hiperparâmetros, estratégias de treinamento/validação.

### 4.6. Modelo Híbrido
- Arquitetura serial, acoplamento FPM+DDM.

---

## 5. Política de Geração e Revisão de Texto

- **Formato de entrega**: Cada subseção da metodologia será escrita em Markdown (.md) neste workspace, para posterior transposição ao documento Word/PDF final.
- **Revisões iterativas**: O usuário revisará cada subseção antes de prosseguir para a próxima.
- **Não modificar seções existentes** do relatório sem solicitação explícita.
- **Notação científica**: Usar Unicode limpo no Markdown (η, α, μm, ², ³, ≈, ≤, ≥, →, ±), sem LaTeX cru.

---

## 6. Referência Cruzada com o Código

- Cada etapa da metodologia deve fazer referência ao script Python correspondente e ao README da etapa no `Codigo_v3`.
- Os resultados quantitativos citados devem ser consistentes com os outputs gerados (figuras e resumos em `Código/outputs/`).
