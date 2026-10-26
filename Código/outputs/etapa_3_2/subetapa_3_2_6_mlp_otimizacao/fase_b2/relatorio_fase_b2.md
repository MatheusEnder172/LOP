# Fase B2 — Busca ampliada de hiperparâmetros (Subetapa 3.2.6)

## Objetivo
A Fase B terminou com as melhores redes no limite do espaço de busca (4 camadas). A B2 verifica se redes
mais profundas e outras escolhas de projeto reduzem ainda mais o erro de X_Zn fora da dobra.

## O que mudou em relação à Fase B
- Profundidade de 2 a 8 camadas ocultas e largura de 8 a 96 (constante ou afunilada).
- Somente épocas fixas, de 200 a 4000 (a parada interna teve mediana 6 vezes pior na Fase B).
- Novas opções: conexões residuais; inicialização de Glorot (Glorot; Bengio, 2010) com o ganho de Tanh;
  entrada temporal em ln t (`KineticsMLPLogT`), que espalha melhor os primeiros minutos, onde ν é grande.
- Dropout de 0 a 0,3; o restante como na Fase B.
- As tentativas 211 (escolhida) e 354 da Fase B foram enfileiradas como tentativas 0 e 1 da B2; a
  tentativa 0 deu 0.0331, reproduzindo o valor da Fase B no mesmo protocolo.
- Tentativas: 523 (479 completas, 44 podadas); CPU somada 52.1 h.

## Melhores tentativas (3 sementes)
| Tentativa | RMSE X_Zn | Camadas | Ativação | ln t | Residual | Inicialização | LayerNorm | Dropout | lr | Lote | Épocas |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 449 | 0.0284 | [82, 41, 20] | GELU | sim | sim | padrao | não | 0.12 | 5.89e-03 | 16 | 840 |
| 499 | 0.0306 | [88, 44, 22] | GELU | sim | sim | padrao | não | 0.09 | 4.59e-03 | 16 | 670 |
| 511 | 0.0308 | [90, 45, 22] | GELU | sim | sim | padrao | não | 0.13 | 4.08e-03 | 16 | 928 |
| 478 | 0.0309 | [91, 45, 22] | GELU | sim | sim | padrao | não | 0.09 | 4.50e-03 | 16 | 703 |
| 461 | 0.0312 | [87, 43, 21] | GELU | sim | sim | padrao | não | 0.17 | 5.19e-03 | 16 | 941 |
| 328 | 0.0313 | [82, 41, 20] | GELU | sim | sim | padrao | não | 0.11 | 5.25e-03 | 16 | 1137 |
| 139 | 0.0314 | [85, 42, 21] | GELU | sim | sim | padrao | não | 0.16 | 6.20e-03 | 16 | 930 |
| 455 | 0.0315 | [88, 44, 22] | GELU | sim | sim | padrao | não | 0.09 | 4.28e-03 | 16 | 790 |
| 446 | 0.0315 | [95, 47, 23] | GELU | sim | sim | padrao | não | 0.17 | 5.44e-03 | 16 | 1024 |
| 508 | 0.0315 | [93, 46, 23] | GELU | sim | sim | padrao | não | 0.14 | 4.31e-03 | 16 | 1811 |

## Medianas por categoria (tentativas completas)
- Camadas: 2 → 0.0589 (n=23); 3 → 0.0368 (n=342); 4 → 0.0388 (n=78); 5 → 0.0542 (n=15); 6 → 0.0590 (n=5); 7 → 0.0764 (n=8); 8 → 0.0524 (n=8)
- Ativação: GELU → 0.0364 (n=141); SiLU → 0.0569 (n=18); Tanh → 0.0376 (n=320)
- Entrada ln t: False → 0.0467 (n=48); True → 0.0373 (n=431)
- Inicialização: padrao → 0.0374 (n=450); xavier → 0.0780 (n=29)
- Residual: False → 0.0377 (n=335); True → 0.0368 (n=144)
- LayerNorm: False → 0.0377 (n=170); True → 0.0376 (n=309)

## Importância dos hiperparâmetros (fANOVA)
| Hiperparâmetro | Importância |
| :--- | :---: |
| Taxa de aprendizado | 0.215 |
| Weight decay | 0.187 |
| LayerNorm | 0.084 |
| Conexões residuais | 0.083 |
| Forma (constante/afunilada) | 0.080 |
| Tamanho do lote | 0.077 |
| Função de ativação | 0.075 |
| Largura da 1ª camada | 0.066 |
| Nº de camadas ocultas | 0.060 |
| Épocas (fixas) | 0.037 |
| Dropout | 0.035 |
| Inicialização | 0.001 |
| Entrada temporal (t ou ln t) | 0.001 |

Observação: o fANOVA mede a variação do erro dentro da região explorada pelo TPE; categorias pouco amostradas tendem a aparecer com importância baixa mesmo quando a diferença entre elas é grande.

