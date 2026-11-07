# Ferramentas do relatório (Documento/ferramentas)

Scripts que escrevem e reorganizam o relatório em .docx (equações nativas, tabelas ABNT, figuras, texto em vermelho fora de Métodos).

- `docx_utils.py`: `SectionWriter`, `latex_to_omml`, `pintar`, `add_references`.
- `escrever_hibrido_serial.py`: texto longo da seção do híbrido serial (25/10). Alimenta o Apêndice E (E.2 a E.4).
- `escrever_resultados_hibrido.py`: Resultados do híbrido serial (25/10, em vermelho, ainda longos).
- `reestruturar_problema_inverso_v6.py`: gerou a v6 a partir da v5.
- `reorganizar_apendices_hibrido_serial.py`: gera a v7 (Metodologia enxuta e Apêndices B a E) a partir de `RELATÓRIO PARCIAL-fab.docx`, sem alterá-lo.
- `analisar_contribuicao_penalidades.py`: contribuição de cada termo de penalização do problema inverso (saída em `Código/outputs/etapa_2_1/tabela_contribuicao_penalidades.csv`).

Os arquivos .docx não são versionados. Ver `PLANO_RETOMADA_PROXIMO_CHAT.md` na raiz do projeto.
