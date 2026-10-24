# Registro de Arquivos Depreciados — Etapa 4.2

## 1. Arquivos Depreciados
- `fig_12a_reconstrucao_XZn_hibrido_16_ensaios.png` e `.pdf`
- `fig_12a_reconstrucao_XZn_hibrido_16_ensaios_log.png` e `.pdf`
- `fig_12a_reconstrucao_XZn_hibrido_16_ensaios_semilog_XZn.png` e `.pdf`

## 2. Data e Motivo da Descontinuação
- **Data**: 01/10/2026
- **Motivo**: Inconsistência textual na legenda dos painéis 4x4, onde constava a string errônea `FPM Puro (\alpha = 3,43)`, quando a simulação mecanicista do FPM Puro sempre foi executada utilizando o parâmetro nominal consolidado da dissertação de Fabrício Bortot Coelho (2017, Tabela 5.9, p. 155): `\alpha = 5500 µm/min`.

## 3. Novos Arquivos Gerados em Substituição
- Versões atualizadas dos painéis 4x4 em `Código/outputs/etapa_4_2_avaliacao_indomain/` com a legenda correta `FPM Puro (\alpha = 5500 \mu\mathrm{m/min})`.
