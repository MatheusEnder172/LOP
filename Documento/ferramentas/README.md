# Ferramentas do relatório (Documento/ferramentas)

Scripts que escrevem e reorganizam o relatório em .docx (equações nativas, tabelas ABNT, figuras, texto em vermelho fora de Métodos).

- `docx_utils.py`: `SectionWriter`, `latex_to_omml`, `pintar`, `add_references`.
- `escrever_hibrido_serial.py`: texto longo da seção do híbrido serial (25/10). Alimenta o Apêndice E (E.2 a E.4).
- `escrever_resultados_hibrido.py`: Resultados do híbrido serial (25/10, em vermelho, ainda longos).
- `reestruturar_problema_inverso_v6.py`: gerou a v6 a partir da v5.
- `reorganizar_apendices_hibrido_serial.py`: gera a v7 (Metodologia enxuta e Apêndices B a E) a partir de `RELATÓRIO PARCIAL-fab.docx`, sem alterá-lo.
- `adicionar_resultados_apendices_v8.py`: gera a v8 a partir da v7 (sem alterá-la): remove o parágrafo repetido da abertura do híbrido serial e acrescenta, em vermelho, os resultados das análises concluídas nos Apêndices B (B.5), D (D.3) e E (E.5 a E.7), lendo os números dos CSVs de `Código/outputs/`.
- `adicionar_testes_achados_v9.py`: gera a v9 a partir da v8 (sem alterá-la): um parágrafo em Métodos (cor normal) sobre a positividade da taxa e, em vermelho no Apêndice E, as seções E.8 (perdas físicas D1 e D2), E.9 (ajuste fino ponta a ponta), E.10 (síntese e decisão: v2 mantida) e E.11 (previsão a priori dos 4 ensaios novos), lendo os números dos CSVs de `Código/outputs/`.
- `adicionar_resultados_v10.py`: gera a v10 a partir da v9 (sem alterá-la): escreve, em vermelho, a subseção de Resultados do modelo híbrido serial (antes de CONCLUSÕES), com os números lidos dos CSVs. As figuras e tabelas de apoio vêm de `Código/etapas/etapa_4_4_resultados_hibrido_serial/analisar_resultados.py`.
- `analisar_contribuicao_penalidades.py`: contribuição de cada termo de penalização do problema inverso (saída em `Código/outputs/etapa_2_1/tabela_contribuicao_penalidades.csv`).

Os arquivos .docx não são versionados. Ver `PLANO_RETOMADA_PROXIMO_CHAT.md` na raiz do projeto.
