# PLANO DE REDAÇÃO: Seção 4 – Materiais e Métodos
## Relatório LOP/TCC: Modelagem Híbrida com Machine Learning aplicada à Simulação da Lixiviação de Concentrado Ustulado de Zinco

**Autores**: Daniel Couto Vieira, Guilherme Moura de Sousa Franco, Matheus Henrique Borba Póvoas, Rodrigo Amaral da Mata  
**Orientador**: Prof. Dr. Fabrício Bortot Coelho  
**Instituição**: DEQ/UFMG – 2026

---

## Visão Geral

A Seção 4 (Materiais e Métodos) descreve, de forma completa e reprodutível, todos os procedimentos experimentais, computacionais e analíticos realizados para o desenvolvimento do modelo híbrido. Cada subseção será redigida de forma modular, revisada individualmente e, ao final, composta no documento principal.

---

## Mapa de Subseções e Status

| Subseção | Título | Etapa(s) do Código | Status |
|:---------|:-------|:-------------------|:-------|
| **4.1** | Procedimentos Experimentais e Base de Dados | Fase 1 (Mapeamento) | ✅ **Concluída & Inserida no Word** |
| **4.2** | Análise Exploratória dos Dados Cinéticos de Bancada | Etapa 0.1 | ✅ **Concluída & Inserida no Word** |
| **4.3** | Metodologia da Distribuição Granulométrica (RRB) | Etapa 0.2 / Módulo 1.1 | ✅ **Concluída & Inserida no Word** |
| **4.4** | Cinética de Retração Interfacial e Balanço Estequiométrico | Etapa 1.2 (`kinetics.py`) | ✅ **Concluída & Inserida no Word** |
| **4.5** | Resolvedor Numérico do Balanço Populacional e Baseline FPM | Etapa 1.3 (`pbm_batch.py`) | ✅ **Concluída & Inserida no Word** |
| **4.6** | Implementação Computacional, Arquitetura de Software e Governança | Toda a pipeline / Clean Code | ✅ **Concluída & Inserida no Word** |
| **4.7** | Metodologia de Otimização Inversa e Geração de Alvos v(t) | Etapa 2.1 (`otimizar_alvos_v.py`) | ✅ **Concluída & Inserida no Word** |
| **4.8** | Pré-Processamento, Engenharia de Atributos e Partição de Dados | Etapa 3.1 (`executar_particao.py`) | ✅ **Concluída & Inserida no Word** |
| **4.9** | Modelos Orientados por Dados (DDM) e Seleção Multicritério | Etapa 3.2 (MLP, RF, SVR, XGBoost, MCDA) | ✅ **Concluída & Inserida no Word** |
| **4.10** | Concepção e Acoplamento da Arquitetura Híbrida Serial (DDM → PBM) | Etapa 4.1 (`serial_hybrid.py`) | ✅ **Concluída & Inserida no Word** |
| **4.11** | Protocolo de Avaliação In-Domain, Benchmark Triplo e Métricas Estatísticas | Etapa 4.2 (`avaliar_hibrido_indomain.py`) | ✅ **Concluída & Inserida no Word** |

---

## Protocolo de Trabalho

1. **Redigir** cada subseção em arquivo `.md` individual na pasta `metodologia/`.
2. **Revisar** com o usuário antes de marcar como concluída.
3. **Atualizar** este plano (`PLANO_METODOLOGIA.md`) com o status a cada subseção finalizada.
4. **Compilar** todos os `.md` em ordem sequencial para composição no documento final.

---

## Fontes Primárias de Dados (Proveniência Acadêmica Real)

- **Dissertação-fonte principal**: Bortot Coelho (2017) – Apêndice A1.1 (Tabelas A1.1, A1.4 para dados cinéticos e balanços de bancada), Apêndice A1.2 (Tabelas A1.6, A1.7 para planta piloto contínua), Capítulo 4 (procedimentos e aparato), Capítulo 5 (Tabelas 5.4, 5.6 e 5.9 para granulometria e parâmetros nominais).
- **Tese de doutorado de referência**: Balarini (2009) – parâmetros cinéticos nominais ($k_s = 1,8 \times 10^4\ \mu\text{m/min}$, $n = 0,7$).
- **Artigos e métodos correlatos**: Elgersma et al. (1992) para lixiviação seletiva amoniacal de zincita; Herbst (1979) para relação de conservação de massa em batelada; Bortot Coelho et al. (2020) para operação contínua piloto.
- **Rastreabilidade e devlog**: Documentados em `RASTREABILIDADE_DADOS.md` e `DEVLOG.md` no repositório de código.


---

## Convenções de Nomenclatura

- Arquivos: `secao_4_X_titulo_resumido.md`
- Figuras referenciadas: manter numeração do relatório parcial (Figura XX).
- Variáveis: usar os mesmos símbolos da revisão bibliográfica (η, X_Zn, C_Af, C_A0, m_B0, D₆₃,₂, etc.).
