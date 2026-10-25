# Fase A — Linha de base honesta da MLP-B v1 (Subetapa 3.2.6)

## Objetivo
Medir o desempenho da configuração v1 ([64, 32], GELU, LayerNorm, AdamW 3e-3 / 1e-4, batch 32,
paciência 60, até 350 épocas) num protocolo de validação sem viés de seleção e com nota em X_Zn,
que é a variável efetivamente reportada pelo híbrido serial.

## Como foi feito
- **Protocolo antigo** (Subetapa 3.2.1): a dobra de validação decide a parada antecipada e dá a nota;
  semente 42; nota na taxa ν.
- **Protocolo novo** (`protocolo_cv.py`): em cada dobra, 2 ensaios do treino (sorteio fixo, sem os
  vértices 1, 2, 5 e 16) servem só para a parada antecipada; os ensaios de validação da dobra passam
  pelo PBM e dão a nota em X_Zn (7 pontos t > 0 por ensaio, 91 no total); sementes 42, 43 e 44.
- O teste cego (ensaios 7, 8 e 14) não foi usado.
- Tempo total: 33 s.

## Resultados
| Referência / protocolo | RMSE X_Zn (91 pts) | R² X_Zn | R² médio de ν nas dobras |
| :--- | :---: | :---: | :---: |
| Teto: X_Zn dos próprios alvos ν | 0.0142 | 0.9952 | – |
| v1 final, no próprio treino (não é validação) | 0.0229 | 0.9876 | – |
| v1, VC protocolo antigo | 0.1301 | 0.6001 | 0.8210 |
| v1, VC protocolo novo (média ± dp, 3 sementes) | 0.1772 ± 0.0464 | 0.2239 | 0.3695 |

Verificação de coerência: o R² médio de ν no protocolo antigo deve reproduzir o valor da Subetapa 3.2.1
(0,8210). Obtido: 0.8210.

### Por dobra (protocolo novo, média das 3 sementes)
| Dobra | Validação | Parada interna (semente 42) | RMSE X_Zn | R² ν | R²_log ν | Melhor época |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | [1, 5, 11, 16] | [3, 12] | 0.0861 | 0.7993 | 0.7064 | 89 |
| 2 | [4, 10, 15] | [11, 13] | 0.2930 | 0.5666 | 0.7268 | 127 |
| 3 | [3, 9, 13] | [6, 15] | 0.1400 | -0.2598 | 0.1197 | 36 |
| 4 | [2, 6, 12] | [10, 11] | 0.0747 | 0.3721 | 0.6576 | 69 |

### Por ensaio (RMSE de X_Zn quando o ensaio está na validação)
| Ensaio | Teto | Protocolo antigo | Protocolo novo (média ± dp) |
| :---: | :---: | :---: | :---: |
| 01 | 0.0095 | 0.0323 | 0.0419 ± 0.0186 |
| 02 | 0.0047 | 0.0867 | 0.0951 ± 0.0339 |
| 03 | 0.0093 | 0.2989 | 0.2071 ± 0.0547 |
| 04 | 0.0216 | 0.0698 | 0.2363 ± 0.1376 |
| 05 | 0.0122 | 0.2405 | 0.1415 ± 0.0739 |
| 06 | 0.0148 | 0.1746 | 0.0749 ± 0.0536 |
| 09 | 0.0113 | 0.0818 | 0.1041 ± 0.0444 |
| 10 | 0.0167 | 0.0609 | 0.4146 ± 0.2477 |
| 11 | 0.0256 | 0.1204 | 0.0773 ± 0.0207 |
| 12 | 0.0071 | 0.0209 | 0.0282 ± 0.0309 |
| 13 | 0.0125 | 0.0347 | 0.0514 ± 0.0181 |
| 15 | 0.0090 | 0.0145 | 0.1482 ± 0.1347 |
| 16 | 0.0153 | 0.0471 | 0.0351 ± 0.0081 |

## Figuras
- `fig_fa_01_protocolo_antigo_vs_novo`: (a) R² de ν por dobra nos dois protocolos; (b) RMSE de X_Zn das referências e dos dois protocolos.
- `fig_fa_02_XZn_fora_da_dobra_13_ensaios`: X_Zn(t) de cada ensaio previsto pelo modelo da dobra em que ele ficou de fora.
- `fig_fa_03_rmse_XZn_por_ensaio`: RMSE de X_Zn por ensaio.

## Base bibliográfica
- Validação cruzada por grupos (ensaios): Roberts et al. (2017); Hastie, Tibshirani e Friedman (2009).
- Viés de selecionar e avaliar no mesmo conjunto: Cawley e Talbot (2010) [referência nova]; vazamento: Kapoor e Narayanan (2023).
- Parada antecipada como regularização: Goodfellow, Bengio e Courville (2016, seção 7.8).