## Finalistas (10 sementes)
| Configuração | RMSE X_Zn (média ± dp) | R² X_Zn | Parâmetros | Dentro de 1 EP | Escolhida |
| :--- | :---: | :---: | :---: | :---: | :---: |
| B2 – tentativa 511 | 0.0326 ± 0.0050 | 0.9743 | 5490 | sim | **sim** |
| B2 – tentativa 478 | 0.0326 ± 0.0027 | 0.9747 | 5539 | sim |  |
| B2 – tentativa 499 | 0.0354 ± 0.0065 | 0.9696 | 5281 | não |  |
| B2 – tentativa 461 | 0.0359 ± 0.0059 | 0.9688 | 5078 | não |  |
| Fase B (Tentativa 211) | 0.0363 ± 0.0053 | 0.9682 | 1492 | não |  |
| B2 – tentativa 449 | 0.0744 ± 0.1300 | 0.5102 | 4592 | não |  |
| v1 (MLP-B, parada interna) | 0.1828 ± 0.0393 | 0.1781 | 2369 | não |  |

Configuração escolhida (B2 – tentativa 511):

```json
{
  "hidden_dims": [
    90,
    45,
    22
  ],
  "activation": "GELU",
  "use_layer_norm": false,
  "use_residual": true,
  "inicializacao": "padrao",
  "entrada_log_t": true,
  "dropout_rate": 0.12543102431411296,
  "lr": 0.004078055233808696,
  "weight_decay": 0.0010208014293023103,
  "batch_size": 16,
  "modo_parada": "epocas_fixas",
  "patience": 0,
  "max_epochs": 928,
  "mono_lambda": 0.0
}
```

### Comparação pareada com a Fase B (mesmas 10 sementes)
- Diferença média de RMSE (B2 − B): -0.0037; a B2 foi melhor em 7 de 10 sementes.
- Teste t pareado: p = 0.028; Wilcoxon pareado: p = 0.049.
- Ressalva: as sementes 42–44 também foram usadas na busca das duas fases, o que favorece igualmente B e B2.

## RMSE de X_Zn por ensaio (10 sementes)
| Ensaio | Teto | Fase B | Fase B2 |
| :---: | :---: | :---: | :---: |
| 01 | 0.0095 | 0.0214 ± 0.0131 | 0.0268 ± 0.0053 |
| 02 | 0.0047 | 0.0366 ± 0.0044 | 0.0228 ± 0.0151 |
| 03 | 0.0093 | 0.0163 ± 0.0053 | 0.0193 ± 0.0049 |
| 04 | 0.0216 | 0.0311 ± 0.0069 | 0.0215 ± 0.0008 |
| 05 | 0.0122 | 0.0392 ± 0.0099 | 0.0213 ± 0.0095 |
| 06 | 0.0148 | 0.0350 ± 0.0115 | 0.0437 ± 0.0123 |
| 09 | 0.0113 | 0.0447 ± 0.0104 | 0.0162 ± 0.0036 |
| 10 | 0.0167 | 0.0348 ± 0.0210 | 0.0542 ± 0.0194 |
| 11 | 0.0256 | 0.0570 ± 0.0086 | 0.0344 ± 0.0012 |
| 12 | 0.0071 | 0.0300 ± 0.0062 | 0.0131 ± 0.0035 |
| 13 | 0.0125 | 0.0320 ± 0.0155 | 0.0222 ± 0.0017 |
| 15 | 0.0090 | 0.0333 ± 0.0148 | 0.0580 ± 0.0132 |
| 16 | 0.0153 | 0.0274 ± 0.0015 | 0.0174 ± 0.0021 |

## Figuras
- `fig_fb2_01_historico_busca`: valor de cada tentativa e melhor valor acumulado.
- `fig_fb2_02_importancia_hiperparametros`: importância relativa (fANOVA).
- `fig_fb2_03_hiperparametros_categoricos`: RMSE por profundidade, ativação, entrada temporal, inicialização, residual e LayerNorm.
- `fig_fb2_04_fatias_hiperparametros`: RMSE contra os hiperparâmetros contínuos, por entrada temporal.
- `fig_fb2_05_finalistas_10_sementes`: Fase B e finalistas da B2 com 10 sementes.
- `fig_fb2_06_XZn_fora_da_dobra_fase_b_vs_b2`: X_Zn(t) fora da dobra.
- `fig_fb2_07_rmse_XZn_por_ensaio`: RMSE de X_Zn por ensaio.

## Base bibliográfica
- Busca de hiperparâmetros: Goodfellow, Bengio e Courville (2016, seção 11.4); Bergstra et al. (2011) [nova]; Akiba et al. (2019) [nova].
- Inicialização de Glorot: Glorot e Bengio (2010) [nova]. Conexões residuais: He et al. (2016) [nova].
- Seleção por validação cruzada e regra de um erro-padrão: Hastie, Tibshirani e Friedman (2009).
