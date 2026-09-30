# Etapa 1.3: Resolvedor PBM Batelada e Simulação Baseline FPM Puro

## Objetivo
Implementar o resolvedor numérico permanente do Balanço Populacional em Batelada (`src/physics/pbm_batch.py`) utilizando o Método das Características acoplado ao balanço estequiométrico de Herbst (1979). Executar a simulação de referência puramente fenomenológica (FPM Puro) com parâmetro de amortecimento nominal $\alpha = 5500\,\mu\text{m/min}$ para os 16 ensaios experimentais de bancada de Bortot Coelho (2017), estabelecendo o baseline de comparação para o futuro modelo híbrido.

---

## Estrutura da Etapa
- **Código-fonte de produção**: [`Código/src/physics/pbm_batch.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/pbm_batch.py)
  - Classe `BatchPBMSolver` com pré-computação monótona $\delta \mapsto X_{\text{Zn}}$ e integração por `scipy.integrate.solve_ivp`.
- **Exportação no Pacote**: [`Código/src/physics/__init__.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/src/physics/__init__.py)
- **Script de Testes Unitários**: [`test_pbm_batch.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/etapas/etapa_1_3_baseline_fpm/test_pbm_batch.py)
  - Validação de monotonicidade, limites físicos $[0, 1]$, limite assintótico analítico e método de perfil de velocidade.
- **Script de Simulação do Baseline**: [`simular_baseline_fpm.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/etapas/etapa_1_3_baseline_fpm/simular_baseline_fpm.py)
  - Simula os 16 ensaios, calcula métricas estatísticas individuais e globais ($R^2$, RMSE, MAE) e plota os gráficos comparativos.
- **Script do Comparativo FPM Nominal vs. Nova Abordagem (Global)**: [`gerar_comparativo_fabricio_vs_novo.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/etapas/etapa_1_3_baseline_fpm/gerar_comparativo_fabricio_vs_novo.py)
  - Realiza o benchmark quantitativo rigoroso entre o modelo nominal com $\alpha = 5500\,\mu\text{m/min}$ e a nova abordagem híbrida adaptativa (painel geral 2×2, barras e paridade).
- **Script do Comparativo Despoluído Ensaio a Ensaio (Individual)**: [`gerar_comparativo_ensaios_individuais.py`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/etapas/etapa_1_3_baseline_fpm/gerar_comparativo_ensaios_individuais.py)
  - Gera os 16 gráficos individuais em alta resolução com painel duplo de curvas cinéticas (Experimental vs. α = 0 vs. α = 5500 vs. LOP) e resíduos ponto a ponto para os 3 modelos teóricos com layout despoluído (legendas externas).

---

## Entregas Técnicas (Outputs)
Centralizadas em [`Código/outputs/etapa_1_3/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/):
1. **Gráficos e Relatórios do Baseline FPM (Modelo Nominal Puro)**:
   - [`fig_03_baseline_fpm_vs_experimento.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/fig_03_baseline_fpm_vs_experimento.png) / [PDF](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/fig_03_baseline_fpm_vs_experimento.pdf): Simulação mecanicista pura com $\alpha$ estático vs. dados experimentais.
   - [`tabela_metricas_baseline_fpm.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/tabela_metricas_baseline_fpm.csv): Métricas individuais do FPM nominal.
   - [`relatorio_validacao_etapa_1_3.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/relatorio_validacao_etapa_1_3.md): Relatório formal de validação da Etapa 1.3.
   - [`nota_conceitual_pbm_batelada.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/nota_conceitual_pbm_batelada.md): Nota teórica sobre o Método das Características.
   - [`fundamentacao_cinetica_pbm_dissertacao_coelho.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/fundamentacao_cinetica_pbm_dissertacao_coelho.md): Fundamentação das equações do PBM na dissertação de Fabrício Bortot Coelho (2017).

2. **Subpasta de Comparativo Global: [`Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/)**:
   - [`fig_comp_01_cinetica_16_ensaios.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_01_cinetica_16_ensaios.png) / [PDF](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_01_cinetica_16_ensaios.pdf): Painel 2×2 das 16 cinéticas.
   - [`fig_comp_02_metricas_e_erro_patamar.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_02_metricas_e_erro_patamar.png) / [PDF](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_02_metricas_e_erro_patamar.pdf): Comparação ensaio a ensaio de $R^2$ e desvio de patamar final.
   - [`fig_comp_03_paridade_e_residuos.png`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_03_paridade_e_residuos.png) / [PDF](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/fig_comp_03_paridade_e_residuos.pdf): Diagrama de paridade 1:1 e bandas de erro de $\pm 5\%$.
   - [`tabela_comparativa_detalhada_modelos.csv`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/tabela_comparativa_detalhada_modelos.csv): Tabela comparativa pareada ensaio a ensaio.
   - [`relatorio_comparativo_fabricio_vs_nova_abordagem.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/relatorio_comparativo_fabricio_vs_nova_abordagem.md): Relatório comparativo aprofundado com citações de páginas, seções e tabelas da dissertação.
   - [`logica_passo_a_passo_nova_abordagem_LOP.md`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/logica_passo_a_passo_nova_abordagem_LOP.md): Documento didático detalhado explicando toda a lógica matemática passo a passo da Nova Abordagem (LOP) com tabela comparativa entre os 3 modelos.

3. **Galeria de Gráficos Individuais Despoluídos: [`Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/ensaios_individuais/`](file:///c:/us%20trem/Doc/UFMG/9/Lop/Codigo_v3/Código/outputs/etapa_1_3/comparacao_fabricio_x_LOP/ensaios_individuais/)**:
   - 16 figuras individuais (PNG 300 DPI e PDF vetorial) para os Ensaios 01 a 16 (`fig_comp_ensaio_01_eta_0_5_ca0_0_10` a `fig_comp_ensaio_16_eta_3_1_ca0_1_50`), contendo 4 curvas de conversão (Experimental, Cinético Puro α = 0, Nominal de Fabrício α = 5500 e LOP), caixa lateral de parâmetros operacionais/métricas e painel inferior de resíduos temporais ponto a ponto para os 3 modelos.
